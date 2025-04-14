import logging
import telebot
from telebot import types
import re
import os
from flask import request
from config import TOKEN, ACCESS_CODES, TARIFF_DESCRIPTIONS, MODULE_ACCESS, ADMIN_IDS
from database import (
    get_user, add_user, update_user_tariff, add_feedback, 
    update_module_progress, get_module_progress, add_homework_submission,
    get_homework_submissions
)
from modules_content import MODULES, MODULE_DESCRIPTIONS, HOMEWORK, ADDITIONAL_MATERIALS
from keyboards import (
    get_main_menu_keyboard, get_back_keyboard, get_modules_keyboard, 
    get_homework_keyboard, get_module_content_keyboard, get_access_keyboard,
    get_submit_homework_keyboard, get_additional_materials_keyboard,
    get_feedback_confirm_keyboard
)

logger = logging.getLogger(__name__)

class BotStates:
    AWAITING_ACCESS_CODE = 'awaiting_access_code'
    AWAITING_FEEDBACK = 'awaiting_feedback'
    AWAITING_HOMEWORK_SUBMISSION = 'awaiting_homework_submission'
    CURRENT_MODULE = 'current_module'  # Stores the current module ID for context


def register_command_handlers(bot, user_states, temp_data):
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        user = get_user(user_id)
        
        # Welcome message
        welcome_text = (
            "👋 *Добро пожаловать в бот курса трансформации!*\n\n"
            "Здесь вы найдете материалы курса, домашние задания "
            "и сможете отслеживать свой прогресс."
        )
        
        # Check if user exists in database
        if user:
            tariff = user[4]  # Index 4 corresponds to tariff in the database row
            bot.send_message(
                user_id, 
                f"{welcome_text}\n\nВаш текущий тариф: *{tariff}*",
                parse_mode="Markdown"
            )
            show_main_menu(message, bot)
        else:
            bot.send_message(
                user_id, 
                f"{welcome_text}\n\nУ вас нет доступа к курсу. "
                "Пожалуйста, введите код доступа с помощью команды /access.",
                parse_mode="Markdown"
            )
    
    @bot.message_handler(commands=['help'])
    def help_command(message):
        help_text = (
            "*Доступные команды:*\n\n"
            "/start - Начать работу с ботом\n"
            "/menu - Показать главное меню\n"
            "/access - Ввести код доступа\n"
            "/modules - Показать доступные модули\n"
            "/homework - Показать домашние задания\n"
            "/progress - Показать ваш прогресс\n"
            "/webapp - Открыть интерактивное мини-приложение\n"
            "/feedback - Отправить обратную связь\n"
            "/info - Информация о курсе\n"
            "/help - Показать это сообщение"
        )
        bot.send_message(message.chat.id, help_text, parse_mode="Markdown")
    
    @bot.message_handler(commands=['menu'])
    def menu_command(message):
        show_main_menu(message, bot)
    
    @bot.message_handler(commands=['access'])
    def access_command(message):
        user_id = message.from_user.id
        
        bot.send_message(
            user_id,
            "Пожалуйста, введите код доступа для получения доступа к курсу:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Set user state to awaiting access code
        user_states[user_id] = BotStates.AWAITING_ACCESS_CODE
    
    @bot.message_handler(commands=['modules'])
    def modules_command(message):
        user_id = message.from_user.id
        user = get_user(user_id)
        
        if not user:
            bot.send_message(
                user_id,
                "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access."
            )
            return
        
        tariff = user[4]
        available_modules = MODULE_ACCESS.get(tariff.lower(), [])
        
        bot.send_message(
            user_id,
            "*Доступные модули курса:*",
            parse_mode="Markdown",
            reply_markup=get_modules_keyboard(tariff, available_modules)
        )
    
    @bot.message_handler(commands=['homework'])
    def homework_command(message):
        user_id = message.from_user.id
        user = get_user(user_id)
        
        if not user:
            bot.send_message(
                user_id,
                "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access."
            )
            return
        
        tariff = user[4]
        available_modules = MODULE_ACCESS.get(tariff.lower(), [])
        
        bot.send_message(
            user_id,
            "*Домашние задания:*",
            parse_mode="Markdown",
            reply_markup=get_homework_keyboard(tariff, available_modules)
        )
    
    @bot.message_handler(commands=['progress'])
    def progress_command(message):
        user_id = message.from_user.id
        user = get_user(user_id)
        
        if not user:
            bot.send_message(
                user_id,
                "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access."
            )
            return
        
        tariff = user[4]
        available_modules = MODULE_ACCESS.get(tariff.lower(), [])
        progress = get_module_progress(user_id)
        
        # Convert progress data to a more usable format
        completed_modules = [module_id for module_id, completed in progress if completed]
        
        # Create progress message
        progress_text = "*Ваш прогресс по курсу:*\n\n"
        
        for module_id in available_modules:
            module_name = MODULES.get(module_id, f"Модуль {module_id}")
            status = "✅" if module_id in completed_modules else "⏳"
            progress_text += f"{status} Модуль {module_id}: {module_name}\n"
        
        # Calculate overall progress
        completed_percentage = 0
        if available_modules:
            completed_percentage = (len(completed_modules) / len(available_modules)) * 100
        
        progress_text += f"\n*Общий прогресс: {completed_percentage:.1f}%*"
        
        bot.send_message(
            user_id,
            progress_text,
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard()
        )
    
    @bot.message_handler(commands=['feedback'])
    def feedback_command(message):
        user_id = message.from_user.id
        user = get_user(user_id)
        
        if not user:
            bot.send_message(
                user_id,
                "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access."
            )
            return
        
        bot.send_message(
            user_id,
            "Пожалуйста, напишите вашу обратную связь или вопрос. Мы ответим вам в ближайшее время:",
            reply_markup=get_back_keyboard()
        )
        
        # Set user state to awaiting feedback
        user_states[user_id] = BotStates.AWAITING_FEEDBACK
    
    @bot.message_handler(commands=['info'])
    def info_command(message):
        user_id = message.from_user.id
        
        info_text = (
            "*О курсе трансформации*\n\n"
            "Этот курс создан для глубокой личностной трансформации и раскрытия вашего потенциала. "
            "Он состоит из 8 модулей, каждый из которых раскрывает определенный аспект вашей личности "
            "и помогает в процессе изменений.\n\n"
            
            "*Структура курса:*\n"
            "• 8 модулей с теоретическими материалами\n"
            "• Практические задания для самостоятельной работы\n"
            "• Домашние задания для закрепления результатов\n"
            "• Дополнительные материалы для углубления знаний\n\n"
            
            "*Доступные тарифы:*\n"
            "• Базовый: доступ к модулям 1-3\n"
            "• Стандартный: доступ к модулям 1-5\n"
            "• Премиум: доступ ко всем модулям\n"
            "• Переход: полный доступ со всеми материалами и персональной поддержкой\n\n"
            
            "Для получения дополнительной информации свяжитесь с нами через раздел 'Обратная связь'."
        )
        
        bot.send_message(
            user_id,
            info_text,
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard()
        )
        
    @bot.message_handler(commands=['webapp'])
    def webapp_command(message):
        user_id = message.from_user.id
        user = get_user(user_id)
        
        if not user:
            bot.send_message(
                user_id,
                "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access."
            )
            return
        
        # URL мини-приложения
        host = os.environ.get('REPLIT_APP_HOST', 'replit.dev')
        mini_app_url = f"https://{host}/mini-app?user_id={user_id}"
        
        # Создаем кнопку для запуска мини-приложения
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "📊 Открыть интерактивный прогресс", 
            web_app=types.WebAppInfo(url=mini_app_url)
        ))
        
        bot.send_message(
            user_id,
            "Нажмите на кнопку ниже, чтобы открыть интерактивное мини-приложение с вашим прогрессом по курсу:",
            reply_markup=markup
        )

    # Homework submission commands
    for module_id in range(1, len(MODULES) + 1):
        # Use a closure to capture the current module_id
        def create_homework_handler(module_id):
            command = f"/homework{module_id}"
            @bot.message_handler(commands=[f"homework{module_id}"])
            def homework_submission_handler(message):
                user_id = message.from_user.id
                user = get_user(user_id)
                
                if not user:
                    bot.send_message(
                        user_id,
                        "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access."
                    )
                    return
                
                tariff = user[4]
                available_modules = MODULE_ACCESS.get(tariff.lower(), [])
                
                if module_id not in available_modules:
                    bot.send_message(
                        user_id,
                        f"У вас нет доступа к модулю {module_id}. Обновите ваш тариф для доступа.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return
                
                bot.send_message(
                    user_id,
                    f"Пожалуйста, отправьте ваше решение домашнего задания для модуля {module_id}.\n\n"
                    f"Вы можете отправить текст, фото или документ. После отправки, "
                    f"ваша работа будет сохранена и передана куратору для проверки.",
                    reply_markup=get_back_keyboard()
                )
                
                # Set state and store module_id
                user_states[user_id] = BotStates.AWAITING_HOMEWORK_SUBMISSION
                temp_data[user_id] = {"module_id": module_id}
        
        # Register the handler
        create_homework_handler(module_id)


def register_message_handlers(bot, user_states, temp_data):
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == BotStates.AWAITING_ACCESS_CODE)
    def handle_access_code(message):
        user_id = message.from_user.id
        access_code = message.text.strip()
        
        # Clear user state
        user_states.pop(user_id, None)
        
        # Check if access code is valid
        valid_tariff = None
        for tariff, codes in ACCESS_CODES.items():
            if access_code in codes:
                valid_tariff = tariff
                break
        
        if valid_tariff:
            user = get_user(user_id)
            if user:
                # Update existing user's tariff
                success = update_user_tariff(user_id, valid_tariff)
                if success:
                    bot.send_message(
                        user_id,
                        f"✅ Ваш тариф успешно обновлен до *{valid_tariff}*!",
                        parse_mode="Markdown",
                        reply_markup=get_main_menu_keyboard()
                    )
                else:
                    bot.send_message(
                        user_id,
                        "❌ Произошла ошибка при обновлении тарифа. Пожалуйста, попробуйте позже.",
                        reply_markup=get_main_menu_keyboard()
                    )
            else:
                # Add new user
                username = message.from_user.username if message.from_user.username else ""
                first_name = message.from_user.first_name if message.from_user.first_name else ""
                last_name = message.from_user.last_name if message.from_user.last_name else ""
                
                success = add_user(user_id, username, first_name, last_name, valid_tariff)
                if success:
                    bot.send_message(
                        user_id,
                        f"✅ Добро пожаловать в курс! Ваш тариф: *{valid_tariff}*\n\n"
                        f"{TARIFF_DESCRIPTIONS.get(valid_tariff, '')}",
                        parse_mode="Markdown",
                        reply_markup=get_main_menu_keyboard()
                    )
                else:
                    bot.send_message(
                        user_id,
                        "❌ Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.",
                        reply_markup=types.ReplyKeyboardRemove()
                    )
        else:
            bot.send_message(
                user_id,
                "❌ Неверный код доступа. Пожалуйста, проверьте код и попробуйте снова или "
                "свяжитесь с администратором курса.",
                reply_markup=types.ReplyKeyboardRemove()
            )
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == BotStates.AWAITING_FEEDBACK)
    def handle_feedback(message):
        user_id = message.from_user.id
        feedback_text = message.text.strip()
        
        # Store feedback in temp_data
        temp_data[user_id] = {"feedback": feedback_text}
        
        # Ask for confirmation
        bot.send_message(
            user_id,
            f"*Ваша обратная связь:*\n\n{feedback_text}\n\nОтправить?",
            parse_mode="Markdown",
            reply_markup=get_feedback_confirm_keyboard()
        )
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == BotStates.AWAITING_HOMEWORK_SUBMISSION)
    def handle_homework_submission(message):
        user_id = message.from_user.id
        module_id = temp_data.get(user_id, {}).get("module_id")
        
        if not module_id:
            bot.send_message(
                user_id,
                "❌ Произошла ошибка. Пожалуйста, попробуйте снова.",
                reply_markup=get_main_menu_keyboard()
            )
            user_states.pop(user_id, None)
            temp_data.pop(user_id, None)
            return
        
        # Store submission in temp_data
        temp_data[user_id]["submission"] = message.text.strip()
        
        # Ask for confirmation
        bot.send_message(
            user_id,
            f"*Ваше решение домашнего задания для модуля {module_id}:*\n\n"
            f"{temp_data[user_id]['submission']}\n\nОтправить?",
            parse_mode="Markdown",
            reply_markup=get_submit_homework_keyboard(module_id)
        )
    
    @bot.message_handler(func=lambda message: message.text == '↩️ Вернуться в главное меню')
    def back_to_main_menu(message):
        user_id = message.from_user.id
        
        # Clear any active states
        user_states.pop(user_id, None)
        temp_data.pop(user_id, None)
        
        show_main_menu(message, bot)
    
    @bot.message_handler(func=lambda message: True)
    def handle_text_messages(message):
        user_id = message.from_user.id
        text = message.text
        nonlocal bot, user_states
        
        # Handle main menu options
        if text == '📚 Модули курса':
            user = get_user(user_id)
            if not user:
                bot.send_message(
                    user_id,
                    "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access."
                )
                return
            
            tariff = user[4]
            available_modules = MODULE_ACCESS.get(tariff.lower(), [])
            
            bot.send_message(
                user_id,
                "*Доступные модули курса:*",
                parse_mode="Markdown",
                reply_markup=get_modules_keyboard(tariff, available_modules)
            )
        
        elif text == '📝 Домашние задания':
            user = get_user(user_id)
            if not user:
                bot.send_message(
                    user_id,
                    "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access."
                )
                return
            
            tariff = user[4]
            available_modules = MODULE_ACCESS.get(tariff.lower(), [])
            
            bot.send_message(
                user_id,
                "*Домашние задания:*",
                parse_mode="Markdown",
                reply_markup=get_homework_keyboard(tariff, available_modules)
            )
        
        elif text == '🔍 Мой прогресс':
            progress_command(message, bot)
        
        elif text == '📊 Мини-приложение':
            # URL мини-приложения
            # Получаем хост из переменной окружения или ставим по умолчанию
            host = os.environ.get('REPLIT_APP_HOST', 'replit.dev')
            mini_app_url = f"https://{host}/mini-app?user_id={user_id}"
            
            # Создаем кнопку для запуска мини-приложения
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                "📊 Открыть интерактивный прогресс", 
                web_app=types.WebAppInfo(url=mini_app_url)
            ))
            
            bot.send_message(
                user_id,
                "Нажмите на кнопку ниже, чтобы открыть интерактивное мини-приложение с вашим прогрессом по курсу:",
                reply_markup=markup
            )
        
        elif text == '💬 Обратная связь':
            feedback_command(message, bot, user_states)
        
        elif text == 'ℹ️ Информация':
            info_command(message, bot)
        
        elif text == '📋 Мой тариф':
            user = get_user(user_id)
            if not user:
                bot.send_message(
                    user_id,
                    "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access."
                )
                return
            
            tariff = user[4]
            tariff_description = TARIFF_DESCRIPTIONS.get(tariff.lower(), "")
            available_modules = MODULE_ACCESS.get(tariff.lower(), [])
            
            tariff_text = (
                f"*Ваш текущий тариф: {tariff}*\n\n"
                f"{tariff_description}\n\n"
                f"*Доступные модули:* {', '.join(map(str, available_modules))}\n\n"
                f"Для повышения тарифа воспользуйтесь командой /access и введите новый код доступа."
            )
            
            bot.send_message(
                user_id,
                tariff_text,
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )
        
        else:
            bot.send_message(
                user_id,
                "Я не понимаю эту команду. Пожалуйста, используйте меню для навигации.",
                reply_markup=get_main_menu_keyboard()
            )


