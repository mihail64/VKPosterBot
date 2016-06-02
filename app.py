# -*- coding: utf-8 -*-
import telebot
import io, re, os, time
from telebot import types
from SQLighter import SQLighter
import botan, requests, json, logging

os.environ['TZ'] = 'Europe/Moscow'
time.tzset() # Настройка времени на сервере

# Настройка соединения с Telegram и Botan
BOTAN_TOKEN = ''
API_TOKEN = ''

# Создание клавиатуры по-умолчанию
key_default = types.ReplyKeyboardMarkup(resize_keyboard=True)
key_default.row(types.KeyboardButton('Добавить страницу ВК 📠'))
key_default.row(types.KeyboardButton('Настройки моих страниц 🚀'))
key_default.row(types.KeyboardButton('О боте VK Poster 🤖'))

key_hide = types.ReplyKeyboardHide(selective=False)
key_force = types.ForceReply(selective=False)

# Настройка логгера, сохраняющего все входящие сообщения
logging.getLogger('requests').setLevel(logging.CRITICAL)
logging.basicConfig(format='[%(asctime)s]%(message)s', 
    level=logging.INFO, filename='app.log', datefmt='%d.%m.%Y %H:%M:%S')

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.

def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            logging.info("[" + str(m.chat.id) + "]: " + m.text)

bot = telebot.TeleBot(API_TOKEN)
bot.set_update_listener(listener)

def keyboard_setup(result):
    # Создание клавиатуры для настройки одной страницы
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if result[0][10] == 0:
        keyboard.row(types.KeyboardButton('Включить уведомления 🔔'))
    else:
        keyboard.row(types.KeyboardButton('Отключить уведомления 🔕'))
    if result[0][7] == 0:
        keyboard.row(types.KeyboardButton('Включить репосты 📝'))
    else:
        keyboard.row(types.KeyboardButton('Отключить репосты 📝'))
    if result[0][8] == 0:
        keyboard.row(types.KeyboardButton('Включить вложения 📎'))
    else:
        keyboard.row(types.KeyboardButton('Отключить вложения 📎'))
    if result[0][12] == 0:
        keyboard.row(types.KeyboardButton('Включить записи участников 🗣'))
    else:
        keyboard.row(types.KeyboardButton('Отключить записи участников 🗣'))
    if result[0][11] == 0:
        keyboard.row(types.KeyboardButton('Показывать название страницы 👁'))
    else:
        keyboard.row(types.KeyboardButton('Скрыть название страницы 👁'))
    keyboard.row(types.KeyboardButton('Удалить страницу ❌'))
    keyboard.row(types.KeyboardButton('⬅️ Вернуться в меню'))
    return keyboard

@bot.message_handler(commands=['start'])
def command_start(message):
    UID = message.chat.id

    bot.send_message(UID, 'Привет! Я бот, который умеет отправлять записи из *групп и пабликов ' \
        'ВКонтакте тебе*, а также *в твои публичные каналы* Telegram.\n\nЧтобы начать, нажми ' \
        '*Добавить страницу ВК* или на команду /add', parse_mode='Markdown', reply_markup=key_default)
    botan.track(BOTAN_TOKEN, message.chat.id, message, 'Запуск бота (start)')

@bot.message_handler(func=lambda message: message.text == u'Добавить страницу ВК 📠')
@bot.message_handler(commands=['add'])
def add_page_url(message):
    UID = message.chat.id
    
    msg = bot.send_message(UID, 'Чтобы добавить новую страницу, с которой нужно отправлять записи, ' \
        'отправь мне её адрес (например: *vk.com/mzk*):', parse_mode='Markdown', reply_markup=key_hide)
    botan.track(BOTAN_TOKEN, message.chat.id, message, 'Запрос на добавление страницы (add)')
    
    with io.open(str(UID) + '.UID', 'w', encoding='utf-8') as file:
        # Создание временного файла .UID для хранения информации о новой странице
        file.write(unicode(json.dumps({'uid': UID, 'vk' : '', 'vk_original' : '', 'vk_type' : '', \
            'channel' : '', 'type' : '', 'last_id' : '', 'to' : ''}, ensure_ascii=False)))
    bot.register_next_step_handler(msg, add_page_to)

