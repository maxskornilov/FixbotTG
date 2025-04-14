import logging
import os
from bot import bot
from app import app  # Import app from app.py for Flask web application

# This file serves dual purpose: it can start the bot directly (run_telegram_bot workflow)
# or expose app for gunicorn (Start application workflow)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.info("Starting bot...")
    
    # Initialize and start the bot
    bot.polling(none_stop=True, interval=0)
