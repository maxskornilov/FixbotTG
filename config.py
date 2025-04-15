import os

# Bot configuration
TOKEN = os.getenv('BOT_TOKEN')

# Database configuration
DATABASE_URL = 'sqlite:///course_bot.db'

# Admin user IDs (for special commands)
ADMIN_IDS = [
    # Add admin user IDs here, e.g., 123456789
]

# Access codes for different tariffs
ACCESS_CODES = {
    'basic': ['basic123', 'basic456'],
    'standard': ['standard123', 'standard456'],
    'premium': ['premium123', 'premium456'],
    'transition': ['transition123', 'transition456']
}

# Tariff descriptions
TARIFF_DESCRIPTIONS = {
    'basic': 'Базовый тариф: доступ к модулям 1-3',
    'standard': 'Стандартный тариф: доступ к модулям 1-5',
    'premium': 'Премиум тариф: доступ к модулям 1-8',
    'transition': 'Тариф "Переход": полный доступ ко всем модулям и персональная поддержка'
}

# Module access by tariff
MODULE_ACCESS = {
    'basic': [1, 2, 3],
    'standard': [1, 2, 3, 4, 5],
    'premium': [1, 2, 3, 4, 5, 6, 7, 8],
    'transition': [1, 2, 3, 4, 5, 6, 7, 8]
}