def add_page_to(message):
    UID = message.chat.id
    UTXT = message.text
    
    if UTXT == u'/cancel':
        bot.send_message(UID, 'Хорошо, возвращаю тебя на главную.', reply_markup=key_default)
    elif bool(re.search('(m.|new.|)(?i)vk.com', UTXT)) and \
    bool(re.search('(m.|new.|)(?i)vk.com\/id\d+', UTXT)) == False:
        # Если в адресе обнаружен vk.com, открываем временный файл .UID и заполняем данными
        with open(str(UID) + '.UID', 'r') as file:
            data = json.load(file)

        if bool(re.search('(m.|new.|)(?i)vk.com\/(public|club)', UTXT)):
            data['vk'] = re.sub('(\Ahttp\S?:\/\/|)(m.|new.|)(?i)vk.com\/(club|public)', '', UTXT)
            data['vk_type'] = 'ID'
            api = 'https://api.vk.com/method/wall.get?owner_id=-%s&count=10&filter=owner' % (data['vk'])
        else:
            data['vk'] = re.sub('(\Ahttp\S?:\/\/|)(m.|new.|)(?i)vk.com\/', '', UTXT)
            data['vk_type'] = 'DOMAIN'
            api = 'https://api.vk.com/method/wall.get?domain=%s&count=10&filter=owner' % (data['vk'])
        data['vk_original'] = UTXT.lower()

        try:
            # Попытка получить данные от vk.com
            items = requests.get(api).json()
            try:
                tmp = items['response'][1]['is_pinned']
                data['last_id'] = items['response'][3]['id']
            except:
                data['last_id'] = items['response'][2]['id']

            with io.open(str(UID) + '.UID', 'w', encoding='utf-8') as file:
                # Если всё прошло успешно, записываем данные в .UID
                file.write(unicode(json.dumps(data)))

            key_choose = types.ReplyKeyboardMarkup(resize_keyboard=True)
            key_choose.row(types.KeyboardButton('В диалог с ботом 👤'))
            key_choose.row(types.KeyboardButton('В публичный канал 👥'))

            msg = bot.reply_to(message, 'Хорошо. Куда нужно присылать новые записи с этой страницы?',
                reply_markup=key_choose)
            bot.register_next_step_handler(msg, add_page_to_type)
        except Exception as ex:
            msg = bot.reply_to(message, 'Видимо, ты прислал мне не ссылку *на группу или публичную' \
            ' страницу* ВКонтакте. Попробуй ещё раз.', parse_mode='Markdown')
            bot.register_next_step_handler(msg, add_page_to)
    elif bool(re.search('(m.|new.|)(?i)vk.com\/id\d+', UTXT)):
        msg = bot.reply_to(message, 'Бот умеет отправлять записи только из *групп и публичных страниц*, ' \
            'страницы пользователей (начинаются с *id...*) сейчас не поддерживаются.\nПопробуй прислать ' \
            'другую группу или публичную страницу.', parse_mode='Markdown')
        bot.register_next_step_handler(msg, add_page_to)
    else:
        msg = bot.reply_to(message, 'Видимо, ты прислал мне не ссылку *на группу или публичную страницу* ' \
            'ВКонтакте. Попробуй ещё раз.', parse_mode='Markdown')
        bot.register_next_step_handler(msg, add_page_to)

