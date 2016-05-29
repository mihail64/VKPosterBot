# -*- coding: utf-8 -*-
from SQLighter import SQLighter
from telebot import types
from telebot import util
from time import sleep
import requests
import eventlet
import telebot
import logging
import urllib
import json
import time
import sys
import re
import os

# TOKEN для вашего бота, нужно запросить у @BotFather
API_TOKEN = ''

# Создание бота
bot_core = telebot.TeleBot(API_TOKEN)

# Создание кнопки открытия меню
open_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
open_menu.row(types.KeyboardButton('Открыть меню'))

def get_data(item):
    # Получение данных, используя VK API
    if item[4] == 'ID':
        api = 'https://api.vk.com/method/wall.get?owner_id=-%s&count=10&filter=owner&' \
        'extended=1' % (item[2])
    else:
        api = 'https://api.vk.com/method/wall.get?domain=%s&count=10&filter=owner&' \
        'extended=1' % (item[2])

    timeout = eventlet.Timeout(10)
    try:
        result = requests.get(api).json()
        return result
    except eventlet.timeout.Timeout:
        logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()

def sender(posts, last_id, VK_NAME, UID, TO, CHN, is_reposts, is_attachments, is_notify):
    """
    Функция, отвечающая за отправку сообщений в Telegram
    """
    for post in reversed(posts):
        if (post['id'] <= last_id) or (is_reposts == 0 and 'copy_post_date' in post) or \
        (is_attachments == 0 and len(post['text']) == 0):
            continue

        post_from = u'Запись из *%s*' % (VK_NAME)

        if is_notify == 1:
            if TO == 0:
                bot_core.send_message(UID, post_from, parse_mode='Markdown', reply_markup=open_menu)
            else:
                bot_core.send_message(CHN, post_from, parse_mode='Markdown')
        else:
            if TO == 0:
                bot_core.send_message(UID, post_from, parse_mode='Markdown', reply_markup=open_menu,
                    disable_notification=True)
            else:
                bot_core.send_message(CHN, post_from, parse_mode='Markdown',
                    disable_notification=True)

        if len(post['text']) > 0:
            post_text = post['text']
            post_text = re.sub('<br>', '\n', post_text)
            post_text = re.sub('<[^>]+>', '', post_text)
            post_text = re.sub('\[(?P<link>.+)\|(?P<title>.+)\]', 
                '<a href=\'http://vk.com/\g<link>\'>\g<title></a>', post_text)

            if len(post_text) > 3000:
                # Если запись длинее 3000 символов, разбиваем на несколько сообщений
                splitted_text = util.split_string(post_text, 3000)
                for text in splitted_text:
                    if TO == 0:
                        bot_core.send_message(UID, text, disable_notification=True, parse_mode='HTML')
                    else:
                        bot_core.send_message(CHN, text, disable_notification=True, parse_mode='HTML')
            else:
                if TO == 0:
                    bot_core.send_message(UID, post_text, disable_notification=True, parse_mode='HTML')
                else:
                    bot_core.send_message(CHN, post_text, disable_notification=True, parse_mode='HTML')
        
        if is_attachments == 1:
            try:
                for item in post['attachments']:
                    if item['type'] == 'photo':
                        # Загрузка фото на сервер и отпрвка
                        file_name = '%s.jpg' % (item['photo']['pid'])
                        urllib.urlretrieve(item['photo']['src_big'], file_name)
                        photo = open(file_name, 'rb')
                
                        if TO == 0:
                            bot_core.send_chat_action(UID, 'upload_photo')
                            bot_core.send_photo(UID, photo, disable_notification=True)
                        else:
                            bot_core.send_photo(CHN, photo, disable_notification=True)
                        os.remove(file_name)
                
                    elif item['type'] == 'audio':
                        # Загрузка аудио на сервер и отправка
                        file_name = '%s.mp3' % (item['audio']['aid'])
                        urllib.urlretrieve(item['audio']['url'], file_name)
                        audio = open(file_name, 'rb')
                        print audio
                        duration = item['audio']['duration']
                        performer = item['audio']['performer']
                        title = item['audio']['title']
                        print duration, performer, title
                        if TO == 0:
                            bot_core.send_chat_action(UID, 'upload_audio')
                            bot_core.send_audio(UID, audio, duration=duration, performer=performer, 
                                title=title, disable_notification=True)
                        else:
                            bot_core.send_audio(CHN, audio, duration=duration, performer=performer, 
                                title=title, disable_notification=True)
                            print 'got it'
                        os.remove(file_name)

                    elif item['type'] == 'doc':
                        if item['doc']['ext'] == 'gif':
                            # Загрузка GIF на сервер и отправка
                            file_name = '%s.gif' % (item['doc']['did'])
                            urllib.urlretrieve(item['doc']['url'], file_name)
                            gif = open(file_name, 'rb')
                        
                            if TO == 0:
                                bot_core.send_chat_action(UID, 'upload_photo')
                                bot_core.send_document(UID, gif, disable_notification=True)
                            else:
                                BOT.send_document(CHN, gif, disable_notification=True)
                            os.remove(file_name)

                    elif item['type'] == 'video':
                        # Формирование ссылки на видео и оправка
                        link = u'*Видео:*\nhttps://vk.com/video-%s_%s' % (abs(item['video']['owner_id']), 
                        item['video']['vid'])
    
                        if TO == 0:
                            bot_core.send_message(UID, link, parse_mode='Markdown', disable_notification=True)
                        else:
                            bot_core.send_message(CHN, link, parse_mode='Markdown', disable_notification=True)
                
                    elif item['type'] == 'poll':
                        # Формирование ссылки на опрос и отправка
                        link = 'Опрос: %s \nhttps://vk.com/wall-%s_%s' % \
                        (item['poll']['question'].encode('utf-8'), abs(post['from_id']), post['id'])
    
                        if TO == 0:
                            bot_core.send_message(UID, link, disable_web_page_preview=True,
                                disable_notification=True)
                        else:
                            bot_core.send_message(CHN, link, disable_web_page_preview=True,
                                disable_notification=True)
            except Exception as ex:
                logging.error('Exception of type {!s} in checker(): {!s}'.format(type(ex).__name__, str(ex)))
                continue
    time.sleep(1)
    return

