import os
import psycopg2
from telethon.sync import TelegramClient, events

# Telegram API credentials
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
bot_token = os.environ.get('BOT_TOKEN')

# PostgreSQL database credentials
db_url = os.environ.get('DATABASE_URL')

# Initialize the Telegram client
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

# Connect to the PostgreSQL database
conn = psycopg2.connect(db_url)
cursor = conn.cursor()


@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    await event.reply('Welcome to the bot!')


@client.on(events.NewMessage(pattern='/profile'))
async def profile_command(event):
    user_id = event.from_id
    has_subscription, days_left = check_subscription(user_id)

    if has_subscription:
        message = f"Your subscription is valid for {days_left} days."
    else:
        message = "Your subscription has expired."

    await event.respond(message)


@client.on(events.NewMessage(pattern='/sub'))
async def sub_command(event):
    user_id = event.sender_id
    if not is_owner(user_id):
        return

    args = event.raw_text.split()[1:]
    if len(args) != 2:
        await event.reply("Invalid command format. Please use /sub <days> <amount_paid>.")
        return

    days, amount_paid = args
    replied_user_id = event.reply_to_msg_id
    replied_user = await client.get_entity(replied_user_id)
    replied_username = replied_user.username if replied_user.username else replied_user.first_name

    save_subscription(replied_user_id, days, amount_paid)

    group_id = event.chat_id
    message = f"{replied_username}, thanks for subscribing to our bot. Your plan is valid for {days} days. Amount paid: {amount_paid}."
    await client.send_message(group_id, message)


def check_subscription(user_id):
    cursor.execute("SELECT days, amount_paid FROM subscriptions WHERE user_id = %s;", (user_id,))
    subscription = cursor.fetchone()

    if subscription:
        days_left = subscription[0]
        amount_paid = subscription[1]
        return True, days_left, amount_paid
    else:
        return False, None, None


def is_owner(user_id):
    # Replace with your own logic to check if the user is the owner/approved user
    approved_users = [5912161237, 1684703664]
    return user_id in approved_users


def save_subscription(user_id, days, amount_paid):
    cursor.execute("SELECT days FROM subscriptions WHERE user_id = %s;", (user_id,))
    existing_subscription = cursor.fetchone()

    if existing_subscription:
        # Update the existing subscription
        days_left = existing_subscription[0] + int(days)
        cursor.execute("UPDATE subscriptions SET days = %s, amount_paid = %s WHERE user_id = %s;",
                       (days_left, amount_paid, user_id))
    else:
        # Insert a new subscription
        cursor.execute("INSERT INTO subscriptions (user_id, days, amount_paid) VALUES (%s, %s, %s);",
                       (user_id, days, amount_paid))

    conn.commit()


# Create the subscriptions table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id BIGINT PRIMARY KEY,
        days INTEGER,
        amount_paid INTEGER
    );
""")
conn.commit()


# Start the client
client.run_until_disconnected()
