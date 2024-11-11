from functools import wraps
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.constants import ChatAction
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

def with_persistent_user_data(handler):
    @wraps(handler)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            user_id = update.effective_user.id
            user_data = {
                'user_id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'last_name': update.effective_user.last_name,
                'language_code': update.effective_user.language_code,
                'last_message': update.message.text if not update.message.text.startswith('/') else None,
                'last_command': update.message.text if update.message.text.startswith('/') else None,
                'last_message_date': update.message.date if not update.message.text.startswith('/') else None,
                'last_command_date': update.message.date if update.message.text.startswith('/') else None
            }

            # Update or insert persistent user data with user_data dictionary
            await context.application.persistence.update_user_data(user_id, user_data)
            
            # update or insert each item of user_data dictionary in context
            for key, value in user_data.items():
                context.user_data[key] = value
            
            # flush all users data to persistence
            await context.application.persistence.flush()
                
            # re-read all users data from persistence to check if data is stored correctly
            all_users_data = await context.application.persistence.get_user_data()
            this_user_data = context.user_data

            return await handler(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in with_persistent_user_data: {e}")
            return await handler(update, context, *args, **kwargs)
    return wrapper

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

@with_typing_action
@with_log_admin
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

@with_typing_action
@with_log_admin
async def cmd_git(update: Update, context: CallbackContext):
    """Update the bot's version from a git repository"""
    
    try:
        # get the branch name from the message
        # branch_name = update.message.text.split(' ')[1]
        message = f"_Updating the bot's code from the branch..._" # `{branch_name}`"
        logger.info(message)
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        
        # update the bot's code
        # command = f"git fetch origin {branch_name} && git reset --hard origin/{branch_name}"
        command = "git status"
        
        if len(update.effective_message.text.split(' ')) > 1:
            git_command = update.effective_message.text.split(' ')[1]
            logger.info(f"git command: {command}")
            command = f"git {git_command}"
        
        # execute system command and return the result
        # os.system(command=command)
        result = os.popen(command).read()
        logger.info(f"Result: {result}")
        
        result = f"_Result:_ `{result}`"
        
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"An error occurred: {e}")

@with_typing_action
@with_log_admin
async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("_Restarting..._", parse_mode=ParseMode.MARKDOWN)
        args = sys.argv[:]
        args.insert(0, sys.executable)
        os.chdir(os.getcwd())
        os.execv(sys.executable, args)
        
    except Exception as e:
        logger.error(f"Error restarting bot: {e}")
        await update.message.reply_text(f"An error occurred while restarting the bot: {e}")
 
def main():
    """Start the bot."""
 
    # Create the Application
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