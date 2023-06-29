import os
import logging
import datetime
import psycopg2
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Telegram bot token
bot_token = os.environ.get('BOT_TOKEN')

# Log group ID
log_group_id = os.environ.get('LOG_GROUP_ID')

# List of approved user IDs
approved_user_ids = [int(user_id) for user_id in os.environ.get('APPROVED_USER_IDS', '').split(',')]

# Heroku Postgres database URL
db_url = os.environ.get('DATABASE_URL')

# Configure logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Start command handler
def start_command(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the subscription bot!")

# Paid command handler
def paid_command(update: Update, context: CallbackContext):
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

        conn = psycopg2.connect(db_url)
        insert_log(conn, user_id, output_message)
        conn.close()

        context.bot.send_message(chat_id=update.effective_chat.id, text="Payment processed successfully.")
        context.bot.send_message(chat_id=log_group_id, text=output_message)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Profile command handler
def profile_command(update: Update, context: CallbackContext):
    replied_user_id = update.message.reply_to_message.from_user.id

    if update.message.from_user.id in approved_user_ids:
        conn = psycopg2.connect(db_url)
        profile = get_user_profile(conn, replied_user_id)
        conn.close()

        if profile:
            context.bot.send_message(chat_id=update.effective_chat.id, text=profile)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="User profile not found.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Helper function to insert log into the database
def insert_log(connection, user_id, log_message):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO logs (user_id, message) VALUES (%s, %s);
    """, (user_id, log_message))
    connection.commit()
    cursor.close()

# Helper function to retrieve user profile from the database
def get_user_profile(connection, user_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT message FROM logs WHERE user_id = %s;
    """, (user_id,))
    profile = cursor.fetchone()
    cursor.close()

    if profile:
        return profile[0]
    else:
        return None

# Addrefer command handler
def add_refer_command(update: Update, context: CallbackContext):
    if update.message.reply_to_message is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to a user's message to add a referral.")
        return

    replied_user_id = update.message.reply_to_message.from_user.id
    referral_name = update.message.text.strip().split()[1]  # Extract the referral name from the command

    if update.message.from_user.id in approved_user_ids:
        conn = psycopg2.connect(db_url)
        insert_refer(conn, replied_user_id, referral_name)
        conn.close()

        context.bot.send_message(chat_id=update.effective_chat.id, text="Referral added successfully.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Helper function to insert referral name into the database
def insert_refer(connection, user_id, referral_name):
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE logs SET referrals = COALESCE(referrals || ', ', '') || %s WHERE user_id = %s;
    """, (referral_name, user_id))
    connection.commit()
    cursor.close()

# Rmrefer command handler
def rm_refer_command(update: Update, context: CallbackContext):
    if update.message.reply_to_message is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to a user's message to remove a referral.")
        return

    replied_user_id = update.message.reply_to_message.from_user.id

    if update.message.from_user.id in approved_user_ids:
        conn = psycopg2.connect(db_url)
        remove_refer(conn, replied_user_id)
        conn.close()

        context.bot.send_message(chat_id=update.effective_chat.id, text="Referral removed successfully.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Helper function to remove referral from the database
def remove_refer(connection, user_id):
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE logs SET referrals = NULL WHERE user_id = %s;
    """, (user_id,))
    connection.commit()
    cursor.close()

# Error handler
def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Exception occurred", exc_info=context.error)

# Create the Telegram bot and set up the handlers
bot = Bot(token=bot_token)
updater = Updater(bot=bot, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start_command))
dispatcher.add_handler(CommandHandler("paid", paid_command))
dispatcher.add_handler(CommandHandler("profile", profile_command))
dispatcher.add_handler(CommandHandler("addrefer", add_refer_command))
dispatcher.add_handler(CommandHandler("rmrefer", rm_refer_command))
dispatcher.add_error_handler(error_handler)

# Start the bot
updater.start_polling()
updater.idle()