def register_callback_handlers(bot, user_states, temp_data):
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        user_id = call.from_user.id
        callback_data = call.data
        
        # Handle module selection
        if callback_data.startswith('module_'):
            module_id = int(callback_data.split('_')[1])
            handle_module_selection(call, module_id)
        
        # Handle locked module
        elif callback_data.startswith('locked_module_'):
            module_id = int(callback_data.split('_')[2])
            bot.answer_callback_query(
                call.id,
                text=f"Модуль {module_id} недоступен на вашем тарифе. Обновите тариф для доступа.",
                show_alert=True
            )
        
        # Handle homework selection
        elif callback_data.startswith('homework_'):
            module_id = int(callback_data.split('_')[1])
            handle_homework_selection(call, module_id)
        
        # Handle locked homework
        elif callback_data.startswith('locked_homework_'):
            module_id = int(callback_data.split('_')[2])
            bot.answer_callback_query(
                call.id,
                text=f"Домашнее задание {module_id} недоступно на вашем тарифе. Обновите тариф для доступа.",
                show_alert=True
            )
        
        # Handle navigation
        elif callback_data == 'back_to_main':
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
            show_main_menu(call.message, bot)
        
        elif callback_data == 'back_to_modules':
            user = get_user(user_id)
            if user:
                tariff = user[4]
                available_modules = MODULE_ACCESS.get(tariff.lower(), [])
                
                try:
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="*Доступные модули курса:*",
                        parse_mode="Markdown",
                        reply_markup=get_modules_keyboard(tariff, available_modules)
                    )
                except Exception as e:
                    # Если сообщение не изменилось или другая ошибка
                    logging.warning(f"Ошибка при редактировании сообщения: {str(e)}")
        
        # Handle module materials
        elif callback_data.startswith('materials_'):
            module_id = int(callback_data.split('_')[1])
            # Show additional materials for the module
            materials = ADDITIONAL_MATERIALS.get(module_id, [])
            materials_text = f"*Дополнительные материалы для модуля {module_id}:*\n\n"
            
            for i, material in enumerate(materials, 1):
                materials_text += f"{i}. {material}\n"
            
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=materials_text,
                    parse_mode="Markdown",
                    reply_markup=get_additional_materials_keyboard(module_id)
                )
            except Exception as e:
                logging.warning(f"Ошибка при редактировании сообщения материалов: {str(e)}")
        
        # Handle module completion
        elif callback_data.startswith('complete_module_'):
            module_id = int(callback_data.split('_')[2])
            success = update_module_progress(user_id, module_id, True)
            
            if success:
                bot.answer_callback_query(
                    call.id,
                    text=f"Модуль {module_id} отмечен как пройденный! 🎉",
                    show_alert=False
                )
            else:
                bot.answer_callback_query(
                    call.id,
                    text="Произошла ошибка. Пожалуйста, попробуйте позже.",
                    show_alert=True
                )
        
        # Handle homework submission
        elif callback_data.startswith('submit_homework_'):
            module_id = int(callback_data.split('_')[2])
            submission = temp_data.get(user_id, {}).get("submission", "")
            
            if submission:
                success = add_homework_submission(user_id, module_id, submission)
                
                if success:
                    # Clear states
                    user_states.pop(user_id, None)
                    temp_data.pop(user_id, None)
                    
                    try:
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text="✅ Ваше домашнее задание успешно отправлено! Куратор скоро его проверит.",
                            reply_markup=None
                        )
                    except Exception as e:
                        logging.warning(f"Ошибка при отправке успешного задания: {str(e)}")
                    
                    show_main_menu(call.message, bot)
                else:
                    try:
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text="❌ Произошла ошибка при отправке домашнего задания. Пожалуйста, попробуйте позже.",
                            reply_markup=None
                        )
                    except Exception as e:
                        logging.warning(f"Ошибка при отображении сообщения об ошибке: {str(e)}")
                    
                    show_main_menu(call.message, bot)
            else:
                bot.answer_callback_query(
                    call.id,
                    text="Домашнее задание не может быть пустым.",
                    show_alert=True
                )
        
        # Handle homework cancellation
        elif callback_data.startswith('cancel_homework_'):
            # Clear states
            user_states.pop(user_id, None)
            temp_data.pop(user_id, None)
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Отправка домашнего задания отменена.",
                reply_markup=None
            )
            
            show_main_menu(call.message, bot)
        
        # Handle feedback submission
        elif callback_data == 'submit_feedback':
            feedback_text = temp_data.get(user_id, {}).get("feedback", "")
            
            if feedback_text:
                success = add_feedback(user_id, feedback_text)
                
                if success:
                    # Clear states
                    user_states.pop(user_id, None)
                    temp_data.pop(user_id, None)
                    
                    try:
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text="✅ Ваша обратная связь успешно отправлена! Спасибо за ваш отзыв.",
                            reply_markup=None
                        )
                    except Exception as e:
                        logging.warning(f"Ошибка при отправке сообщения об успешном отзыве: {str(e)}")
                    
                    # Notify admins about new feedback
                    for admin_id in ADMIN_IDS:
                        try:
                            bot.send_message(
                                admin_id,
                                f"*Новая обратная связь от пользователя {user_id}:*\n\n{feedback_text}",
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logger.error(f"Failed to notify admin {admin_id}: {e}")
                    
                    show_main_menu(call.message, bot)
                else:
                    try:
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text="❌ Произошла ошибка при отправке обратной связи. Пожалуйста, попробуйте позже.",
                            reply_markup=None
                        )
                    except Exception as e:
                        logging.warning(f"Ошибка при отправке сообщения об ошибке отзыва: {str(e)}")
                    
                    show_main_menu(call.message, bot)
            else:
                bot.answer_callback_query(
                    call.id,
                    text="Обратная связь не может быть пустой.",
                    show_alert=True
                )
        
        # Handle feedback cancellation
        elif callback_data == 'cancel_feedback':
            # Clear states
            user_states.pop(user_id, None)
            temp_data.pop(user_id, None)
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Отправка обратной связи отменена.",
                reply_markup=None
            )
            
            show_main_menu(call.message, bot)
        
        # Handle access code entry
        elif callback_data == 'enter_access_code':
            bot.send_message(
                user_id,
                "Пожалуйста, введите код доступа:",
                reply_markup=types.ReplyKeyboardRemove()
            )
            
            # Set user state to awaiting access code
            user_states[user_id] = BotStates.AWAITING_ACCESS_CODE
    
    def handle_module_selection(call, module_id):
        user_id = call.from_user.id
        user = get_user(user_id)
        
        if not user:
            bot.answer_callback_query(
                call.id,
                text="У вас нет доступа к курсу. Пожалуйста, введите код доступа.",
                show_alert=True
            )
            return
        
        tariff = user[4]
        available_modules = MODULE_ACCESS.get(tariff.lower(), [])
        
        if module_id not in available_modules:
            bot.answer_callback_query(
                call.id,
                text=f"Модуль {module_id} недоступен на вашем тарифе. Обновите тариф для доступа.",
                show_alert=True
            )
            return
        
        # Get module content
        module_title = MODULES.get(module_id, f"Модуль {module_id}")
        module_description = MODULE_DESCRIPTIONS.get(module_id, "Описание отсутствует")
        
        module_text = f"*{module_title}*\n\n{module_description}"
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=module_text,
                parse_mode="Markdown",
                reply_markup=get_module_content_keyboard(module_id)
            )
        except Exception as e:
            logging.warning(f"Ошибка при отображении модуля: {str(e)}")
    
    def handle_homework_selection(call, module_id):
        user_id = call.from_user.id
        user = get_user(user_id)
        
        if not user:
            bot.answer_callback_query(
                call.id,
                text="У вас нет доступа к курсу. Пожалуйста, введите код доступа.",
                show_alert=True
            )
            return
        
        tariff = user[4]
        available_modules = MODULE_ACCESS.get(tariff.lower(), [])
        
        if module_id not in available_modules:
            bot.answer_callback_query(
                call.id,
                text=f"Домашнее задание {module_id} недоступно на вашем тарифе. Обновите тариф для доступа.",
                show_alert=True
            )
            return
        
        # Get homework content
        homework_text = HOMEWORK.get(module_id, "Домашнее задание отсутствует")
        
        # Get user submissions for this module
        submissions = get_homework_submissions(user_id, module_id)
        
        submission_text = ""
        if submissions:
            submission_text = "\n\n*Ваши отправленные решения:*\n"
            for idx, submission in enumerate(submissions[:3], 1):  # Show only the latest 3 submissions
                submission_date = submission[4][:16] if submission[4] else "Неизвестно"
                submission_text += f"{idx}. Отправлено: {submission_date}\n"
            
            if len(submissions) > 3:
                submission_text += f"(и еще {len(submissions) - 3} отправленных решений)"
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"{homework_text}{submission_text}",
                parse_mode="Markdown",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("↩️ Назад к модулям", callback_data="back_to_modules")
                )
            )
        except Exception as e:
            logging.warning(f"Ошибка при отображении домашнего задания: {str(e)}")


