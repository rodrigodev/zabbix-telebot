from telegram.ext import Updater, CommandHandler

def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hello World!')

def hello(bot, update):
    bot.sendMessage(update.message.chat_id,
                    text='Hello {0}'.format(update.message.from_user.first_name))

updater = Updater('232872196:AAHPm8nWAHIg3xVSst1KBWoli3ihd-Vc5rA')

updater.dispatcher.addHandler(CommandHandler('start', start))
updater.dispatcher.addHandler(CommandHandler('hello', hello))

updater.start_polling()
updater.idle()
