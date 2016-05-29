# -*- coding: utf-8 -*-
import requests
import telebot
import time
import json
import re
from telebot import types
from SQLighter import SQLighter

# TOKEN для вашего бота, нужно запросить у @BotFather
API_TOKEN = ''

# Создание клавиатуры по-умолчанию
key_default = types.ReplyKeyboardMarkup(resize_keyboard=True)
key_default.row(types.KeyboardButton('Добавить страницу ВК 📠'))
key_default.row(types.KeyboardButton('Настройки моих страниц 📻'))
key_default.row(types.KeyboardButton('О боте VK Poster 🤖'))

# Клавиатуры, скрывающая предыдущую
key_hide = types.ReplyKeyboardHide(selective=False)

# Создание списков для хранения временных данных
tmp_data = [{'uid': 0, 'vk_original': '', 'to': 0, 'vk_type': ''}]
counter = []
tmp_id = 0

# Создание бота
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def command_start(message):
	UID = message.chat.id # В UID каждый раз записывается ID пользователя Telegram

    bot.send_message(UID, 'Привет! Я бот, который умеет отправлять записи из *групп и пабликов ' \
    'ВКонтакте тебе*, а также *в твои публичные каналы* Telegram.\n\nЧтобы начать, нажми ' \
    '*Добавить страницу ВК*.', parse_mode='Markdown', reply_markup=key_default)

@bot.message_handler(func=lambda message: message.text == u'Добавить страницу ВК 📠')
def add_page_url(message):
    global tmp_data
    UID = message.chat.id
    tmp_data[0]['uid'] = UID

    msg = bot.send_message(UID, 'Чтобы добавить новую страницу, с которой нужно отправлять записи, ' \
        'отправь мне её адрес (например: *vk.com/mzk*):', parse_mode='Markdown', reply_markup=key_hide)
    bot.register_next_step_handler(msg, add_page_to)

def add_page_to(message):
    global tmp_data
    UTXT = message.text

    if bool(re.search('(m.|new.|)(?i)vk.com', UTXT)):
        if bool(re.search('(m.|new.|)(?i)vk.com\/(public|club)', UTXT)):
            tmp_data[0]['vk'] = re.sub('(\Ahttp\S?:\/\/|)(m.|new.|)(?i)vk.com\/(club|public)', '', UTXT)
            tmp_data[0]['vk_type'] = 'ID'
            api = 'https://api.vk.com/method/wall.get?owner_id=-%s&count=10&filter=owner' % \
            (tmp_data[0]['vk'])
        else:
            tmp_data[0]['vk'] = re.sub('(\Ahttp\S?:\/\/|)(m.|new.|)(?i)vk.com\/', '', UTXT)
            tmp_data[0]['vk_type'] = 'DOMAIN'
            api = 'https://api.vk.com/method/wall.get?domain=%s&count=10&filter=owner' % ((tmp_data[0]['vk']))
        tmp_data[0]['vk_original'] = UTXT.lower()

        try:
            items = requests.get(api).json()
            try:
                tmp = items['response'][1]['is_pinned']
                tmp_data[0]['last_id'] = items['response'][3]['id']
            except:
                tmp_data[0]['last_id'] = items['response'][2]['id']

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.row(types.KeyboardButton('В диалог с ботом'))
            keyboard.row(types.KeyboardButton('В публичный канал'))

            msg = bot.reply_to(message, 'Хорошо. Куда нужно присылать новые записи с этой страницы?',
            reply_markup=keyboard)
            bot.register_next_step_handler(msg, add_page_to_type)
        except:
            msg = bot.reply_to(message, 'Видимо, ты прислал мне не ссылку *на группу или публичную страницу* ' \
            'ВКонтакте. Попробуй ещё раз.', parse_mode='Markdown')
            bot.register_next_step_handler(msg, add_page_to)
    else:
        msg = bot.reply_to(message, 'Видимо, ты прислал мне не ссылку *на группу или публичную страницу* ' \
            'ВКонтакте. Попробуй ещё раз.', parse_mode='Markdown')
        bot.register_next_step_handler(msg, add_page_to)