def add_page_to_type(message):
    UID = message.chat.id
    UTXT = message.text
    
    if UTXT == u'/cancel':
        bot.send_message(UID, 'Хорошо, возвращаю тебя на главную.', reply_markup=key_default)
    elif UTXT == u'В диалог с ботом 👤':
        with open(str(UID) + '.UID', 'r') as file:
            # Открываем временный .UID для чтения
            data = json.load(file)
        
        data['to'] = 0
        data['channel'] = UID
        db = SQLighter()
        # Выполняем запрос в БД, если пользователь выбрал 'В чат с ботом'
        db.insert(data['uid'], data['vk'], data['vk_original'], data['vk_type'], 
            int(data['last_id']), 0, 0, 0, 1)
        db.close()

        msg = bot.send_message(UID, 'Я буду присылать новые записи с указанной страницы в этот диалог ' \
            '(с ботом *VK Poster*).\n\nЧтобы включить отправку репостов из других групп, а также настроить ' \
            'отправку вложений (фотографий, аудио и т. д.) перейди в *Настройки моих страниц*.' \
            '\n\nЧто будем делать дальше?', parse_mode='Markdown', reply_markup=key_default)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Добавление страницы (в чат с ботом)')
    elif UTXT == u'В публичный канал 👥':
        msg = bot.send_message(UID, 'Чтобы бот смог отправлять записи в публичный канал, нужно сделать бота ' \
            '*VK Poster* администратором канала.\n\nКогда администратор добавлен, отправь мне логин ' \
            'канала (например: *@durov*):', parse_mode='Markdown', reply_markup=key_hide)
        bot.register_next_step_handler(msg, add_page_channel)
    else:
        msg = bot.reply_to(message, 'Похоже, ты не ответил на вопрос. Куда присылать новые записи?')
        bot.register_next_step_handler(msg, add_page_to_type)

def add_page_channel(message):
    UID = message.chat.id
    UTXT = message.text
    accept = True
    
    if UTXT == u'/cancel':
        bot.send_message(UID, 'Хорошо, возвращаю тебя на главную.', reply_markup=key_default)
    elif bool(re.search('^@\S+\Z', UTXT)):
        db = SQLighter()
        check = db.select_by_chn(UTXT)
        db.close()
        if len(check) > 0:
            if int(check[0][1]) != int(UID):
                # Проверяем, есть ли уже такой канал в базе, и если есть,
                # то сверяем ID текущего пользователя и ID пользователя из базы
                # во избежание получения доступа к чужому каналу Telegram, в
                # котором бот уже является администратором
                msg = bot.reply_to(message, 'Хмм, похоже, что кто-то другой уже использует данный канал.\n' \
                    'Чтобы добавить страницу VK для данного канала, используй аккаунт Telegram, с которого ' \
                    'добавлял первую страницу.\n\nПопробуй прислать другой логин канала (начинается с ' \
                    '*@*) или нажми /cancel для отмены.', reply_markup=key_hide, parse_mode='Markdown')
                accept = False
                bot.register_next_step_handler(msg, add_page_channel)
        if accept:
            try:
                if len(check) < 1:
                    bot.send_message(UTXT, 'Бот *VK Poster* (@VKPstBot) теперь будет отправлять ' \
                        'записи в этот канал.', parse_mode='Markdown')

                with open(str(UID) + '.UID', 'r') as file:
                    # Открываем временный .UID для чтения
                    data = json.load(file)

                data['to'] = 1
                data['channel'] = UTXT

                db = SQLighter()
                # Выполняем запрос в БД, если пользователь выбрал 'В публичный канал'
                db.insert(data['uid'], data['vk'], data['vk_original'], 
                    data['vk_type'], int(data['last_id']), int(data['to']), 
                    data['channel'], 0, 1)
                db.close()

                UTXT = re.sub('_', '\_', UTXT)
                msg = bot.send_message(UID, 'Я буду присылать новые записи с указанной страницы в канал ' \
                    '%s.\n\nЧтобы включить отправку репостов из других групп, а также настроить ' \
                    'отправку вложений (фотографий, аудио и т. д.) перейди в *Настройки моих страниц*.' \
                    '\n\nЧто будем делать дальше?' % (UTXT.encode('utf-8')), 
                    parse_mode='Markdown', reply_markup=key_default)
                botan.track(BOTAN_TOKEN, message.chat.id, message, 'Добавление страницы (в публичный канал)')
            except Exception as ex:
                UTXT = re.sub('_', '\_', UTXT)
                msg = bot.reply_to(message, 'Необходимо сделать бота *VK Poster* администратором канала %s.\n' \
                    'Отправь мне логин канала (начинается с *@*), в котором *VK Poster* является ' \
                    'администратором и может отправлять сообщения.' % (UTXT.encode('utf-8')), 
                    parse_mode='Markdown')
                bot.register_next_step_handler(msg, add_page_channel)
    elif accept:
        msg = bot.reply_to(message, 'Похоже, ты не прислал логин канала (начинается с *@*). ' \
            'Попробуй ещё раз.', parse_mode='Markdown')
        bot.register_next_step_handler(msg, add_page_channel)