def checker(item):
    """
    Функция, получающая ID последнего поста, данные VK API, и передающая их sender()
    """
    logging.info('[VK] Started scanning for new posts')
    last_id = item[9]
    logging.info('Last ID (VK) = {!s}'.format(last_id))
    
    try:
        posts = get_data(item)
        array = posts['response']['wall'][1:]
        VK_NAME = posts['response']['groups'][0]['name']

        try:
            is_pinned = array[0]['is_pinned']
        except:
            is_pinned = 0

        if is_pinned == 0:
            new_last_id = array[0]['id']
            logging.info('New last_id (VK) is {!s}'.format(new_last_id))
            
            sender(array, last_id, VK_NAME, item[1], item[5], item[6], item[7], item[8], item[10])
        else:
            new_last_id = array[1]['id']
            logging.info('New last_id (VK) is {!s}'.format(new_last_id))
            
            sender(array[1:], last_id, VK_NAME, item[1], item[5], item[6], item[7], item[8], item[10])
        return new_last_id
    except Exception as ex:
        logging.error('Exception of type {!s} in checker(): {!s}'.format(type(ex).__name__, str(ex)))
        return last_id

# Настройка логирования
logging.getLogger('requests').setLevel(logging.CRITICAL)
logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', 
    level=logging.INFO, filename='core_log.log', datefmt='%d.%m.%Y %H:%M:%S')

while True:
    # Создание бесконечного цикла с паузой в 5 минут
    db = SQLighter()
    data = db.select_all()
    for item in data:
        last_id = int(checker(item))
        db.update_last_id(item[0], last_id)
    db.close()

    logging.info('[App] Script went to sleep.')
    time.sleep(60 * 5)

logging.info('[App] Script exited.\n')