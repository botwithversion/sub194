import os
from telethon.sync import TelegramClient, events

# Your Telegram API credentials
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
bot_token = os.environ.get('BOT_TOKEN')

# Initialize the Telegram client
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)


@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    await event.reply('Welcome to the bot!')


@client.on(events.NewMessage(pattern='/profile'))
async def profile_command(event):
    # Check if the user has an active subscription
    # You'll need to implement your own logic to fetch the subscription details for the user
    user_id = event.sender_id
    has_subscription, days_left = check_subscription(user_id)

    if has_subscription:
        await event.reply(f"You have {days_left} days left in your subscription.")
    else:
        await event.reply("Your subscription has expired or you are not a subscriber.")


@client.on(events.NewMessage(pattern='/sub'))
async def sub_command(event):
    # Check if the user is the owner/approved user
    user_id = event.sender_id
    if not is_owner(user_id):
        return

    # Parse the command arguments
    args = event.raw_text.split()[1:]
    if len(args) != 2:
        await event.reply("Invalid command format. Please use /sub <days> <amount_paid>.")
        return

    days, amount_paid = args
    user_id = event.reply_to_msg_id
    username = await client.get_entity(user_id)

    # Save the subscription details to your database
    save_subscription(user_id, days, amount_paid)

    # Send the subscription details in the group
    group_id = event.chat_id
    message = f"{username} thanks for subscribing to our bot. Your plan is valid till {days} days. Your amount paid: {amount_paid}."
    await client.send_message(group_id, message)


def check_subscription(user_id):
    # Implement your own logic to check the subscription details for the user
    # Return a tuple (has_subscription, days_left)
    # If the subscription is expired, return (False, None)
    # If the user is not a subscriber, return (False, None)
    pass


def is_owner(user_id):
    # Implement your own logic to check if the user is the owner/approved user
    pass


def save_subscription(user_id, days, amount_paid):
    # Implement your own logic to save the subscription details to your database
    pass


# Start the client
client.run_until_disconnected()
