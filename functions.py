import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from telegram import Update
from telegram.ext import CallbackContext
import datetime
import requests
import json

secure_df = pd.read_csv('secure_list.csv')
API_WEATHER = secure_df.loc[secure_df['source'] == 'OpenWeatherMap', 'api_key'].values[0]
USER_CITY_PATH = secure_df.loc[secure_df['source'] == 'UserCityPath', 'api_key'].values[0]
INQUIRIES_PATH = secure_df.loc[secure_df['source'] == 'AllInquiresPath', 'api_key'].values[0]
RAIN_USERS_PATH = secure_df.loc[secure_df['source'] == 'RainNotificationsPath', 'api_key'].values[0]
MIN_INQURIES = 20

user_city = pd.read_csv(USER_CITY_PATH)
all_inquiries = pd.read_csv(INQUIRIES_PATH)
rain_users = pd.read_csv(RAIN_USERS_PATH)


#HELPING FUNCTIONS
def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_WEATHER}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        weather = data['weather'][0]['main']
        return temp, weather
    return None, None


def save_inquiry(user_id, city, weather, temp):
    global all_inquiries
    current_date = datetime.datetime.today().strftime('%Y-%m-%d')
    all_inquiries = pd.concat([all_inquiries, pd.DataFrame({'user_id': [user_id], 'city': [city],
                                                            'date': [current_date], 'weather': [weather],
                                                            'temperature': [temp], 'score': [None]})], ignore_index=True)
    all_inquiries.to_csv(INQUIRIES_PATH, index=False)


def predict_score(user_id, city, temp, weather):
    user_df = all_inquiries[all_inquiries['user_id'] == user_id].dropna()
    X = user_df[['city', 'weather', 'temperature']]
    user_df['date'] = pd.to_datetime(user_df['date'])
    X = X.assign(year=user_df['date'].dt.year,
                 month=user_df['date'].dt.month,
                 day=user_df['date'].dt.day)
    X = pd.get_dummies(X)
    X_pred = X.loc[[X.index[-1]]]
    X = X.loc[X.index[:-1]]
    y = user_df['score']
    y = y.loc[y.index[:-1]]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_test_pred = model.predict(X_test)

    if r2_score(y_test, y_test_pred) < 0.7:
        return -1

    y_pred = model.predict(X_test)
    return y_pred[0].round(1)


#COMMANDS
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello! I'll help you find out if it''s nice outside! \n"
                              "Choose your city to check the weather conditions, and rate them.")

def choose_city(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    context.user_data['choosing_city'] = True
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the name of the city.")


def rain(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"I'm going outside to check the weather:)")
    if user_id in user_city['user_id'].values:
        city = user_city[user_city['user_id'] == user_id].iloc[0]['city']
        temp, weather = get_weather(city)
        if weather == 'Rain':
            context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"It's going to rain in {city}, you better bring an umbrella! But it's still nice,"
                                      f" isn't it? Use the 'weather' command to rate this rainy day!")
        else :
            context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"You're safe from rain."
                                      f" Use the 'weather' command to rate this nice day :)")

    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please use the 'choose_city' command to enter your city.")


def rain_notifications(update: Update, context: CallbackContext):
    global rain_users
    rain_users_dict = rain_users.set_index('user_id')['send'].to_dict()
    user_id = update.message.from_user.id
    if user_id in rain_users_dict.keys():
        if  rain_users_dict[user_id] == 1:
            rain_users_dict[user_id] = 0
            context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"I'll stop sending you rain notifications. \nIf you want to receive them "
                                      f"use the 'rain_notifications' command again.")

        else:
            rain_users_dict[user_id] = 1
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"From now on I'll send you rain notifications at 9 am everyday. \n"
                                          f"If you want to stop receiving them use the 'rain_notifications' command again.")

    rain_users= pd.DataFrame(list(rain_users_dict.items()), columns=['user_id', 'send'])
    rain_users.to_csv(RAIN_USERS_PATH, index=False)




