# Telegram Bot for Managing Subscriptions

This is a Telegram bot that helps manage subscriptions. It allows users to start, view their profile, and subscribe to the bot's services.

## Deploy to Heroku

You can easily deploy this bot to Heroku by clicking the button below:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Getting Started

To get started with the bot, follow these steps:

1. Clone this repository.
2. Set up a Telegram bot and obtain your API credentials.
3. Set up a PostgreSQL database and obtain the database URL.
4. Update the `app.json` file with your credentials and URLs.
5. Commit and push your changes to your GitHub repository.
6. Click the "Deploy to Heroku" button above to deploy the bot.
7. Provide the required environment variables in the Heroku dashboard.
8. Launch the bot on Heroku and start interacting with it on Telegram.

## Bot Commands

The bot supports the following commands:

- `/start` - Start the bot and receive a welcome message.
- `/profile` - View your subscription profile and remaining days.
- `/sub <days> <amount_paid>` - Subscribe to the bot's services (owner/approved user only).

## License

This project is licensed under the [MIT License](LICENSE).
