import os
import logging
import datetime
import psycopg2
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

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

        conn = psycopg2.connect(db_url)
        insert_log(conn, user_id, output_message)
        conn.close()

        context.bot.send_message(chat_id=update.effective_chat.id, text="Payment processed successfully.")
        context.bot.send_message(chat_id=log_group_id, text=output_message)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Profile command handler
def profile_command(update: Update, context):
    replied_user_id = update.message.reply_to_message.from_user.id

    if update.message.from_user.id in approved_user_ids:
        conn = psycopg2.connect(db_url)
        profile = get_user_profile(conn, replied_user_id)
        conn.close()

        if profile:
            context.bot.send_message(chat_id=update.effective_chat.id, text=profile[profile.find("\n\n")+2:])
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="No profile data found for the user.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Check data command handler
def check_data_command(update: Update, context):
    if update.message.from_user.id in approved_user_ids:
        conn = psycopg2.connect(db_url)
        data = get_all_data(conn)
        conn.close()

        if data:
            context.bot.send_message(chat_id=update.effective_chat.id, text=data[data.find("\n\n")+2:])
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="No data available.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Clear all command handler
def clear_all_command(update: Update, context):
    if update.message.from_user.id in approved_user_ids:
        chat_id = update.effective_chat.id

        # Delete all messages in the chat
        context.bot.delete_chat(chat_id)

        # Leave the chat
        context.bot.leave_chat(chat_id)

    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Expiring command handler
def expiring_command(update: Update, context):
    if update.message.from_user.id in approved_user_ids:
        conn = psycopg2.connect(db_url)
        expiring_users = get_expiring_subscriptions(conn)
        conn.close()

        if expiring_users:
            message = "Subscriptions expiring today:\n\n"
            for user_id, username in expiring_users:
                message += f"User ID: {user_id}"
                if username:
                    message += f" (@{username})"
                message += "\n"
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="No subscriptions expiring today.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Error handler
def error(update: Update, context):
    logger.warning(f"Update {update} caused error {context.error}")

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
    dispatcher.add_handler(CommandHandler("clearall", clear_all_command))
    dispatcher.add_handler(CommandHandler("expiring", expiring_command))

    # Register error handler
    dispatcher.add_error_handler(error)

    # Connect to the database
    conn = psycopg2.connect(db_url)

    # Create the "logs" table if it doesn't exist
    create_logs_table(conn)

    # Start the bot
    updater.start_polling()

    # Run the bot until Ctrl-C is pressed
    updater.idle()

def create_logs_table(connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            message TEXT
        );
    """)
    connection.commit()
    cursor.close()

def insert_log(connection, user_id, message):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO logs (user_id, message)
        VALUES (%s, %s);
    """, (user_id, message))
    connection.commit()
    cursor.close()

def get_user_profile(connection, user_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT message FROM logs WHERE user_id = %s ORDER BY id DESC LIMIT 1;
    """, (user_id,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def get_all_data(connection):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT message FROM logs;
    """)
    result = cursor.fetchall()
    cursor.close()
    return '\n\n'.join([row[0] for row in result])

def get_expiring_subscriptions(connection):
    cursor = connection.cursor()
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT user_id, username FROM logs WHERE SUBSTRING(message, 'Valid Till: (\d{4}-\d{2}-\d{2})') = %s;
    """, (current_date,))
    result = cursor.fetchall()
    cursor.close()
    return result

if __name__ == '__main__':
    main()