def send_rain_notifications(context: CallbackContext):
    global rain_users
    rain_users_dict = rain_users.set_index('user_id')['send'].to_dict()
    for user_id in rain_users_dict.keys():
        if rain_users_dict[user_id] == 1:
            if user_id in user_city['user_id'].values:
                city = user_city[user_city['user_id'] == user_id].iloc[0]['city']
                temp, weather = get_weather(city)
                if (weather == 'Rain'):
                    context.bot.send_message(chat_id=int(user_id),
                                text=f"It's going to rain in {city}, you better bring an umbrella! Have a nice day!")
                else:
                    context.bot.send_message(chat_id=int(user_id),
                                text=f"No rain for now, have a nice day:)")
            else:
                context.bot.send_message(chat_id=int(user_id),
                                        text=f"Sadly, I don't know where you are, please use the 'choose_city' "
                                             f"command to let me know.")




def temperature(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_city['user_id'].values:
        city = user_city.loc[user_city['user_id'] == user_id, 'city'].values[0]
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"I'm going outside to check the weather:)")
        temp, weather = get_weather(city)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"The temperature in {city} is {temp}°C.")

    else :
        context.bot.send_message(chat_id=update.effective_chat.id, text = "Please use the 'choose_city' command to enter your city.")


def weather_info(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"I'm going outside to check the weather:)")
    if user_id in user_city['user_id'].values:
        city = user_city.loc[user_city['user_id'] == user_id, 'city'].values[0]
        temp, weather = get_weather(city)
        if ((all_inquiries[all_inquiries['user_id'] == user_id].shape[0] > MIN_INQURIES) and
                (all_inquiries[(all_inquiries['user_id'] == user_id) & (all_inquiries['city'] == city)].shape[0] > MIN_INQURIES//3)):
            score_pred = predict_score(user_id, city, weather, temp)
            if score_pred != -1:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"It's nice outside! It's {weather} and {temp}°C in {city}. \nAccording to "
                                          f"your previous responses, I'd guess your rating would be around {score_pred}."
                                          f"\nTell me how do you really enjoy this weather? Please rate it from 1 to 5 in the next message.")
            else:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=f"It's nice outside! It's {weather} and {temp}°C in {city}. "
                                              f"\nHow do you enjoy this weather? Please rate it from 1 to 5 in the next message.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"It's nice outside! It's {weather} and {temp}°C in {city}. "
                                          f"\nHow do you enjoy this weather? Please rate it from 1 to 5 in the next message.")

        context.user_data['rating_weather'] = True
        save_inquiry(user_id, city, weather, temp)

    else :
        context.bot.send_message(chat_id=update.effective_chat.id, text = "Please use the 'choose_city' command to enter your city.")


def input(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_text = update.message.text
    global user_city, all_inquiries

    #CITY INPUT
    if context.user_data.get('choosing_city', False):
        temp, weather = get_weather(user_text)
        context.user_data['choosing_city'] = False
        if temp is not None:
            if user_id in user_city['user_id'].values:
                user_city.loc[user_city['user_id'] == user_id, 'city'] = user_text

            else:
                new_user_city = pd.DataFrame({'user_id': [user_id], 'city': [user_text]})
                user_city = pd.concat([user_city, new_user_city], ignore_index=True)

            user_city.to_csv(USER_CITY_PATH, index=False)

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Your city is {user_text}. I'll save it for your next inquiries, "
                                          f"if you want to change it please use the 'choose_city' command again.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Sorry, I couldn't find the city '{user_text}'. "
                                          f"Please use the 'choose_city' command to enter your city.")

    #SCORE INPUT
    elif context.user_data.get('rating_weather', False):
        context.user_data['rating_weather'] = False
        if user_text.isdigit() and float(user_text) <= 5 and float(user_text) >= 1:
            score = float(user_text)
            all_inquiries.loc[all_inquiries.index[-1], 'score'] = score

            all_inquiries.to_csv('all_inquiries.csv', index=False)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Thank you! I will save it for predicting your mood in the future!")


        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Sorry, the score you provided is not in the range from 1 to 5. "
                                          f"Please use the 'weather' command again to rate the weather conditions.")

    #NO COMMAND INPUT
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"I didn't quite understood you, please use one of the commands. Or just go outside. it's nice out there!")
