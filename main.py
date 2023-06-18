import os
import psycopg2
from telethon import TelegramClient, events

# Telegram API credentials
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
bot_token = os.environ.get('BOT_TOKEN')

# Database credentials
db_url = os.environ.get('DATABASE_URL')

# Initialize the Telegram client
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Connect to the PostgreSQL database
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# /start command handler
@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    await event.respond('Welcome to the bot!')

# /profile command handler
@client.on(events.NewMessage(pattern='/profile'))
async def profile_command(event):
    user_id = event.from_id
    has_subscription, days_left = check_subscription(user_id)

    if has_subscription:
        message = f"Your subscription is valid for {days_left} days."
    else:
        message = "Your subscription has expired."

    await event.respond(message)

# /sub command handler (for the bot owner)
@client.on(events.NewMessage(pattern='/sub'))
async def sub_command(event):
    if event.sender_id == int(os.environ.get('BOT_OWNER_ID')):
        command_args = event.raw_text.split()
        if len(command_args) == 3:
            user_id = event.reply_to_msg_id
            days = command_args[1]
            amount_paid = command_args[2]

            store_subscription(user_id, days, amount_paid)

            message = f"{user_id} thanks for subscribing to our bot. Your plan is valid till {days} days. Your amount paid: {amount_paid}."
            await event.respond(message)

# Function to check user subscription
def check_subscription(user_id):
    cursor.execute("SELECT days, amount_paid FROM subscriptions WHERE user_id = %s;", (user_id,))
    result = cursor.fetchone()

    if result is not None:
        days_left, amount_paid = result
        has_subscription = True
    else:
        days_left = 0
        amount_paid = 0
        has_subscription = False

    return has_subscription, days_left

# Function to store user subscription
def store_subscription(user_id, days, amount_paid):
    cursor.execute("INSERT INTO subscriptions (user_id, days, amount_paid) VALUES (%s, %s, %s);", (user_id, days, amount_paid))
    conn.commit()

# Start the Telegram client
client.run_until_disconnected()
