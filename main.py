import psycopg2
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

bot_token = "YOUR_BOT_TOKEN"
log_group_id = "LOG_GROUP_ID"
approved_user_ids = [12345678, 87654321]  # Approved user IDs
db_url = "YOUR_DATABASE_URL"

# Start command
def start_command(update: Update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome! Use /paid to register your subscription.")

# Paid command
def paid_command(update: Update, context):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    start_date = update.message.date.strftime("%Y-%m-%d")
    end_date = (update.message.date + timedelta(days=30)).strftime("%Y-%m-%d")

    conn = psycopg2.connect(db_url)
    save_subscription_details(conn, user_id, username, start_date, end_date)
    conn.close()

    context.bot.send_message(chat_id=update.effective_chat.id, text="Subscription registered successfully.")

# Profile command
def profile_command(update: Update, context):
    user_id = update.message.from_user.id

    if user_id in approved_user_ids:
        conn = psycopg2.connect(db_url)
        profile = get_user_profile(conn, user_id)
        conn.close()

        if profile:
            context.bot.send_message(chat_id=update.effective_chat.id, text=profile)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="No subscription found for the user.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Expiring command
def expiring_command(update: Update, context):
    user_id = update.message.from_user.id

    if user_id in approved_user_ids:
        conn = psycopg2.connect(db_url)
        expiring_users = get_expiring_users(conn)
        conn.close()

        if expiring_users:
            message = "Expiring subscriptions:\n\n"
            for user in expiring_users:
                message += f"Username: @{user[0]}\n"
                message += f"End Date: {user[1]}\n\n"
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="No expiring subscriptions found.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not an approved user.")

# Message handler
def message_handler(update: Update, context):
    if update.message.reply_to_message is not None and update.message.from_user.id in approved_user_ids:
        replied_user_id = update.message.reply_to_message.from_user.id
        user_id = update.message.from_user.id
        message_text = update.message.text

        conn = psycopg2.connect(db_url)
        profile = get_user_profile(conn, replied_user_id)

        if profile:
            log_message = f"User ID: {user_id}\n\nMessage:\n{message_text}"
            insert_log(conn, user_id, log_message)
            conn.close()

            context.bot.send_message(chat_id=update.effective_chat.id, text="Message logged successfully.")
            context.bot.send_message(chat_id=log_group_id, text=log_message)
        else:
            conn.close()
            context.bot.send_message(chat_id=update.effective_chat.id, text="No subscription found for the user.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not allowed to log messages.")

# Save subscription details
def save_subscription_details(conn, user_id, username, start_date, end_date):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO subscriptions (user_id, username, start_date, end_date)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET username = excluded.username, start_date = excluded.start_date, end_date = excluded.end_date
        """,
        (user_id, username, start_date, end_date)
    )
    conn.commit()

# Get user profile
def get_user_profile(conn, user_id):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT username, start_date, end_date
        FROM subscriptions
        WHERE user_id = %s
        """,
        (user_id,)
    )
    profile = cursor.fetchone()
    if profile:
        return f"Username: @{profile[0]}\nStart Date: {profile[1]}\nEnd Date: {profile[2]}"
    else:
        return None

# Get expiring users
def get_expiring_users(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT username, end_date
        FROM subscriptions
        WHERE end_date = current_date
        """
    )
    expiring_users = cursor.fetchall()
    return expiring_users

# Insert log
def insert_log(conn, user_id, message):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO logs (user_id, message)
        VALUES (%s, %s)
        """,
        (user_id, message)
    )
    conn.commit()

# Set up the bot
def main():
    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start_command)
    dispatcher.add_handler(start_handler)

    paid_handler = CommandHandler('paid', paid_command)
    dispatcher.add_handler(paid_handler)

    profile_handler = CommandHandler('profile', profile_command)
    dispatcher.add_handler(profile_handler)

    expiring_handler = CommandHandler('expiring', expiring_command)
    dispatcher.add_handler(expiring_handler)

    message_handler = MessageHandler(Filters.text & ~Filters.command, message_handler)
    dispatcher.add_handler(message_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
