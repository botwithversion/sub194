# Rest of your code...

# Inline button callback query handler
def callback_query_handler(update: Update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    if data.startswith('profile|'):
        user_id = int(data.split("|")[1])
        conn = psycopg2.connect(db_url)
        profile = get_user_profile(conn, user_id)
        conn.close()

        if profile:
            # Extract the user's profile data from the message
            profile_data = profile.split('\n\n')[-1]
            query.edit_message_text(text=profile_data)
        else:
            query.edit_message_text(text="No profile data found for the user.")

# Rest of your code...

def main():
    # Rest of your code...

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Rest of your code...

    # Register callback query handler for inline buttons
    dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))

    # Rest of your code...

if __name__ == '__main__':
    main()
