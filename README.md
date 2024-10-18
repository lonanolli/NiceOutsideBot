# Nice Outside

Nice Outside is a Telegram bot that provides real-time weather information, alerts users about rain, and attempts to predict their satisfaction with the weather based on previous responses.

Find it [here](t.me/aaahwhatshouldIwear_bot).


## Features

- **Weather Information**: Get the current temperature and weather conditions for your selected city.
- **Umbrella Notifications**: Receive alerts when rain is expected.
- **User-Specific Data**: The bot remembers users' selected cities for future queries, allowing for a personalized experience.
- **Satisfaction score**: Rate your enjoyment of the weather on a scale, and the bot will learn from your feedback to predict your scores in future.

## Setup Requirements

To run this bot, you need to add your [Telegram Bot](https://telegram.me/BotFather) token and API from [OpenWeatherMap](https://openweathermap.org/) to the following file:

- **secure_list.csv**: This file contains your API keys and paths. 

```csv
source,api_key
OpenWeatherMap,YOUR_API_KEY
Telegram,YOUR_TOKEN
UserCityPath,user_cities.csv
AllInquiresPath,all_inquiries.csv
RainNotificationsPath,rain_users.csv
