from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Telegram bot token
bot_token = '5187613700:AAGi2CNj-NrbB1MqKMS9Ft-F7aANxpp1iNk'

# List of approved users
approved_users = ['tiny_pro', 'FRAG_GOD_HACKER']  # Add the usernames of approved users here

# Start command handler
def start_command(update: Update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the subscription bot!")

# Paid command handler
def paid_command(update: Update, context):
    user = update.message.reply_to_message.from_user
    username = user.username
    user_id = user.id
    message_text = update.message.text.strip().split()
    payment_amount = ''.join(filter(str.isdigit, message_text[1]))  # Extract the payment amount

    if username in approved_users:
        output_message = f"Customer - {username} (user id: {user_id}) has paid {payment_amount}."
        context.bot.send_message(chat_id=update.effective_chat.id, text=output_message)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Create the Telegram bot
bot = Bot(token=bot_token)
updater = Updater(bot=bot, use_context=True)

# Register handlers
start_handler = CommandHandler('start', start_command)
paid_handler = CommandHandler('paid', paid_command)
updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(paid_handler)

# Start the bot
updater.start_polling()

# Run the bot until it is stopped manually
updater.idle()