@bot.message_handler(func=lambda message: message.text == u'Настройки моих страниц 🚀')
@bot.message_handler(commands=['settings'])
def settings_choose(message):
    UID = message.chat.id
    UTXT = message.text
    
    db = SQLighter()
    if len(db.select_all_by_uid(UID)) > 0:
        key_nums = types.ReplyKeyboardMarkup(row_width=5, resize_keyboard=True)
        result = db.select_all_by_uid(UID)
        counter = ['NULL']
        pages_list = ''

        for item in result:
            counter.append({'id' : item[0]})
            if item[5] == 0:
                pages_list += '*#%s* ∙ Из *%s* в *чат с ботом*\n' % (str(len(counter) - 1), \
                    item[3].encode('utf-8'))
                key_nums.add(types.KeyboardButton('#%s' % (str(len(counter) - 1))))
            else:
                pages_list += '*#%s* ∙ Из *%s* в *канал %s*\n' % (str(len(counter) - 1), \
                    item[3].encode('utf-8'), item[6].encode('utf-8'))
                key_nums.add(types.KeyboardButton('#%s' % (str(len(counter) - 1))))
        key_nums.row(types.KeyboardButton('⬅️ Вернуться в меню'))

        with io.open(str(UID) + '.UID', 'w', encoding='utf-8') as file:
            # Создаём временный .UID файл для хранения связок ID из базы — номер в клавиатуре
            file.write(unicode(json.dumps({'data': counter}, ensure_ascii=False)))

        msg = bot.send_message(UID, pages_list, parse_mode='Markdown', 
            reply_markup=key_nums)
        bot.send_message(UID, 'Нажми на номер страницы, которую хочешь изменить или удалить.')
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройки пользовательских страниц')
        bot.register_next_step_handler(msg, settings_page)
    else:
        msg = bot.send_message(UID, 'Похоже, *ты не добавил ещё ни одной страницы*.\nНажми /add, чтобы' \
        ' добавить.', parse_mode='Markdown', reply_markup=key_default)
    db.close()

def settings_page(message):
    UID = message.chat.id
    UTXT = message.text

    if UTXT == u'⬅️ Вернуться в меню' or UTXT == u'/cancel' or UTXT == u'Открыть меню':
        bot.send_message(UID, 'Что делаем дальше?', reply_markup=key_default)
    elif bool(re.search('^#\d+\Z', UTXT)):
        UTXT = int(re.sub('#', '', UTXT))

        try:
            with open(str(UID) + '.UID', 'r') as file:
                # Открываем временный .UID для чтения
                data = json.load(file)
            if UTXT < len(data['data']):
                with io.open(str(UID) + '.UID', 'w', encoding='utf-8') as file:
                    # Перезаписываем .UID единственныйм значением — нужным ID из базы
                    file.write(unicode(json.dumps({'id': data['data'][UTXT]['id']})))
                
                db = SQLighter()
                key_settings = keyboard_setup(db.select_all_by_id(data['data'][UTXT]['id']))
                db.close()
            
                bot.send_message(UID, 'Что ты хочешь изменить?', reply_markup=key_settings)
                botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройка одной страницы')
                bot.register_next_step_handler(message, settings_page_doing)
        except Exception as ex:
            print ex
            bot.send_message(UID, 'Похоже, ты прислал мне неправильный номер. Попробуй ещё раз.')
            bot.register_next_step_handler(message, settings_page)
    else:
        bot.send_message(UID, 'Похоже, ты прислал мне неправильный номер. Попробуй ещё раз.')
        bot.register_next_step_handler(message, settings_page)