def add_page_to_type(message):
    global tmp_data
    UID = message.chat.id
    UTXT = message.text

    if UTXT == u'В диалог с ботом':
        tmp_data[0]['to'] = 0
        tmp_data[0]['channel'] = UID
        db = SQLighter()
        db.insert(tmp_data[0]['uid'], tmp_data[0]['vk'], tmp_data[0]['vk_original'], tmp_data[0]['vk_type'], 
            tmp_data[0]['last_id'], tmp_data[0]['to'], tmp_data[0]['to'], 0, 1)
        db.close()
        msg = bot.send_message(UID, 'Я буду присылать новые записи с указанной страницы в этот диалог ' \
            '(с ботом *VK Poster*).\n\nЧтобы включить отправку репостов из других групп, а также настроить ' \
            'отправку вложений (фотографий, аудио и т. д.) перейди в *Настройки моих страниц*.' \
            '\n\nЧто будем делать дальше?', parse_mode='Markdown', reply_markup=key_default)
    elif UTXT == u'В публичный канал':
        msg = bot.send_message(UID, 'Чтобы бот смог отправлять записи в публичный канал, нужно сделать бота ' \
            '*VK Poster* администратором канала.\n\nКогда администратор добавлен, отправь мне логин ' \
            'канала (например: *@durov*):', parse_mode='Markdown', reply_markup=key_hide)
        bot.register_next_step_handler(msg, add_page_channel)
    else:
        msg = bot.reply_to(message, 'Похоже, ты не ответил на вопрос. Куда присылать новые записи?')
        bot.register_next_step_handler(msg, add_page_to_type)

def add_page_channel(message):
    global tmp_data
    UID = message.chat.id
    UTXT = message.text

    if '@' in UTXT:
        tmp_data[0]['to'] = 1
        tmp_data[0]['channel'] = UTXT
        db = SQLighter()
        db.insert(tmp_data[0]['uid'], tmp_data[0]['vk'], tmp_data[0]['vk_original'], tmp_data[0]['vk_type'], 
            tmp_data[0]['last_id'], tmp_data[0]['to'], tmp_data[0]['channel'], 0, 1)
        db.close()
        msg = bot.send_message(UID, 'Я буду присылать новые записи с указанной страницы в канал ' \
            '%s.\n\nЧтобы включить отправку репостов из других групп, а также настроить ' \
            'отправку вложений (фотографий, аудио и т. д.) перейди в *Настройки моих страниц*.' \
            '\n\nЧто будем делать дальше?' % (UTXT.encode('utf-8')), 
            parse_mode='Markdown', reply_markup=key_default)
    else:
        msg = bot.reply_to(message, 'Похоже, ты не прислал логин канала (начинается с *@*). ' \
            'Попробуй ещё раз.', parse_mode='Markdown')
        bot.register_next_step_handler(msg, add_page_channel)

@bot.message_handler(func=lambda message: message.text == u'Настройки моих страниц 📻')
def settings_choose(message):
    global counter
    UID = message.chat.id
    UTXT = message.text
    
    db = SQLighter()
    if len(db.select_all_by_uid(UID)) > 0:
        msg = bot.send_message(UID, 'Выбери страницу', parse_mode='Markdown')
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        result = db.select_all_by_uid(UID)
        counter = ['NULL']
        for item in result:
            counter.append({'id':item[0]})
            if item[5] == 0:
                bot.send_message(UID, '*#%s* ∙ Из *%s* в *чат с ботом*' % (str(len(counter) - 1), 
                    item[3].encode('utf-8')), parse_mode='Markdown')
                keyboard.add(types.KeyboardButton('#%s' % (str(len(counter) - 1))))
            else:
                bot.send_message(UID, '*#%s* ∙ Из *%s* в *канал %s*' % (str(len(counter) - 1), 
                    item[3].encode('utf-8'), item[6].encode('utf-8')), parse_mode='Markdown')
                keyboard.add(types.KeyboardButton('#%s' % (str(len(counter) - 1))))
        keyboard.add(types.KeyboardButton('Вернуться в меню'))
        bot.send_message(UID, 'Нажми на номер страницы, которую хочешь изменить или удалить.', 
            parse_mode='Markdown', reply_markup=keyboard)

        bot.register_next_step_handler(msg, settings_page)
    else:
        msg = bot.send_message(UID, 'Похоже, ты не добавил ещё ни одной страницы.', 
            parse_mode='Markdown', reply_markup=key_default)
    db.close()

