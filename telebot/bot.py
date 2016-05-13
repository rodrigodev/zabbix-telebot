import ConfigParser
import logging
import telegram

from zabbix.zabbix import Zabbix

from telegram.ext import Updater, CommandHandler
from telegram import Emoji, ForceReply, InlineKeyboardButton, \
    InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, \
    CallbackQueryHandler, Filters

# Define the different states a chat can be in
MENU, AWAIT_CONFIRMATION, AWAIT_INPUT = range(3)

# Python 2 and 3 unicode differences
try:
    YES, NO = (Emoji.THUMBS_UP_SIGN.decode('utf-8'),
               Emoji.THUMBS_DOWN_SIGN.decode('utf-8'))
except AttributeError:
    YES, NO = (Emoji.THUMBS_UP_SIGN, Emoji.THUMBS_DOWN_SIGN)

# States are saved in a dict that maps chat_id -> state
state = dict()
# Sometimes you need to save data temporarily
context = dict()
# This dict is used to store the settings value for the chat.
# Usually, you'd use persistence for this (e.g. sqlite).
values = dict()


class TelegramBot(object):

    def __init__(self):
        self.zabb = Zabbix()
        self.__get_config()

        self.__updater = Updater(self.telegram_key)

        self.__updater.dispatcher.addHandler(
            CommandHandler('set', self.set_value))

        self.__updater.dispatcher.addHandler(
            MessageHandler([Filters.text], self.entered_value))

        self.__updater.dispatcher.addHandler(
            CallbackQueryHandler(self.confirm_value))

        self.__updater.dispatcher.addHandler(
            CommandHandler('start', self.help))

        self.__updater.dispatcher.addHandler(
            CommandHandler('help', self.help))

        self.__updater.dispatcher.addHandler(
            CommandHandler('keyboard', self.keyboard))

        self.__updater.dispatcher.addHandler(
            CommandHandler('hello', self.hello))

        self.__updater.dispatcher.addHandler(
            CommandHandler('hostgroups', self.hostgroups))

        self.__updater.dispatcher.addHandler(
            CommandHandler('hosts', self.hosts, pass_args=True))

        self.__updater.dispatcher.addErrorHandler(self.error)

        self.__updater.start_polling()
        self.__updater.idle()

    def __get_config(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('prod.cfg')

        self.telegram_key = self.config.get('TELEGRAM', 'KEY')

    def hello(self, bot, update):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.TYPING)
        bot.sendMessage(update.message.chat_id,
                        text='Hello {0}'
                        .format(update.message.from_user.first_name))

    def hostgroups(self, bot, update):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.TYPING)
        bot.sendMessage(update.message.chat_id,
                        text=self.zabb.get_hostgroups())

    def hosts(self, bot, update, args):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.TYPING)
        for host in self.zabb.get_hosts_by_hostgroup(args):
            bot.sendMessage(update.message.chat_id,
                            text=host)

    # Example handler. Will be called on the /set
    # command and on regular messages
    def set_value(self, bot, update):
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        user_state = state.get(chat_id, MENU)

        if user_state == MENU:
            state[user_id] = AWAIT_INPUT  # set the state
            bot.sendMessage(chat_id,
                            text="Please enter your settings value",
                            reply_markup=ForceReply())

    def entered_value(self, bot, update):
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        chat_state = state.get(user_id, MENU)

        # Check if we are waiting for input
        if chat_state == AWAIT_INPUT:
            state[user_id] = AWAIT_CONFIRMATION

            # Save the user id and the answer to context
            context[user_id] = update.message.text
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton(YES, callback_data=YES),
                  InlineKeyboardButton(NO, callback_data=NO)]])
            bot.sendMessage(chat_id, text="Are you sure?",
                            reply_markup=reply_markup)

    def confirm_value(self, bot, update):
        query = update.callback_query
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        text = query.data
        user_state = state.get(user_id, MENU)
        user_context = context.get(user_id, None)

        # Check if we are waiting for confirmation and the right user answered
        if user_state == AWAIT_CONFIRMATION:
            del state[user_id]
            del context[user_id]
            bot.answerCallbackQuery(query.id, text="Ok!")
            if text == YES:
                values[user_id] = user_context
                bot.editMessageText(
                    text="Changed value to %s." % values[user_id],
                    chat_id=chat_id,
                    message_id=query.message.message_id)
            else:
                bot.editMessageText(text="Alright, value is still %s."
                                         % values.get(user_id, 'not set'),
                                    chat_id=chat_id,
                                    message_id=query.message.message_id)

    def help(self, bot, update):
        bot.sendMessage(update.message.chat_id,
                        text="Use /set to test this bot.")

    def keyboard(self, bot, update):
        custom_keyboard = [[KeyboardButton(Emoji.THUMBS_UP_SIGN),
                            KeyboardButton(Emoji.THUMBS_DOWN_SIGN)]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Stay here, I'll be back.",
                        reply_markup=reply_markup)

    def error(self, bot, update, error):
        logging.warning('Update "%s" caused error "%s"' % (update, error))
