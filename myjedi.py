import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Set your API keys
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
OPENAI_API_KEY = 'YOUR_OPENAI_API_KEY'
openai.api_key = OPENAI_API_KEY

# Store conversation states and business plans
customer_ideas = {}

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Please share your product idea, and I'll generate a simple business plan for it."
    )

# Handler to process the product pitch
async def handle_pitch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    idea = update.message.text

    # Store the idea
    customer_ideas[user_id] = idea

    # Generate business plan with OpenAI
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Create a simple business plan for this product idea: {idea}",
        max_tokens=200,
        temperature=0.7,
    )
    business_plan = response.choices[0].text.strip()

    # Send the generated business plan to the customer
    await update.message.reply_text(
        f"Here's a simple business plan for your idea:\n\n{business_plan}\n\n"
        "If you're happy with this, reply with 'approve' to submit it for specialist analysis."
    )

    # Save business plan for later reference
    customer_ideas[user_id] = {
        "idea": idea,
        "business_plan": business_plan,
        "approved": False
    }

# Handler for customer approval
async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    text = update.message.text.lower()

    # Check if user has submitted an idea
    if user_id not in customer_ideas:
        await update.message.reply_text("Please submit your product idea first.")
        return

    # Approve and forward to mentor if customer approves
    if text == "approve":
        customer_ideas[user_id]["approved"] = True

        # Forward business plan to the mentor (replace with actual mentor's chat ID)
        MENTOR_CHAT_ID = 987654321
        idea = customer_ideas[user_id]["idea"]
        business_plan = customer_ideas[user_id]["business_plan"]

        await context.bot.send_message(
            chat_id=MENTOR_CHAT_ID,
            text=f"New product idea for review:\n\nIdea: {idea}\n\nBusiness Plan:\n{business_plan}"
        )

        # Notify customer
        await update.message.reply_text(
            "Thank you! Your idea is now under specialist analysis. We'll update you soon."
        )
    else:
        await update.message.reply_text(
            "If you approve the business plan, please reply with 'approve' to submit it."
        )

# Main function to set up the bot
async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pitch))
    app.add_handler(MessageHandler(filters.Regex(r'(?i)\bapprove\b'), handle_approval))

    # Run the bot
    await app.run_polling()

# Entry point
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())