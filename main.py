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
    user = update.message.from_user
    user_id = user.id
    payment_amount = None

    if len(update.message.text.split()) > 1:
        payment_amount = update.message.text.split()[1]

    output_message = "THANKS FOR YOUR SUBSCRIPTION\n"
    output_message += f"User id: {user_id}\n"

    if user.username:
        output_message += f"Username: @{user.username}\n"
    else:
        output_message += f"Username: {user.first_name}\n"

    if payment_amount:
        output_message += f"Amount: {payment_amount}"
    else:
        output_message += "Amount: Not specified"

    context.bot.send_message(chat_id=update.effective_chat.id, text=output_message)

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
