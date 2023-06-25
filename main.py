import os
import logging
import datetime
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Telegram bot token
bot_token = os.environ.get('BOT_TOKEN')

# Log group ID
log_group_id = os.environ.get('LOG_GROUP_ID')

# Approved user IDs
approved_user_ids_str = os.environ.get('APPROVED_USER_IDS')
approved_user_ids = [int(user_id.strip()) for user_id in approved_user_ids_str.split(',')] if approved_user_ids_str else []

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

    # Check if the user is an approved user
    if update.message.from_user.id not in approved_user_ids:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")
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

# Profile command handler
def profile_command(update: Update, context):
    if update.message.reply_to_message is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to a user's message to check their profile.")
        return

    # Check if the user is an approved user
    if update.message.from_user.id not in approved_user_ids:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")
        return

    replied_user = update.message.reply_to_message.from_user
    user_id = replied_user.id

    # Check if the user has an active subscription
    has_active_subscription = False
    for record in logger.records:
        if record.levelname == 'INFO':
            if f"User ID: {user_id}" in record.message:
                valid_till_str = record.message.split("Valid Till: ")[-1]
                valid_till = datetime.datetime.strptime(valid_till_str, "%Y-%m-%d").date()
                if valid_till >= datetime.date.today():
                    has_active_subscription = True
                    break

    if has_active_subscription:
        context.bot.send_message(chat_id=update.effective_chat.id, text="The user has an active subscription.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="The user does not have an active subscription.")

# Create the Telegram bot
bot = Bot(token=bot_token)
updater = Updater(bot=bot, use_context=True)

# Register handlers
start_handler = CommandHandler('start', start_command)
paid_handler = CommandHandler('paid', paid_command)
profile_handler = CommandHandler('profile', profile_command)
updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(paid_handler)
updater.dispatcher.add_handler(profile_handler)

# Start the bot
updater.start_polling()

# Run the bot until it is stopped manually
updater.idle()
