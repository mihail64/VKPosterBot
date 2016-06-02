# -*- coding: utf-8 -*-
import sqlite3

class SQLighter:
    # Класс, отвечающий за запросы в базу данных
    def __init__(self):
        # Подключение к базе данных
        self.connection = sqlite3.connect('data.db')
        self.cursor = self.connection.cursor()

    def insert(self, uid, vk, vk_original, vk_type, last_id, to, channel, is_reposts, is_attchs):
        # Добавление записи в базу данных
        with self.connection:
            self.cursor.execute("""
                    INSERT INTO storage (
                        id, user_id, vk, vk_original, vk_type, last_id, type, channel, is_reposts,
                        is_attachments, is_notify, is_title, is_all_posts )
                    VALUES ( 
                        NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 0 )
                    """, (uid, vk, vk_original, vk_type, last_id, to, channel, is_reposts, 
                        is_attchs))
            self.connection.commit()

    def delete_by_id(self, row_id):
        # Удаление записи по полученному ID
        with self.connection:
            self.cursor.execute('DELETE FROM storage WHERE id=?', (row_id,))
            self.connection.commit()

    def delete_by_uid(self, row_id):
        # Удаление всех записей по пользовательскому UID
        with self.connection:
            self.cursor.execute('DELETE FROM storage WHERE user_id=?', (row_id,))
            self.connection.commit()

    def reposts_update(self, row_id, param):
        # Изменение настроек: репосты
        with self.connection:
            self.cursor.execute('UPDATE storage SET is_reposts=? WHERE id=?', (param, row_id))
            self.connection.commit()

    def attachments_update(self, row_id, param):
        # Изменение настроек: вложения
        with self.connection:
            self.cursor.execute('UPDATE storage SET is_attachments=? WHERE id=?', (param, row_id))
            self.connection.commit()

    def notify_update(self, row_id, param):
        # Изменение настроек: уведомления
        with self.connection:
            self.cursor.execute('UPDATE storage SET is_notify=? WHERE id=?', (param, row_id))
            self.connection.commit()
    
    def is_title_update(self, row_id, param):
        # Изменение настроек: отображение названия
        with self.connection:
            self.cursor.execute('UPDATE storage SET is_title=? WHERE id=?', (param, row_id))
            self.connection.commit()
    
    def is_all_posts_update(self, row_id, param):
        # Изменение настроек: отправка всех записей
        with self.connection:
            self.cursor.execute('UPDATE storage SET is_all_posts=? WHERE id=?', (param, row_id))
            self.connection.commit()

    def update_last_id(self, row_id, param):
        # Обновление `last_id` в базе данных
        with self.connection:
            self.cursor.execute('UPDATE storage SET last_id=? WHERE id=?', (param, row_id))
            self.connection.commit()

    def select_all_by_uid(self, uid):
        # Получение всех строк по пользовательскому ID
        with self.connection:
            return self.cursor.execute('SELECT * FROM storage WHERE user_id=?', (uid,)).fetchall()

    def select_all_by_id(self, row_id):
        # Получение строки по ID
        with self.connection:
            return self.cursor.execute('SELECT * FROM storage WHERE id=?', (row_id,)).fetchall()

    def select_all_chn(self):
        # Получение все каналов из базы
        with self.connection:
            return self.cursor.execute('SELECT * FROM storage WHERE type=1').fetchall()

    def select_by_chn(self, chn):
        # Получение все каналов из базы
        with self.connection:
            return self.cursor.execute('SELECT * FROM storage WHERE channel=?', (chn,)).fetchall()

    def select_all(self):
        # Получение всех строк из базы данных
        with self.connection:
            return self.cursor.execute('SELECT * FROM storage').fetchall()

    def close(self):
        # Закрытие соединения с базой данных
        self.connection.close()