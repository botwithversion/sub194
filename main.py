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

# Heroku Postgres connection details
db_url = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(db_url)

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

        # Save the log message to the database
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs (user_id, message) VALUES (%s, %s)", (user_id, output_message))
        conn.commit()
        cursor.close()
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Profile command handler
def profile_command(update: Update, context):
    if update.message.reply_to_message is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to a user's message to check their profile.")
        return

    replied_user_id = update.message.reply_to_message.from_user.id

    # Check if the user is an approved user
    if update.message.from_user.id in approved_user_ids:
        cursor = conn.cursor()
        cursor.execute("SELECT message FROM logs WHERE user_id = %s ORDER BY id DESC LIMIT 1", (replied_user_id,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            latest_message = result[0]
            context.bot.send_message(chat_id=update.effective_chat.id, text=latest_message)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="No profile data found for the user.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Check data command handler
def check_data_command(update: Update, context):
    # Check if the user is an approved user
    if update.message.from_user.id in approved_user_ids:
        cursor = conn.cursor()
        cursor.execute("SELECT message FROM logs ORDER BY id DESC LIMIT 10")
        results = cursor.fetchall()
        cursor.close()

        if results:
            data = '\n'.join([result[0] for result in results])
            context.bot.send_message(chat_id=update.effective_chat.id, text=data)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="No data available.")
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

    # Register error handler
    dispatcher.add_error_handler(error)

    # Start the bot
    updater.start_polling()

    # Run the bot until Ctrl-C is pressed
    updater.idle()

if __name__ == '__main__':
    main()
