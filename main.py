import logging
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Telegram bot token
bot_token = '5187613700:AAGi2CNj-NrbB1MqKMS9Ft-F7aANxpp1iNk'

# Log group ID
log_group_id = '-864625355'  # Replace with the ID of your log group

# List of approved user IDs
approved_user_ids = [5912161237]  # Add the user IDs of approved users here

# Configure logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Start command handler
def start_command(update: Update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the subscription bot!")

# Paid command handler
def paid_command(update: Update, context):
    if update.message.reply_to_message is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to a user's message to process the payment.")
        return

    replied_user = update.message.reply_to_message.from_user
    user_id = replied_user.id
    username = replied_user.username
    first_name = replied_user.first_name
    message_text = update.message.text.strip().split()

    if len(message_text) < 2:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please specify the payment amount.")
        return

    payment_amount = ''.join(filter(str.isdigit, message_text[1]))  # Extract the payment amount

    if update.message.from_user.id in approved_user_ids:
        output_message = "THANKS FOR YOUR SUBSCRIPTION\n"
        output_message += f"User ID: {user_id}\n"

        if username:
            output_message += f"Username: @{username}\n"
        elif first_name:
            output_message += f"First Name: {first_name}\n"

        output_message += f"Amount: {payment_amount} PD"
        context.bot.send_message(chat_id=update.effective_chat.id, text=output_message)

        # Log the output message
        logger.info(output_message)

        # Send the log message to the log group
        bot = Bot(token=bot_token)
        bot.send_message(chat_id=log_group_id, text=output_message)
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
