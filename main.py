import os
import logging
import datetime
import psycopg2
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import dj_database_url

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve the bot token from the environment variable
bot_token = os.environ.get('BOT_TOKEN')

# Retrieve the approved user IDs from the environment variable
approved_user_ids = set(int(user_id) for user_id in os.environ.get('APPROVED_USER_IDS', '').split(','))

# Retrieve the log group ID from the environment variable
log_group_id = os.environ.get('LOG_GROUP_ID')

# Retrieve the database URL from the environment variable
db_url = os.environ.get('DATABASE_URL')
db_conn = dj_database_url.parse(db_url)

# Establish the database connection
conn = psycopg2.connect(
    database=db_conn['NAME'],
    user=db_conn['USER'],
    password=db_conn['PASSWORD'],
    host=db_conn['HOST'],
    port=db_conn['PORT']
)
cursor = conn.cursor()

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

        # Store the subscription details in the database
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
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to a message to view the profile.")
        return

    replied_user = update.message.reply_to_message.from_user
    user_id = replied_user.id

    if update.message.from_user.id in approved_user_ids:
        # Check if the user has an active subscription
        select_query = '''SELECT end_date
                          FROM subscriptions
                          WHERE user_id = %s
                          AND end_date >= CURRENT_DATE'''
        cursor.execute(select_query, (user_id,))
        result = cursor.fetchone()

        if result is not None:
            end_date = result[0]
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"The user has an active subscription. Valid till: {end_date}")
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
