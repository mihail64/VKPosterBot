# -*- coding: utf-8 -*-
import sqlite3

class SQLighter:
    def __init__(self):
        """ Настраиваем соединение с базой """
        self.connection = sqlite3.connect('data.db')
        self.cursor = self.connection.cursor()

    def insert(self, uid, vk, vk_original, vk_type, last_id, to, channel, is_reposts, is_attchs):
        """ Добавляем запись в базу """
        with self.connection:
            self.cursor.execute("""
                    INSERT INTO storage (
                        id,
                        user_id,
                        vk,
                        vk_original,
                        vk_type,
                        last_id,
                        type, 
                        channel,
                        is_reposts,
                        is_attachments,
                        is_notify
                    )
                    VALUES (
                        NULL,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        1
                    )
                    """, (uid, vk, vk_original, vk_type, last_id, to, channel, is_reposts, is_attchs))
            self.connection.commit()

    def delete_by_id(self, row_id):
        """ Удаляем запись из базы по ID """
        with self.connection:
            self.cursor.execute('DELETE FROM storage WHERE id=?', (row_id,))
            self.connection.commit()

    def reposts_update(self, row_id, param):
        """ Обновляем настройки репостов """
        with self.connection:
            self.cursor.execute('UPDATE storage SET is_reposts=? WHERE id=?', (param, row_id))
            self.connection.commit()

    def attachments_update(self, row_id, param):
        """ Обновляем настройки вложений """
        with self.connection:
            self.cursor.execute('UPDATE storage SET is_attachments=? WHERE id=?', (param, row_id))
            self.connection.commit()

    def notify_update(self, row_id, param):
        """ Обновляем настройки уведомлений """
        with self.connection:
            self.cursor.execute('UPDATE storage SET is_notify=? WHERE id=?', (param, row_id))
            self.connection.commit()

    def update_last_id(self, row_id, param):
        """ Обновляем ID последнего поста в базе """
        with self.connection:
            self.cursor.execute('UPDATE storage SET last_id=? WHERE id=?', (param, row_id))
            self.connection.commit()

    def select_all_by_uid(self, uid):
        """ Получаем все строки по ID пользователя """
        with self.connection:
            return self.cursor.execute('SELECT * FROM storage WHERE user_id=?', (uid,)).fetchall()

    def select_all_by_id(self, row_id):
        """ Получаем все строки по ID """
        with self.connection:
            return self.cursor.execute('SELECT * FROM storage WHERE id=?', (row_id,)).fetchall()

    def select_all(self):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM storage').fetchall()

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()