from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Telegram bot token
bot_token = '5187613700:AAGi2CNj-NrbB1MqKMS9Ft-F7aANxpp1iNk'

# List of approved user IDs
approved_user_ids = [5912161237]  # Add the user IDs of approved users here

# Start command handler
def start_command(update: Update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the subscription bot!")

# Paid command handler
def paid_command(update: Update, context):
    reply_message = update.message.reply_to_message
    if reply_message is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to a user's message to process the payment.")
        return

    user = reply_message.from_user
    user_id = user.id
    message_text = update.message.text.strip().split()

    if len(message_text) < 2:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please specify the payment amount.")
        return

    payment_amount = ''.join(filter(str.isdigit, message_text[1]))  # Extract the payment amount

    if user_id in approved_user_ids:
        output_message = f"Customer - {user_id} has paid {payment_amount}."
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
