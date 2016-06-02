# -*- coding: utf-8 -*-
import telebot
from time import sleep
from telebot import util
from telebot import types
from SQLighter import SQLighter
import json, time, sys, re, os, vk
import logging, urllib, requests, eventlet

os.environ['TZ'] = 'Europe/Moscow'
time.tzset() # Настройка времени на сервере

# Настройка соединения с Telegram
API_TOKEN = ''

ship = telebot.TeleBot(API_TOKEN)

session = vk.Session()
api = vk.API(session)

# Создание клавиатуры по-умолчанию
open_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
open_menu.row(types.KeyboardButton('Открыть меню'))

def get_data(item, is_all_posts):
    # Полчение данных от vk.com с указанными параметрами
    if item[4] == 'ID':
        if is_all_posts == 1:
            api = 'https://api.vk.com/method/wall.get?owner_id=-%s&count=10&extended=1' % (item[2])
        else:
            api = 'https://api.vk.com/method/wall.get?owner_id=-%s&count=10&filter=owner&extended=1' % \
                (item[2])
    else:
        if is_all_posts == 1:
            api = 'https://api.vk.com/method/wall.get?domain=%s&count=10&extended=1' % (item[2])
        else:
            api = 'https://api.vk.com/method/wall.get?domain=%s&count=10&filter=owner&extended=1' % \
                (item[2])

    # Указываем время для таймаута           
    timeout = eventlet.Timeout(10)
    try:
        result = requests.get(api).json()
        return result
    except eventlet.timeout.Timeout:
        logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()

def sender(posts, last_id, vk_name, UID, TO, CHN, is_reposts, is_attaches, is_notify, is_title):
    for post in reversed(posts):
        if (post['id'] <= last_id) or (is_reposts == 0 and 'copy_post_date' in post) or \
        (is_attaches == 0 and len(post['text']) == 0):
            # Если пост старый, либо это репост, либо нет вложений и они
            # отключены, то переходим к следующему посту
            continue
        
        # Формируем сообщение с заголовком записи
        post_from = u'Запись из *%s*' % (vk_name)
        if post['from_id'] != post['to_id']:
            user_name = api.users.get(user_ids=post['from_id'])[0]['first_name'] + ' ' + \
            api.users.get(user_ids=post['from_id'])[0]['last_name']
            # Добавляем ссылку на автора и ссылку на запись
            post_from += u'\nОт: [%s](https://vk.com/id%s)\n[Показать запись VK](https://vk.com/' \
                'wall%s_%s)' % (user_name, post['from_id'], post['to_id'], post['id'])
            
        if is_title == 1:
            # Если нужно отправлять название страницы, то отправляем
            if is_notify == 1 and TO == 0:
                ship.send_chat_action(UID, 'typing')
                ship.send_message(UID, post_from, parse_mode='Markdown', reply_markup=open_menu,
                    disable_web_page_preview=True)
            elif is_notify == 1 and TO == 1:
                ship.send_message(CHN, post_from, parse_mode='Markdown', disable_web_page_preview=True)
            elif is_notify == 0 and TO == 0:
                ship.send_chat_action(UID, 'typing')
                ship.send_message(UID, post_from, parse_mode='Markdown', reply_markup=open_menu,
                    disable_notification=True, disable_web_page_preview=True)
            elif is_notify == 0 and TO == 1:
                ship.send_message(CHN, post_from, parse_mode='Markdown',
                    disable_notification=True, disable_web_page_preview=True)

        if len(post['text']) > 0:
            # Если есть текст записи, то обрабатываем его
            body = post['text']
            body = re.sub('<br>', '\n', body)
            body = re.sub('<[^>]+>', '', body)
            body = re.sub('\[(?P<link>.+)\|(?P<title>.+)\]', '<a href=\'http://vk.com/\g<link>\'>' \
                '\g<title></a>', body)

            if len(body) > 3000:
                # Если запись длинее 3000 символов, разбиваем на несколько сообщений
                splitted_text = util.split_string(body, 3000)
                for text in splitted_text:
                    if TO == 0:
                        ship.send_chat_action(UID, 'typing')
                        ship.send_message(UID, text, disable_notification=True, parse_mode='HTML')
                    else:
                        ship.send_message(CHN, text, disable_notification=True, parse_mode='HTML')
            else:
                if TO == 0:
                    ship.send_chat_action(UID, 'typing')
                    ship.send_message(UID, body, disable_notification=True, parse_mode='HTML')
                else:
                    ship.send_message(CHN, body, disable_notification=True, parse_mode='HTML')
        
        if is_attaches == 1:
            # Если нужно отправлять вложения, то проверяем их наличие
            try:
                for item in post['attachments']:
                    # Проверяем каждое вложение из данных vk.com
                    if item['type'] == 'photo':
                        # Если фотография, то загружаем её на сервер и отправляем
                        name = '%s.jpg' % (item['photo']['pid'])
                        urllib.urlretrieve(item['photo']['src_big'], name)
                        
                        with open(name, 'rb') as photo:
                            # Открываем фото и отправляем в канал либо чат
                            if TO == 0:
                                ship.send_chat_action(UID, 'upload_photo')
                                ship.send_photo(UID, photo, disable_notification=True)
                            else:
                                ship.send_photo(CHN, photo, disable_notification=True)
                        # Удаляем фото после отправки
                        os.remove(name)
                
                    elif item['type'] == 'audio':
                        # Если аудио, то загружаем его на сервер и отправляем
                        name = '%s.mp3' % (int(item['audio']['aid']))
                        url_check = int(urllib.urlopen(item['audio']['url']).info()['Content-Length']) >> 20
                        if url_check > 35:
                            # Если размер файла более 35mb, то пропускаем его
                            continue
                        
                        urllib.urlretrieve(item['audio']['url'], name)
                        try:
                            # Пытаемся отправить файл в канал либо чат
                            with open(name, 'rb') as audio:
                                # Получаем мета-данные от vk.com
                                duration = int(item['audio']['duration'])
                                performer = str(item['audio']['performer'].encode('utf-8'))
                                title = str(item['audio']['title'].encode('utf-8'))
                        
                                if TO == 0:
                                    ship.send_chat_action(UID, 'upload_audio')
                                    ship.send_audio(UID, audio, duration, performer, title, 
                                        disable_notification=True, timeout=15)
                                else:
                                    ship.send_audio(CHN, audio, duration, performer, title, 
                                        disable_notification=True, timeout=15)
                                # Удаляем аудио после отправки
                                os.remove(name)
                        except Exception as ex:
                            # Если произошла ошибка, выводим её, удаляем файл и продолжаем
                            os.remove(name)
                            logging.error('Exception of type {!s} in sender() while send audio' \
                                ': {!s}'.format(type(ex).__name__, str(ex)))
                            continue

                    elif item['type'] == 'doc':
                        if item['doc']['ext'] == 'gif':
                            # Если GIF-файл, то загружаем его на сервер и отправляем
                            name = '%s.gif' % (item['doc']['did'])
                            urllib.urlretrieve(item['doc']['url'], name)
                            gif = open(name, 'rb')
                        
                            if TO == 0:
                                ship.send_chat_action(UID, 'upload_photo')
                                ship.send_document(UID, gif, disable_notification=True, timeout=9)
                            else:
                                ship.send_document(CHN, gif, disable_notification=True, timeout=9)
                            # Удаляем GIF после отправки
                            os.remove(name)
                    elif item['type'] == 'video':
                        # Если есть видео, то отправляем ссылку на него
                        link = u'*Видео:* https://vk.com/video-%s\_%s' % (abs(item['video']['owner_id']), \
                            item['video']['vid'])
    
                        if TO == 0:
                            ship.send_chat_action(UID, 'typing')
                            ship.send_message(UID, link, parse_mode='Markdown', disable_notification=True)
                        else:
                            ship.send_message(CHN, link, parse_mode='Markdown', disable_notification=True)
                
                    elif item['type'] == 'poll':
                        # Если есть опрос, то отправляем ссылку на него
                        link = 'Опрос: %s \nhttps://vk.com/wall-%s_%s' % \
                        (item['poll']['question'].encode('utf-8'), abs(post['from_id']), post['id'])
    
                        if TO == 0:
                            ship.send_chat_action(UID, 'typing')
                            ship.send_message(UID, link, disable_web_page_preview=True,
                                disable_notification=True)
                        else:
                            ship.send_message(CHN, link, disable_web_page_preview=True,
                                disable_notification=True)
            except Exception as ex:
                # Отображаем ошибку и продолжаем дальше
                logging.error('Exception of type {!s} in sender(): {!s}'.format(type(ex).__name__, str(ex)))
                continue
    # Сон на 1 секунду между каждым шагом цикла
    time.sleep(1)
    return