def settings_page(message):
    global counter
    global tmp_id
    UID = message.chat.id
    UTXT = message.text

    if UTXT == u'Вернуться в меню':
        bot.send_message(UID, 'Что делаем дальше?', reply_markup=key_default)
    elif '#' in UTXT:
        UTXT = int(re.sub('#', '', UTXT))
        if UTXT < len(counter):
            row_id = counter[UTXT]['id']
            tmp_id = row_id
            db = SQLighter()
            result = db.select_all_by_id(row_id)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            if result[0][7] == 0:
                keyboard.row(types.KeyboardButton('Включить репосты'))
            else:
                keyboard.row(types.KeyboardButton('Отключить репосты'))
            if result[0][8] == 0:
                keyboard.row(types.KeyboardButton('Включить вложения'))
            else:
                keyboard.row(types.KeyboardButton('Отключить вложения'))
            if result[0][10] == 0:
                keyboard.row(types.KeyboardButton('Включить уведомления'))
            else:
                keyboard.row(types.KeyboardButton('Отключить уведомления'))
            db.close()
            
            keyboard.row(types.KeyboardButton('Удалить страницу'))
            keyboard.row(types.KeyboardButton('Вернуться в меню'))
            bot.send_message(UID, 'Что ты хочешь изменить?', reply_markup=keyboard)

            bot.register_next_step_handler(message, settings_page_doing)

