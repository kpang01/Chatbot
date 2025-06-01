# gemini_multichat_bot/platforms/telegram_bot.py

import logging
import os
import re # For parsing due date in add_task_command
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue
import pytz # Import pytz

# Import core logic
from core import main as core_logic # Assuming core.main has the chatbot logic

# .env loading is now primarily handled by core/main.py
# However, TELEGRAM_BOT_TOKEN is needed here before Application setup.
# Ensure .env is loaded early enough for all modules.
# The load_dotenv in core/main.py should make TELEGRAM_BOT_TOKEN available if .env is correct.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# If TELEGRAM_BOT_TOKEN is still None here, it means .env wasn't loaded before this line,
# or the token is missing from .env. core/main.py's load_dotenv should cover it.

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user = update.effective_user
    welcome_message = (
        f"Hello {user.mention_html()}! I'm a friendly chatbot powered by Gemini, here to chat with you.\n\n"
        "Feel free to ask me anything or just say hello!\n\n"
        "Type /help for more information."
    )
    await update.message.reply_html(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the /help command is issued."""
    help_text = (
        "I'm a conversational chatbot powered by Gemini.\n\n"
        "You can chat with me about various topics, ask questions, or just have a friendly conversation.\n\n"
        "<b>Commands:</b>\n"
        "  /start - Get the welcome message.\n"
        "  /help - Show this help message.\n\n"
        "Just type your message, and I'll do my best to respond!"
    )
    await update.message.reply_html(help_text, disable_web_page_preview=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles non-command messages using Gemini."""
    user_id = str(update.effective_user.id)
    text = update.message.text

    # Use the new generate_chat_response function from core_logic
    response_text = core_logic.generate_chat_response(user_id, text)
    await update.message.reply_text(response_text)


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables. Bot cannot start.")
        return

    # Create the Application and pass it your bot's token.
    # Explicitly create JobQueue with a timezone to address apscheduler issue
    job_queue = JobQueue()
    # Ensure the scheduler associated with this job_queue has its timezone configured
    # This might require a different way to set it if JobQueue() doesn't allow direct scheduler config at init
    # For now, let's assume python-telegram-bot's default JobQueue will pick up pytz if available
    # or we might need to pass a pre-configured scheduler.
    # Re-attempting the explicit configuration:
    if job_queue.scheduler:
        try:
            job_queue.scheduler.configure(timezone=pytz.utc)
        except Exception as e:
            logger.warning(f"Could not directly configure job_queue scheduler timezone: {e}. Relying on defaults.")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).job_queue(job_queue).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    # Removed task-specific command handlers: add, list, done, reminders

    # Message handler for general text (to be processed by Gemini)
    # This remains the same as it uses core_logic.generate_chat_response
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Starting Telegram bot (Chat Mode)...")
    application.run_polling()
    logger.info("Telegram bot stopped.")

if __name__ == "__main__":
    main()
