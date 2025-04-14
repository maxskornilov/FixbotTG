import logging
import os
import telebot
from telebot import types
from config import TOKEN, ACCESS_CODES, TARIFF_DESCRIPTIONS, MODULE_ACCESS, ADMIN_IDS
from database import get_user, add_user, update_user_tariff
import handlers

# Initialize the bot
bot = telebot.TeleBot(TOKEN)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Register handlers
from handlers import (
    register_command_handlers,
    register_message_handlers,
    register_callback_handlers,
    register_admin_handlers,
    register_state_handlers
)

# States for conversation handling
class BotStates:
    AWAITING_ACCESS_CODE = 'awaiting_access_code'
    AWAITING_FEEDBACK = 'awaiting_feedback'
    AWAITING_HOMEWORK_SUBMISSION = 'awaiting_homework_submission'
    CURRENT_MODULE = 'current_module'  # Stores the current module ID for context

# Initialize state storage
user_states = {}
temp_data = {}  # For storing temporary user data during conversations

# Register all handlers
register_command_handlers(bot, user_states, temp_data)
register_message_handlers(bot, user_states, temp_data)
register_callback_handlers(bot, user_states, temp_data)
register_admin_handlers(bot, user_states, temp_data)
register_state_handlers(bot, user_states, temp_data)

logger.info("Bot initialized successfully")
