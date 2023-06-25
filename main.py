import logging
import os
import datetime
import psycopg2
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Telegram bot token
bot_token = '6226527400:AAExD7XybEOdVdp3hTpycXsYl0RDRXERhVc'

# Log group ID
log_group_id = '-864625355'  # Replace with the ID of your log group

# List of approved user IDs
approved_user_ids = [5912161237]  # Add the user IDs of approved users here

# Configure logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Heroku PostgreSQL credentials
database_url = os.getenv('DATABASE_URL')

# Connect to the PostgreSQL database
conn = psycopg2.connect(database_url, sslmode='require')
cursor = conn.cursor()

# Create subscriptions table if it doesn't exist
create_table_query = '''CREATE TABLE IF NOT EXISTS subscriptions (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        start_date DATE,
                        end_date DATE
                    )'''
cursor.execute(create_table_query)
conn.commit()

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

        # Store the subscription data in the database
        insert_query = '''INSERT INTO subscriptions (user_id, username, start_date, end_date)
                          VALUES (%s, %s, %s, %s)
                          ON CONFLICT (user_id) DO UPDATE
                          SET username = EXCLUDED.username,
                              start_date = EXCLUDED.start_date,
                              end_date = EXCLUDED.end_date'''
        cursor.execute(insert_query, (user_id, username, current_date, expire_date))
        conn.commit()

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

    replied_user = update.message.reply_to_message.from_user
    user_id = replied_user.id

    if update.message.from_user.id in approved_user_ids:
        # Check if the replied user has an active subscription
        select_query = 'SELECT end_date FROM subscriptions WHERE user_id = %s'
        cursor.execute(select_query, (user_id,))
        result = cursor.fetchone()

        if result is not None:
            end_date = result[0]
            current_date = datetime.datetime.now().date()

            if current_date <= end_date:
                context.bot.send_message(chat_id=update.effective_chat.id, text="The user has an active subscription.")
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text="The user's subscription has expired.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="The user doesn't have an active subscription.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

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

# Close the database connection
cursor.close()
conn.close()
