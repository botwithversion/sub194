import os
import logging
import datetime
import psycopg2
from telegram import Bot, Update, Chat
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
            context.bot.send_message(chat_id=update.effective_chat.id, text=profile[0])
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="No profile found for the user.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Check_data command handler
def check_data_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id in approved_user_ids:
        conn = psycopg2.connect(db_url)
        data_count = get_data_count(conn)
        conn.close()

        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Total data count: {data_count}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Clear_all command handler
def clear_all_command(update: Update, context: CallbackContext):
    if update.message.chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
        context.bot.send_message(chat_id=update.effective_chat.id, text="This command can only be used in a group or supergroup.")
        return

    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    if user_id in approved_user_ids:
        context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

        # Delete all messages in the chat
        messages = context.bot.get_chat(chat_id).get('all_members_are_administrators')
        for message in messages:
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)

        # Leave the chat
        context.bot.leave_chat(chat_id=chat_id)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Error handler
def error(update: Update, context: CallbackContext):
    logger.warning(f"Update {update} caused error {context.error}")

# Helper function to insert log into the database
def insert_log(conn, user_id, log_message):
    cur = conn.cursor()
    cur.execute("INSERT INTO logs (user_id, log_message) VALUES (%s, %s)", (user_id, log_message))
    conn.commit()

# Helper function to retrieve user profile from the database
def get_user_profile(conn, user_id):
    cur = conn.cursor()
    cur.execute("SELECT log_message FROM logs WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
    return cur.fetchone()

# Helper function to retrieve data count from the database
def get_data_count(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM logs")
    return cur.fetchone()[0]

def main():
    # Create the Telegram Updater and pass in the bot's token
    updater = Updater(bot_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("paid", paid_command))
    dispatcher.add_handler(CommandHandler("profile", profile_command))
    dispatcher.add_handler(CommandHandler("check_data", check_data_command))
    dispatcher.add_handler(CommandHandler("clearall", clear_all_command))  # Add clearall command handler

    # Register error handler
    dispatcher.add_error_handler(error)  # Add error handler

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
