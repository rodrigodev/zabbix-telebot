import configparser
import logging
import telegram
import subprocess
import os

from zabbix.zabbix import Zabbix
from telegram.ext import Updater, CommandHandler
from telegram import ForceReply, InlineKeyboardButton, \
    InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, \
    CallbackQueryHandler, Filters

# Define the different states a chat can be in
MENU, AWAIT_HOST, AWAIT_HOSTGROUP, AWAIT_ALERTS, AWAIT_ACKNOWLEDGE, AWAIT_ACKNOWLEDGE_CONFIRMATION = range(6)

# Python 2 and 3 unicode differences
YES = "Yes"
NO = "No"
# States are saved in a dict that maps chat_id -> state
state = dict()
# Sometimes you need to save data temporarily
context = dict()
# This dict is used to store the settings value for the chat.
# Usually, you'd use persistence for this (e.g. sqlite).
values = dict()

event_keys = dict()


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

        self.__updater.dispatcher.addHandler(
            MessageHandler([Filters.text], self.entered_value))

        # main functions

        self.__updater.dispatcher.addHandler(
            CommandHandler('start', self.keyboard))

        self.__updater.dispatcher.addHandler(
            CommandHandler('help', self.help))

        self.__updater.dispatcher.addHandler(
            CommandHandler('graph', self.graph))

        self.__updater.dispatcher.addHandler(
            CommandHandler('hostgroups', self.hostgroups_click))

        self.__updater.dispatcher.addHandler(
            CommandHandler('sla', self.sla))

        self.__updater.dispatcher.addHandler(
            CommandHandler('triggers', self.active_triggers_click))

        self.__updater.dispatcher.addHandler(
            CommandHandler('acknowledge', self.acknowledge_click))

        self.__updater.dispatcher.addErrorHandler(self.error)

        self.__updater.start_polling()
        self.__updater.idle()

    def __get_config(self):
        self.config = configparser.ConfigParser()
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

        bot.sendMessage(update.message.chat_id, text=result,
                        disable_web_page_preview=True)

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

        bot.sendMessage(update.message.chat_id, text=result,
                        disable_web_page_preview=True)

    @chat_action_args
    def acknowledge_event(self, bot, update, args):
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id

        state[user_id] = AWAIT_ACKNOWLEDGE  # set the state
        bot.sendMessage(chat_id,
                        text="Please write the acknowledge message:",
                        reply_markup=ForceReply())

    def acknowledge_confirmation(self, bot, update):
        query = update.callback_query
        user_id = query.from_user.id
        text = query.data
        user_context = context.get(user_id, None)
        event_key = event_keys.get(user_id, None)
        user_state = state.get(query.from_user.id, MENU)

        if user_state == AWAIT_ACKNOWLEDGE_CONFIRMATION:
            del state[user_id]
            del context[user_id]
            if event_keys[user_id]:
                del event_keys[user_id]

            if text == YES:
                values[user_id] = user_context

                self.zabb.set_acknowledge(event_key, values[user_id])

                bot.answerCallbackQuery(query.id, text="Acknowledge done!")
            else:
                bot.answerCallbackQuery(query.id, text="Acknowledge aborted!")

    def confirm_value(self, bot, update):
        query = update.callback_query
        update.message = query.message
        user_id = query.from_user.id
        user_state = state.get(query.from_user.id, MENU)

        if user_state == AWAIT_HOSTGROUP:
            self.hosts(bot, update, query.data)
        elif user_state == AWAIT_ALERTS:
            self.hostgroups_active_triggers(bot, update, query.data)
        elif user_state == AWAIT_ACKNOWLEDGE:
            event_keys[user_id] = query.data
            self.acknowledge_event(bot, update, query.data)
        elif user_state == AWAIT_ACKNOWLEDGE_CONFIRMATION:
            self.acknowledge_confirmation(bot, update)

        bot.answerCallbackQuery(query.id)

    def entered_value(self, bot, update):
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        chat_state = state.get(user_id, MENU)

        if chat_state == AWAIT_ACKNOWLEDGE:
            state[user_id] = AWAIT_ACKNOWLEDGE_CONFIRMATION

            # Save the user id and the answer to context
            context[user_id] = update.message.text
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton(YES, callback_data=YES),
                  InlineKeyboardButton(NO, callback_data=NO)]])
            bot.sendMessage(chat_id, text="Are you sure?",
                            reply_markup=reply_markup)

    # keyboard button calls

    def sla(self, bot, update):
        bot.sendMessage(update.message.chat_id,
                        text=self.zabb.get_sla(),
                        disable_web_page_preview=True)

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
                        reply_markup=reply_markup,
                        disable_web_page_preview=True)

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
                        reply_markup=reply_markup,
                        disable_web_page_preview=True)

    @chat_action
    def acknowledge_click(self, bot, update):
        user_id = update.message.from_user.id
        state[user_id] = AWAIT_ACKNOWLEDGE

        for event in self.zabb.get_events():
            prompt = "Host: {}\nEvento: {}".format(event['hosts'][0]['name'],
                                                   event['description'])

            bot.sendMessage(update.message.chat_id, text=prompt)

            buttons = [[InlineKeyboardButton(
                text="acknowledge",
                callback_data=event['lastEvent']['eventid'])]]

            reply_markup = InlineKeyboardMarkup(buttons)

            bot.sendMessage(update.message.chat_id,
                            text='Press to acknowledge it.',
                            reply_markup=reply_markup,
                            disable_web_page_preview=True)

    # support commands

    def help(self, bot, update):
        bot.sendMessage(update.message.chat_id,
                        text="Use /set to test this bot.")

    def keyboard(self, bot, update):
        custom_keyboard = [[
            KeyboardButton("/sla"),
            KeyboardButton("/acknowledge"),
            KeyboardButton("/triggers"),
            KeyboardButton("/hostgroups"),
            KeyboardButton("/graph")
        ]]
        reply_markup = ReplyKeyboardMarkup(
            custom_keyboard, resize_keyboard=True)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Teclado de comandos ativado!",
                        reply_markup=reply_markup,
                        disable_web_page_preview=True)

    def graph(self, bot, update):
        bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
        os.system("rm /tmp/zabbix_graph.png")
        os.system("php -f ./gimg.php")
        bot.sendPhoto(chat_id=update.message.chat_id, photo=open('/tmp/zabbix_graph.png','rb'))

    def error(self, bot, update, error):
        logging.warning('Update "%s" caused error "%s"' % (update, error))