def checker(item):
    # Пишем текущее время начала
    logging.info('[VK] Started scanning for new posts')
    last_id = item[9]
    logging.info('Last ID (VK) = {!s}'.format(last_id))
    
    try:
        # Получаем данные от vk.com
        posts = get_data(item, item[12])
        array = posts['response']['wall'][1:]
        # Получаем название страницы-источника
        vk_name = posts['response']['groups'][0]['name']

        try:
            is_pinned = array[0]['is_pinned']
        except:
            is_pinned = 0

        if is_pinned == 0:
            new_last_id = array[0]['id']
            logging.info('New last_id (VK) is {!s}'.format(new_last_id))
            
            sender(array, last_id, vk_name, item[1], item[5], item[6], item[7], item[8], item[10], item[11])
        else:
            new_last_id = array[1]['id']
            logging.info('New last_id (VK) is {!s}'.format(new_last_id))
            
            sender(array[1:], last_id, vk_name, item[1], item[5], item[6], item[7], item[8], item[10], item[11])
        return new_last_id
    except Exception as ex:
        # Отображаем ошибку и продолжаем
        logging.error('Exception of type {!s} in checker(): {!s}'.format(type(ex).__name__, str(ex)))
        return last_id

# Настройка логирования
logging.getLogger('requests').setLevel(logging.CRITICAL)
logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', 
    level=logging.INFO, filename='ship.log', datefmt='%d.%m.%Y %H:%M:%S')

while True:
    db = SQLighter()
    # Получаем данные о страницах из базы данных
    data = db.select_all()
    for item in data:
        # Для каждой страницы совершаем обход
        last_id = int(checker(item))
        # Обновляем `last_id` в базе
        db.update_last_id(item[0], last_id)
    # Закрываем соединение с базой
    db.close()

    logging.info('[App] Script went to sleep.')
    # Спим в течение 3 минут
    time.sleep(60 * 3)

logging.info('[App] Script exited.\n')