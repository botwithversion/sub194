import logging
import os
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram bot token
bot_token = os.getenv('BOT_TOKEN')

# Log group ID
log_group_id = os.getenv('LOG_GROUP_ID')

# Approved user IDs
approved_user_ids = list(map(int, os.getenv('APPROVED_USER_IDS').split(',')))

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
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please specify the payment amount and validity period.")
        return

    payment_amount = ''.join(filter(str.isdigit, message_text[1]))  # Extract the payment amount

    # Extract the validity period from the message
    validity_period = 1  # Default validity period is 1 day
    for word in message_text[2:]:
        if word.isdigit():
            validity_period = int(word)
            break

    if update.message.from_user.id in approved_user_ids:
        output_message = "THANKS FOR YOUR SUBSCRIPTION\n"
        output_message += f"User ID: {user_id}\n\n"

        if username:
            output_message += f"Username: @{username}\n\n"
        elif first_name:
            output_message += f"First Name: {first_name}\n\n"

        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        expire_date = (datetime.datetime.now() + datetime.timedelta(days=validity_period)).strftime("%Y-%m-%d")

        output_message += f"Amount: {payment_amount} USD\n"
        output_message += f"Subscription Start: {current_date}\n"
        output_message += f"Valid Till: {expire_date}"

        context.bot.send_message(chat_id=update.effective_chat.id, text=output_message)

        # Log the output message
        logger.info(output_message)

        # Send the log message to the log group
        bot = Bot(token=bot_token)
        bot.send_message(chat_id=log_group_id, text=output_message)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Profile command handler
def profile_command(update: Update, context):
    if update.message.reply_to_message is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to a user's message to check their profile.")
        return

    replied_user_id = update.message.reply_to_message.from_user.id

    if replied_user_id in approved_user_ids:
        context.bot.send_message(chat_id=update.effective_chat.id, text="The replied user has an active subscription.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="The replied user does not have an active subscription.")

# Check data command handler
def check_data_command(update: Update, context):
    if update.message.from_user.id in approved_user_ids:
        for user_id, data in subscriptions.items():
            output_message = f"User ID: {user_id}\n"
            output_message += f"Amount: {data['amount']} USD\n"
            output_message += f"Subscription Start: {data['start_date']}\n"
            output_message += f"Valid Till: {data['expire_date']}\n"
            context.bot.send_message(chat_id=update.effective_chat.id, text=output_message)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Error handler
def error_handler(update: Update, context):
    logger.warning(f"Update {update} caused error {context.error}")

def main():
    # Create the Updater and pass the bot token
    updater = Updater(token=bot_token, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("paid", paid_command))
    dispatcher.add_handler(CommandHandler("profile", profile_command))
    dispatcher.add_handler(CommandHandler("check_data", check_data_command))

    # Register error handler
    dispatcher.add_error_handler(error_handler)

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
