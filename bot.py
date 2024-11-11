from functools import wraps
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, CallbackContext
from dotenv import load_dotenv, dotenv_values, find_dotenv, get_key

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def with_log_admin(handler):
    @wraps(handler)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            admin_user_id = get_key(find_dotenv(), "ADMIN_ID_LIST")
            user_id = update.effective_user.id
            user_name = update.effective_user.full_name
            command = update.message.text

            if str(user_id) != admin_user_id:
                log_message = f"Command: {command}\nUser ID: {user_id}\nUser Name: {user_name}"
                logger.debug(f"Sending log message to admin: {log_message}")
                try:
                    await context.bot.send_message(chat_id=admin_user_id, text=log_message, parse_mode=ParseMode.MARKDOWN)
                except Exception as e:
                    logger.error(f"Failed to send log message: {e}")

            return await handler(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error: {e}")
            return await handler(update, context, *args, **kwargs)
    return wrapper

def with_typing_action(handler):
    @wraps(handler)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            logger.debug("Sending typing action")
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
            return await handler(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error: {e}")
            return await handler(update, context, *args, **kwargs)
    return wrapper

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    keyboard = [
        [
            InlineKeyboardButton("Learn More", callback_data='learn_more'),
            InlineKeyboardButton("Get Started", callback_data='get_started')
        ],
        [InlineKeyboardButton("Contact Support", callback_data='contact')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        "🚀 Welcome to MyJedi - Your AI-Powered Product Development Partner!\n\n"
        "We combine AI precision with expert human insights to transform your "
        "ideas into reality in just 5 days.\n\n"
        "What would you like to do?"
    )
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

@with_typing_action
@with_log_admin
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'learn_more':
        message = (
            "🌟 *MyJedi: AI + Human Expertise*\n\n"
            "We offer:\n"
            "• AI-powered business planning\n"
            "• Expert human validation\n"
            "• MVP in 5 days\n"
            "• Cost-effective development\n"
            "• Real-time guidance\n\n"
            "Ready to start your journey?"
        )
        keyboard = [[InlineKeyboardButton("Get Started", callback_data='get_started')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == 'get_started':
        message = (
            "🎯 *Let's Begin Your Journey*\n\n"
            "1. Share your product idea\n"
            "2. Receive AI-generated plan\n"
            "3. Get expert validation\n"
            "4. Start MVP development\n\n"
            "Type your product idea below, and our AI will begin analysis!"
        )
        await query.edit_message_text(message, parse_mode='Markdown')
    
    elif query.data == 'contact':
        message = (
            "📞 *Need Support?*\n\n"
            "Our team is here to help!\n"
            "• Email: support@myjedi.ai\n"
            "• Hours: 24/7\n\n"
            "We typically respond within 2 hours."
        )
        keyboard = [[InlineKeyboardButton("Back to Menu", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == 'main_menu':
        await start(update, context)

@with_typing_action
@with_log_admin
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages."""
    if not update.message or not update.message.text:
        return
        
    message = (
        "🤖 *Processing Your Idea*\n\n"
        "Thank you for sharing your concept! Our AI is analyzing your idea:\n\n"
        f"```{update.message.text[:100]}...```\n\n"
        "A Jedi expert will review the AI analysis and provide personalized feedback shortly.\n\n"
        "Expected response time: 2-4 hours"
    )
    
    keyboard = [[InlineKeyboardButton("Back to Menu", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

@with_typing_action
@with_log_admin
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message when the command /help is issued."""
    help_text = (
        "🔍 *MyJedi Bot Help*\n\n"
        "Available commands:\n"
        "/start - Begin your journey\n"
        "/help - Show this help message\n\n"
        "Simply type your product idea to get started!"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Start the bot."""
    # Create the Application
    # 'Updater' object has no attribute '_Updater__polling_cleanup_cb' and no __dict__ for setting new attributes
    # pip install --upgrade python-telegram-
    application = Application.builder().token(os.getenv('DEFAULT_BOT_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()