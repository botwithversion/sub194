import os
import logging
import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve the bot token from the environment variable
bot_token = os.environ.get('BOT_TOKEN')

# Retrieve the approved user IDs from the environment variable
approved_user_ids = set(int(user_id) for user_id in os.environ.get('APPROVED_USER_IDS', '').split(','))

# Start command handler
def start_command(update: Update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the bot!")

# Paid command handler
def paid_command(update: Update, context):
    if update.message.reply_to_message is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to a message to process the payment.")
        return

    replied_user = update.message.reply_to_message.from_user
    user_id = replied_user.id
    username = replied_user.username
    first_name = replied_user.first_name

    if update.message.from_user.id in approved_user_ids:
        message_text = update.message.text.split()
        payment_amount = ''.join(filter(str.isdigit, message_text[1])) if len(message_text) > 1 else None
        expire_days = ''.join(filter(str.isdigit, message_text[2])) if len(message_text) > 2 else '1'
        current_date = datetime.datetime.now().date()
        expire_date = current_date + datetime.timedelta(days=int(expire_days))

        if username is not None:
            user_info = f"Username: @{username}"
        else:
            user_info = f"First Name: {first_name}"

        output_message = f"THANKS FOR YOUR SUBSCRIPTION\n" \
                         f"User ID: {user_id}\n" \
                         f"{user_info}\n" \
                         f"Amount: {payment_amount}\n" \
                         f"Subscription Valid till: {expire_date}"

        # Log the output message to the log group
        logger.info(output_message)

        # Send the log message to the log group
        log_group_id = os.environ.get('LOG_GROUP_ID')
        context.bot.send_message(chat_id=log_group_id, text=output_message)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Profile command handler
def profile_command(update: Update, context):
    if update.message.reply_to_message is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to a message to view the profile.")
        return

    replied_user = update.message.reply_to_message.from_user
    user_id = replied_user.id

    if update.message.from_user.id in approved_user_ids:
        # Check if the user has an active subscription by searching for their user ID in the log group messages
        log_group_id = os.environ.get('LOG_GROUP_ID')
        chat_messages = context.bot.get_chat(chat_id=log_group_id).get('messages')
        subscription_messages = [message for message in chat_messages if str(user_id) in message.get('text', '')]

        if subscription_messages:
            context.bot.send_message(chat_id=update.effective_chat.id, text="The user has an active subscription.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="The user does not have an active subscription.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Error handler
def error_handler(update: Update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

# Create the Telegram bot
updater = Updater(bot_token, use_context=True)
dispatcher = updater.dispatcher

# Register the command handlers
dispatcher.add_handler(CommandHandler("start", start_command))
dispatcher.add_handler(CommandHandler("paid", paid_command))
dispatcher.add_handler(CommandHandler("profile", profile_command))

# Register the error handler
dispatcher.add_error_handler(error_handler)

# Start the bot
updater.start_polling()
