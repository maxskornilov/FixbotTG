from telebot import types
from modules_content import MODULES

# Main menu keyboard
def get_main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton('📚 Модули курса'),
        types.KeyboardButton('📝 Домашние задания'),
        types.KeyboardButton('🔍 Мой прогресс'),
        types.KeyboardButton('📊 Мини-приложение'),
        types.KeyboardButton('💬 Обратная связь'),
        types.KeyboardButton('ℹ️ Информация'),
        types.KeyboardButton('📋 Мой тариф')
    ]
    markup.add(*buttons)
    return markup

# Back to main menu button
def get_back_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('↩️ Вернуться в главное меню'))
    return markup

# Modules selection keyboard
def get_modules_keyboard(user_tariff=None, available_modules=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if not available_modules:
        available_modules = list(MODULES.keys())
    
    buttons = []
    for module_id, module_name in MODULES.items():
        if module_id in available_modules:
            button_text = f"Модуль {module_id}: {module_name}"
            buttons.append(types.InlineKeyboardButton(
                button_text, callback_data=f"module_{module_id}"
            ))
        else:
            button_text = f"🔒 Модуль {module_id}: {module_name}"
            buttons.append(types.InlineKeyboardButton(
                button_text, callback_data=f"locked_module_{module_id}"
            ))
    
    # Add buttons to markup
    for button in buttons:
        markup.add(button)
    
    # Add back button
    markup.add(types.InlineKeyboardButton("↩️ Назад", callback_data="back_to_main"))
    
    return markup

# Homework selection keyboard
def get_homework_keyboard(user_tariff=None, available_modules=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if not available_modules:
        available_modules = list(MODULES.keys())
    
    buttons = []
    for module_id, module_name in MODULES.items():
        if module_id in available_modules:
            button_text = f"Задание {module_id}: {module_name}"
            buttons.append(types.InlineKeyboardButton(
                button_text, callback_data=f"homework_{module_id}"
            ))
        else:
            button_text = f"🔒 Задание {module_id}: {module_name}"
            buttons.append(types.InlineKeyboardButton(
                button_text, callback_data=f"locked_homework_{module_id}"
            ))
    
    # Add buttons to markup
    for button in buttons:
        markup.add(button)
    
    # Add back button
    markup.add(types.InlineKeyboardButton("↩️ Назад", callback_data="back_to_main"))
    
    return markup

# Module content keyboard
def get_module_content_keyboard(module_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        types.InlineKeyboardButton("📚 Материалы", callback_data=f"materials_{module_id}"),
        types.InlineKeyboardButton("📝 Домашнее задание", callback_data=f"homework_{module_id}")
    )
    
    markup.add(
        types.InlineKeyboardButton("✅ Отметить как пройденный", callback_data=f"complete_module_{module_id}"),
        types.InlineKeyboardButton("↩️ К списку модулей", callback_data="back_to_modules")
    )
    
    return markup

# Access code request keyboard
def get_access_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Ввести код доступа", callback_data="enter_access_code"))
    return markup

# Confirm homework submission keyboard
def get_submit_homework_keyboard(module_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Отправить", callback_data=f"submit_homework_{module_id}"),
        types.InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_homework_{module_id}")
    )
    return markup

# Additional materials keyboard
def get_additional_materials_keyboard(module_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("↩️ Назад к модулю", callback_data=f"module_{module_id}"))
    return markup

# Feedback confirmation keyboard
def get_feedback_confirm_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Отправить", callback_data="submit_feedback"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_feedback")
    )
    return markup