def settings_page_doing(message):
    global counter
    global tmp_id
    UID = message.chat.id
    UTXT = message.text

    if UTXT == u'Удалить страницу':
        db = SQLighter()
        db.delete_by_id(tmp_id)
        db.close
        bot.send_message(UID, 'Страница была удалена 😵\nЧто делаем дальше?', reply_markup=key_default)
        counter = []
        tmp_id = 0
    if UTXT == u'Включить репосты':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.reposts_update(tmp_id, 1)
        result = db.select_all_by_id(tmp_id)
        db.close
        keyboard.row(types.KeyboardButton('Отключить репосты'))
        if result[0][8] == 0:
            keyboard.row(types.KeyboardButton('Включить вложения'))
        else:
            keyboard.row(types.KeyboardButton('Отключить вложения'))
        if result[0][10] == 0:
            keyboard.row(types.KeyboardButton('Включить уведомления'))
        else:
            keyboard.row(types.KeyboardButton('Отключить уведомления'))
        keyboard.row(types.KeyboardButton('Удалить страницу'))
        keyboard.row(types.KeyboardButton('Вернуться в меню'))
        bot.send_message(UID, 'Репосты для данной страницы были включены.', 
            reply_markup=keyboard)

        bot.register_next_step_handler(message, settings_page_doing)
    if UTXT == u'Отключить репосты':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.reposts_update(tmp_id, 0)
        result = db.select_all_by_id(tmp_id)
        db.close
        keyboard.row(types.KeyboardButton('Включить репосты'))
        if result[0][8] == 0:
            keyboard.row(types.KeyboardButton('Включить вложения'))
        else:
            keyboard.row(types.KeyboardButton('Отключить вложения'))
        if result[0][10] == 0:
            keyboard.row(types.KeyboardButton('Включить уведомления'))
        else:
            keyboard.row(types.KeyboardButton('Отключить уведомления'))
        keyboard.row(types.KeyboardButton('Удалить страницу'))
        keyboard.row(types.KeyboardButton('Вернуться в меню'))
        bot.send_message(UID, 'Репосты для данной страницы были отключены.', 
            reply_markup=keyboard)

        bot.register_next_step_handler(message, settings_page_doing)
    if UTXT == u'Отключить вложения':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.attachments_update(tmp_id, 0)
        result = db.select_all_by_id(tmp_id)
        db.close
        if result[0][7] == 0:
            keyboard.row(types.KeyboardButton('Включить репосты'))
        else:
            keyboard.row(types.KeyboardButton('Отключить репосты'))
        if result[0][10] == 0:
            keyboard.row(types.KeyboardButton('Включить уведомления'))
        else:
            keyboard.row(types.KeyboardButton('Отключить уведомления'))
        keyboard.row(types.KeyboardButton('Включить вложения'))
        keyboard.row(types.KeyboardButton('Удалить страницу'))
        keyboard.row(types.KeyboardButton('Вернуться в меню'))
        bot.send_message(UID, 'Вложения для данной страницы были отключены.', 
            reply_markup=keyboard)

        bot.register_next_step_handler(message, settings_page_doing)
    if UTXT == u'Включить вложения':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.attachments_update(tmp_id, 1)
        result = db.select_all_by_id(tmp_id)
        db.close
        if result[0][7] == 0:
            keyboard.row(types.KeyboardButton('Включить репосты'))
        else:
            keyboard.row(types.KeyboardButton('Отключить репосты'))
        if result[0][10] == 0:
            keyboard.row(types.KeyboardButton('Включить уведомления'))
        else:
            keyboard.row(types.KeyboardButton('Отключить уведомления'))
        keyboard.row(types.KeyboardButton('Отключить вложения'))
        keyboard.row(types.KeyboardButton('Удалить страницу'))
        keyboard.row(types.KeyboardButton('Вернуться в меню'))
        bot.send_message(UID, 'Вложения для данной страницы были включены.', 
            reply_markup=keyboard)

        bot.register_next_step_handler(message, settings_page_doing)
    if UTXT == u'Отключить уведомления':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.notify_update(tmp_id, 0)
        result = db.select_all_by_id(tmp_id)
        db.close
        if result[0][7] == 0:
            keyboard.row(types.KeyboardButton('Включить репосты'))
        else:
            keyboard.row(types.KeyboardButton('Отключить репосты'))
        if result[0][8] == 0:
            keyboard.row(types.KeyboardButton('Включить вложения'))
        else:
            keyboard.row(types.KeyboardButton('Отключить вложения'))
        keyboard.row(types.KeyboardButton('Включить уведомления'))
        keyboard.row(types.KeyboardButton('Удалить страницу'))
        keyboard.row(types.KeyboardButton('Вернуться в меню'))
        bot.send_message(UID, 'Уведомления для данной страницы были отключены.', 
            reply_markup=keyboard)

        bot.register_next_step_handler(message, settings_page_doing)
    if UTXT == u'Включить уведомления':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.notify_update(tmp_id, 1)
        result = db.select_all_by_id(tmp_id)
        db.close
        if result[0][7] == 0:
            keyboard.row(types.KeyboardButton('Включить репосты'))
        else:
            keyboard.row(types.KeyboardButton('Отключить репосты'))
        if result[0][8] == 0:
            keyboard.row(types.KeyboardButton('Включить вложения'))
        else:
            keyboard.row(types.KeyboardButton('Отключить вложения'))
        keyboard.row(types.KeyboardButton('Отключить уведомления'))
        keyboard.row(types.KeyboardButton('Удалить страницу'))
        keyboard.row(types.KeyboardButton('Вернуться в меню'))
        bot.send_message(UID, 'Уведомления для данной страницы были включены.', 
            reply_markup=keyboard)

        bot.register_next_step_handler(message, settings_page_doing)
    if UTXT == u'Вернуться в меню':
        bot.send_message(UID, 'Что делаем дальше?', reply_markup=key_default)

@bot.message_handler(func=lambda message: message.text == u'Открыть меню')
def open_menu(message):
	"""
	Функция, открывающая главное меню
	"""
    UID = message.chat.id

    bot.send_message(UID, 'Что будем делать?', reply_markup=key_default)

@bot.message_handler(func=lambda message: message.text == u'О боте VK Poster 🤖')
def command_about(message):
	"""
	Функция, выводящая информацию о боте
	"""
    UID = message.chat.id

    bot.send_message(UID, 'Бот *VK Poster* может автоматически присылать новые записи из групп ' \
        'и публичных страниц ВКонтакте непосредственно в диалог с ботом, либо в указанный тобою ' \
        'канал Telegram.\n\n*VK Poster* написан на Python 2.7 и использует открытые методы API ' \
        'ВКонтакте.\n\nИсходный код бота доступен на GitHub: git.io/vrH5I\n' \
        'Создатель бота: @kozak', parse_mode='Markdown', reply_markup=key_default, 
        disable_web_page_preview=True)

# bot.polling(), чтобы бот продолжал работу и не выключался
bot.polling()