def settings_page_doing(message):
    UID = message.chat.id
    UTXT = message.text

    with open(str(UID) + '.UID', 'r') as file:
        # Открываем временный .UID для чтения
        data = json.load(file)

    if UTXT == u'Удалить страницу ❌':
        db = SQLighter()
        db.delete_by_id(data['id'])
        db.close

        bot.send_message(UID, '*Страница была удалена.*\nЧто делаем дальше?', parse_mode='Markdown', \
            reply_markup=key_default)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Удаление страницы')
    elif UTXT == u'Включить репосты 📝':
        db = SQLighter()
        db.reposts_update(data['id'], 1)
        keyboard = keyboard_setup(db.select_all_by_id(data['id']))
        db.close
        
        bot.send_message(UID, 'Репосты для данной страницы были включены.', 
            reply_markup=keyboard)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройки: включение репостов')
        bot.register_next_step_handler(message, settings_page_doing)
    elif UTXT == u'Отключить репосты 📝':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.reposts_update(data['id'], 0)
        keyboard = keyboard_setup(db.select_all_by_id(data['id']))
        db.close
        
        bot.send_message(UID, 'Репосты для данной страницы были отключены.', 
            reply_markup=keyboard)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройки: отключение репостов')
        bot.register_next_step_handler(message, settings_page_doing)
    elif UTXT == u'Отключить вложения 📎':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.attachments_update(data['id'], 0)
        keyboard = keyboard_setup(db.select_all_by_id(data['id']))
        db.close
        
        bot.send_message(UID, 'Вложения для данной страницы были отключены.', 
            reply_markup=keyboard)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройки: отключение вложений')
        bot.register_next_step_handler(message, settings_page_doing)
    elif UTXT == u'Включить вложения 📎':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.attachments_update(data['id'], 1)
        keyboard = keyboard_setup(db.select_all_by_id(data['id']))
        db.close
        
        bot.send_message(UID, 'Вложения для данной страницы были включены.', 
            reply_markup=keyboard)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройки: включение вложений')
        bot.register_next_step_handler(message, settings_page_doing)
    elif UTXT == u'Отключить уведомления 🔕':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.notify_update(data['id'], 0)
        keyboard = keyboard_setup(db.select_all_by_id(data['id']))
        db.close
        
        bot.send_message(UID, 'Уведомления для данной страницы были отключены.', 
            reply_markup=keyboard)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройки: отключение уведомлений')
        bot.register_next_step_handler(message, settings_page_doing)
    elif UTXT == u'Включить уведомления 🔔':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.notify_update(data['id'], 1)
        keyboard = keyboard_setup(db.select_all_by_id(data['id']))
        db.close
        
        bot.send_message(UID, 'Уведомления для данной страницы были включены.', 
            reply_markup=keyboard)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройки: включение уведомлений')
        bot.register_next_step_handler(message, settings_page_doing)
    elif UTXT == u'Включить записи участников 🗣':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.is_all_posts_update(data['id'], 1)
        keyboard = keyboard_setup(db.select_all_by_id(data['id']))
        db.close
        
        bot.send_message(UID, 'Отправка записей участников для данной страницы была включена.', 
            reply_markup=keyboard)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройки: включение записей участников')
        bot.register_next_step_handler(message, settings_page_doing)
    elif UTXT == u'Отключить записи участников 🗣':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.is_all_posts_update(data['id'], 0)
        keyboard = keyboard_setup(db.select_all_by_id(data['id']))
        db.close
        
        bot.send_message(UID, 'Отправка записей участников для данной страницы была отключена.', 
            reply_markup=keyboard)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройки: отключение записей участников')
        bot.register_next_step_handler(message, settings_page_doing)
    elif UTXT == u'Показывать название страницы 👁':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.is_title_update(data['id'], 1)
        keyboard = keyboard_setup(db.select_all_by_id(data['id']))
        db.close
        
        bot.send_message(UID, 'Отображение названия страницы было включено.', 
            reply_markup=keyboard)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройки: включено отображение названия')
        bot.register_next_step_handler(message, settings_page_doing)
    elif UTXT == u'Скрыть название страницы 👁':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        db = SQLighter()
        db.is_title_update(data['id'], 0)
        keyboard = keyboard_setup(db.select_all_by_id(data['id']))
        db.close
        
        bot.send_message(UID, 'Отображение названия страницы было отключено.', 
            reply_markup=keyboard)
        botan.track(BOTAN_TOKEN, message.chat.id, message, 'Настройки: отключено отображение названия')
        bot.register_next_step_handler(message, settings_page_doing)
    elif UTXT == u'⬅️ Вернуться в меню':
        os.remove(str(UID) + '.UID')
        bot.send_message(UID, 'Что делаем дальше?', reply_markup=key_default)
    else:
        bot.register_next_step_handler(message, settings_page_doing)

