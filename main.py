import logging
import datetime
import os
import sqlite3
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Load environment variables
bot_token = os.getenv("BOT_TOKEN")
log_group_id = os.getenv("LOG_GROUP_ID")
approved_user_ids = list(map(int, os.environ.get('APPROVED_USER_IDS', '').split(',')))

# Create SQLite connection
db_file = "subscriptions.db"
conn = sqlite3.connect(db_file)

# Create the subscriptions table if it doesn't exist
create_table_query = """
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER PRIMARY KEY,
    payment_amount TEXT,
    validity_period INTEGER,
    start_date TEXT,
    expire_date TEXT
);
"""
conn.execute(create_table_query)
conn.commit()

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

        output_message += f"Amount: {payment_amount} PD\n"
        output_message += f"Subscription Start: {current_date}\n"
        output_message += f"Valid Till: {expire_date}"

        context.bot.send_message(chat_id=update.effective_chat.id, text=output_message)

        # Log the output message
        logger.info(output_message)

        # Send the log message to the log group
        bot = Bot(token=bot_token)
        bot.send_message(chat_id=log_group_id, text=output_message)

        # Store the subscription data in the database
        insert_query = "INSERT INTO subscriptions (user_id, payment_amount, validity_period, start_date, expire_date) VALUES (?, ?, ?, ?, ?)"
        conn.execute(insert_query, (user_id, payment_amount, validity_period, current_date, expire_date))
        conn.commit()
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not authorized to use this command.")

# Profile command handler
def profile_command(update: Update, context: CallbackContext):
    if update.message.reply_to_message is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to a user's message to check the profile.")
        return

    replied_user_id = update.message.reply_to_message.from_user.id

    select_query = "SELECT * FROM subscriptions WHERE user_id = ?"
    result = conn.execute(select_query, (replied_user_id,))
    subscription = result.fetchone()

    if subscription:
        output_message = f"Subscription Data for User ID: {replied_user_id}\n\n"
        output_message += f"Payment Amount: {subscription[1]} USD\n"
        output_message += f"Validity Period: {subscription[2]} days\n"
        output_message += f"Subscription Start: {subscription[3]}\n"
        output_message += f"Valid Till: {subscription[4]}"
    else:
        output_message = "No subscription data found for the replied user."

    context.bot.send_message(chat_id=update.effective_chat.id, text=output_message)

# Check data command handler
def check_data_command(update: Update, context: CallbackContext):
    select_query = "SELECT * FROM subscriptions"
    result = conn.execute(select_query)
    subscriptions = result.fetchall()

    output_message = "Subscription Data:\n\n"
    if subscriptions:
        for subscription in subscriptions:
            output_message += f"User ID: {subscription[0]}\n"
            output_message += f"Payment Amount: {subscription[1]} USD\n"
            output_message += f"Validity Period: {subscription[2]} days\n"
            output_message += f"Subscription Start: {subscription[3]}\n"
            output_message += f"Valid Till: {subscription[4]}\n\n"
    else:
        output_message += "No subscription data found."

    context.bot.send_message(chat_id=update.effective_chat.id, text=output_message)

# Error handler
def error(update: Update, context: CallbackContext):
    logger.warning(f"Update {update} caused error {context.error}")

def main():
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("paid", paid_command))
    dispatcher.add_handler(CommandHandler("profile", profile_command))
    dispatcher.add_handler(CommandHandler("check_data", check_data_command))

    # Add error handler
    dispatcher.add_error_handler(error)

    updater.start_polling()
    logger.info("Bot started polling.")

    updater.idle()

if __name__ == '__main__':
    main()

# Close the SQLite connection
conn.close()
