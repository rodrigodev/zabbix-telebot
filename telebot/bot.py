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
MENU, AWAIT_HOST, AWAIT_HOSTGROUP, AWAIT_ALERTS = range(4)

# States are saved in a dict that maps chat_id -> state
state = dict()
# Sometimes you need to save data temporarily
context = dict()
# This dict is used to store the settings value for the chat.
# Usually, you'd use persistence for this (e.g. sqlite).
values = dict()


def chat_action(func):
    def print_chat_action(self, bot, update):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.TYPING)

        return func(self, bot, update)

    return print_chat_action


def chat_action_args(func):
    def print_chat_action(self, bot, update, args):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.TYPING)

        return func(self, bot, update, args)

    return print_chat_action


class TelegramBot(object):

    def __init__(self):
        self.zabb = Zabbix()
        self.__get_config()

        self.__updater = Updater(self.telegram_key)

        self.__updater.dispatcher.addHandler(
            CallbackQueryHandler(self.confirm_value))

        # main functions

        self.__updater.dispatcher.addHandler(
            CommandHandler('start', self.keyboard))

        self.__updater.dispatcher.addHandler(
            CommandHandler('help', self.help))

        self.__updater.dispatcher.addHandler(
            CommandHandler('hostgroups', self.hostgroups_click))

        self.__updater.dispatcher.addHandler(
            CommandHandler('slachat', self.sla))

        self.__updater.dispatcher.addHandler(
            CommandHandler('triggers', self.active_triggers_click))

        self.__updater.dispatcher.addErrorHandler(self.error)

        self.__updater.start_polling()
        self.__updater.idle()

    def __get_config(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('prod.cfg')

        self.telegram_key = self.config.get('TELEGRAM', 'KEY')

    def __get_active_triggers_by_hostgroup(self, hostgroup_name):
        return self.zabb.get_active_triggers_by_hostgroup(hostgroup_name)

    @chat_action_args
    def hosts(self, bot, update, args):
        hostgroup_name = [hostgroup['name']
                          for hostgroup in self.zabb.get_hostgroups()
                          if hostgroup['groupid'] == args][0]

        head_text = '//hostgroups/hosts\nHostgroup: {}\n\n'.format(
            hostgroup_name)

        hosts_list = sorted(['{}'.format(host['name'])
                             for host
                             in self.zabb.get_hosts_by_hostgroup([args])])

        result = '{}{}'.format(head_text, '\n'.join(hosts_list))

        bot.sendMessage(update.message.chat_id, text=result)

    @chat_action_args
    def hostgroups_active_triggers(self, bot, update, args):
        result = '//active_triggers\nHostgroup: {}\n\n'.format(args)

        triggers_by_host_list = {}
        for trigger in self.zabb.get_active_triggers_by_hostgroup(args):
            host = trigger['hosts'][0]['host']

            if(host not in triggers_by_host_list.keys()):
                triggers_by_host_list[host] = []

            triggers_by_host_list[host].append(
                trigger['description'].encode('utf-8'))

        for host in sorted(triggers_by_host_list.keys()):
            result += 'Host: {}\n\n'.format(host)

            for trigger in triggers_by_host_list[host]:
                result += '- {}\n'.format(trigger)

            result += '\n\n'

        bot.sendMessage(update.message.chat_id, text=result)

    def confirm_value(self, bot, update):
        query = update.callback_query
        update.message = query.message
        user_state = state.get(query.from_user.id, MENU)

        if user_state == AWAIT_HOSTGROUP:
            self.hosts(bot, update, query.data)
        elif user_state == AWAIT_ALERTS:
            self.hostgroups_active_triggers(bot, update, query.data)

        bot.answerCallbackQuery(query.id)

    # keyboard button calls

    def sla(self, bot, update):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.TYPING)
        bot.sendMessage(update.message.chat_id,
                        text=self.zabb.get_slachat())

    @chat_action
    def hostgroups_click(self, bot, update):
        user_id = update.message.from_user.id
        state[user_id] = AWAIT_HOSTGROUP
        buttons = []

        for item in self.zabb.get_hostgroups():
            buttons.append([InlineKeyboardButton(
                text=item["name"],
                callback_data=item["groupid"]
            )])

        reply_markup = InlineKeyboardMarkup(buttons)

        bot.sendMessage(update.message.chat_id,
                        text="getting information",
                        reply_markup=reply_markup)

    @chat_action
    def active_triggers_click(self, bot, update):
        user_id = update.message.from_user.id
        state[user_id] = AWAIT_ALERTS
        buttons = []

        for item in self.zabb.get_hostgroups():
            errors = len(self.__get_active_triggers_by_hostgroup(item["name"]))
            if errors:
                buttons.append([InlineKeyboardButton(
                    text="{} ({})".format(item["name"], errors),
                    callback_data=item["name"]
                )])

        reply_markup = InlineKeyboardMarkup(buttons)

        bot.sendMessage(update.message.chat_id,
                        text="getting information",
                        reply_markup=reply_markup)

    # support commands

    def help(self, bot, update):
        bot.sendMessage(update.message.chat_id,
                        text="Use /set to test this bot.")

    def keyboard(self, bot, update):
        custom_keyboard = [[
            KeyboardButton("/start"),
            KeyboardButton("/triggers"),
            KeyboardButton("/hostgroups")
        ]]
        reply_markup = ReplyKeyboardMarkup(
            custom_keyboard, resize_keyboard=True)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Teclado de comandos ativado!",
                        reply_markup=reply_markup)

    def error(self, bot, update, error):
        logging.warning('Update "%s" caused error "%s"' % (update, error))