def register_admin_handlers(bot, user_states, temp_data):
    @bot.message_handler(commands=['admin'], func=lambda message: message.from_user.id in ADMIN_IDS)
    def admin_command(message):
        admin_text = (
            "*Админ-панель*\n\n"
            "Доступные команды:\n"
            "/users - показать список пользователей\n"
            "/feedback - показать отзывы\n"
            "/broadcast - отправить сообщение всем пользователям\n"
            "/adduser - добавить пользователя\n"
            "/updatetariff - обновить тариф пользователя"
        )
        
        bot.send_message(
            message.from_user.id,
            admin_text,
            parse_mode="Markdown"
        )
    
    # Other admin handlers can be added here


def register_state_handlers(bot, user_states, temp_data):
    # This function is for any additional state-based handlers
    # Currently, the state handlers are included in register_message_handlers
    pass


# Helper function to show main menu
def show_main_menu(message, bot_instance):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if user:
        bot_instance.send_message(
            user_id,
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        bot_instance.send_message(
            user_id,
            "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access.",
            reply_markup=get_access_keyboard()
        )


# Helper functions for command handlers (to avoid circular imports)
def progress_command(message, bot_instance):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user:
        bot_instance.send_message(
            user_id,
            "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access."
        )
        return
    
    tariff = user[4]
    available_modules = MODULE_ACCESS.get(tariff.lower(), [])
    progress = get_module_progress(user_id)
    
    # Convert progress data to a more usable format
    completed_modules = [module_id for module_id, completed in progress if completed]
    
    # Create progress message
    progress_text = "*Ваш прогресс по курсу:*\n\n"
    
    for module_id in available_modules:
        module_name = MODULES.get(module_id, f"Модуль {module_id}")
        status = "✅" if module_id in completed_modules else "⏳"
        progress_text += f"{status} Модуль {module_id}: {module_name}\n"
    
    # Calculate overall progress
    completed_percentage = 0
    if available_modules:
        completed_percentage = (len(completed_modules) / len(available_modules)) * 100
    
    progress_text += f"\n*Общий прогресс: {completed_percentage:.1f}%*"
    
    bot_instance.send_message(
        user_id,
        progress_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )


def feedback_command(message, bot_instance, user_states):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user:
        bot_instance.send_message(
            user_id,
            "У вас нет доступа к курсу. Пожалуйста, введите код доступа с помощью команды /access."
        )
        return
    
    bot_instance.send_message(
        user_id,
        "Пожалуйста, напишите вашу обратную связь или вопрос. Мы ответим вам в ближайшее время:",
        reply_markup=get_back_keyboard()
    )
    
    # Set user state to awaiting feedback
    user_states[user_id] = BotStates.AWAITING_FEEDBACK


def info_command(message, bot_instance):
    user_id = message.from_user.id
    
    info_text = (
        "*О курсе трансформации*\n\n"
        "Этот курс создан для глубокой личностной трансформации и раскрытия вашего потенциала. "
        "Он состоит из 8 модулей, каждый из которых раскрывает определенный аспект вашей личности "
        "и помогает в процессе изменений.\n\n"
        
        "*Структура курса:*\n"
        "• 8 модулей с теоретическими материалами\n"
        "• Практические задания для самостоятельной работы\n"
        "• Домашние задания для закрепления результатов\n"
        "• Дополнительные материалы для углубления знаний\n\n"
        
        "*Доступные тарифы:*\n"
        "• Базовый: доступ к модулям 1-3\n"
        "• Стандартный: доступ к модулям 1-5\n"
        "• Премиум: доступ ко всем модулям\n"
        "• Переход: полный доступ со всеми материалами и персональной поддержкой\n\n"
        
        "Для получения дополнительной информации свяжитесь с нами через раздел 'Обратная связь'."
    )
    
    bot_instance.send_message(
        user_id,
        info_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )
