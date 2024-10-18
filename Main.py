import datetime
import functions
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import pandas as pd

secure_df = pd.read_csv('secure_list.csv')
TOKEN = secure_df.loc[secure_df['source'] == 'Telegram', 'api_key'].values[0]


updater = Updater(token=TOKEN, use_context=True)

dispatcher = updater.dispatcher

job = updater.job_queue
job.run_daily(functions.send_rain_notifications, time=datetime.time(hour=9, minute=0, second=00))

dispatcher.add_handler(CommandHandler("start", functions.start))
dispatcher.add_handler(CommandHandler("rain", functions.rain))
dispatcher.add_handler(CommandHandler("choose_city", functions.choose_city))
dispatcher.add_handler(CommandHandler("temperature", functions.temperature))
dispatcher.add_handler(CommandHandler("weather", functions.weather_info))
dispatcher.add_handler(CommandHandler("rain_notifications", functions.rain_notifications))


dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, functions.input))

updater.start_polling()

updater.idle()