@bot.message_handler(commands=['stop'])
def command_stop(message):
    UID = message.chat.id

    msg = bot.send_message(UID, '⛔️ Ты действительно хочешь *удалить все свои страницы* из *VK Poster*?\n' \
        'Это действие *необратимо*.\n\nЧтобы продолжить, отправь мне _ДА_', parse_mode='Markdown', 
        reply_markup=key_force)
    bot.register_next_step_handler(msg, command_stop_delete)

def command_stop_delete(message):
    UID = message.chat.id
    UTXT = message.text

    if UTXT == u'ДА':
        db = SQLighter()
        # Удаляем из базы все записи, связанные с ID пользователя
        db.delete_by_uid(UID)
        db.close
        bot.send_message(UID, 'Все твои страницы были удалены из *VK Poster*.\nЧтобы запустить бот ' \
            'заново, нажми /start', parse_mode='Markdown')
    else:
        bot.send_message(UID, 'Что делаем дальше?', reply_markup=key_default)

@bot.message_handler(func=lambda message: message.text == u'Открыть меню')
@bot.message_handler(commands=['cancel'])
def open_menu(message):
    UID = message.chat.id

    bot.send_message(UID, 'Что будем делать?', reply_markup=key_default)
    botan.track(BOTAN_TOKEN, message.chat.id, message, 'Главное меню')

@bot.message_handler(func=lambda message: message.text == u'О боте VK Poster 🤖')
@bot.message_handler(commands=['about'])
def command_about(message):
    UID = message.chat.id

    bot.send_message(UID, 'Бот *VK Poster* может автоматически присылать новые записи из групп ' \
        'и публичных страниц ВКонтакте непосредственно в диалог с ботом, либо в указанный тобою ' \
        'канал Telegram.\n\n*VK Poster* написан на Python 2.7 и использует открытые методы API ' \
        'ВКонтакте.\n\nИсходный код бота доступен на GitHub: git.io/vrH5I\n' \
        'Создатель бота: @kozak', parse_mode='Markdown', reply_markup=key_default, 
        disable_web_page_preview=True)
    botan.track(BOTAN_TOKEN, message.chat.id, message, 'Информация о Боте')

@bot.message_handler(commands=['stats'])
def command_stats(message):
    UID = message.chat.id
    UTXT = message.text

    db = SQLighter()
    result = db.select_all()
    chn = db.select_all_chn()
    db.close()
    
    users = []
    for i in result:
        if i[1] not in users:
            users.append(i[1])
    msg = bot.send_message(UID, '🚀 *Статистика*\nАктивных страниц: *%s*\nАктивных пользователей: *%s*\n' \
        'Активных каналов: *%s*\n\nВерсия бота: *2.2.1*' % (len(result), len(users), len(chn)), \
        parse_mode='Markdown')
    botan.track(BOTAN_TOKEN, message.chat.id, message, 'Просмотр статистики')

@bot.message_handler(commands=['help'])
def command_help(message):
    UID = message.chat.id

    bot.send_message(UID, '*Помощь*\n\n/add — добавить новую страницу VK\n/cancel — отмена любого запроса/' \
        'действия\n/settings — раздел настроек всех твоих страниц VK\n/about — информация о боте\n/stats —' \
        'статистика использования бота\n/stop — удаление всех твоих страниц из VK Poster', \
        parse_mode='Markdown')
bot.polling(none_stop=True)