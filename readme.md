# VKPosterBot
Бот для автоматического постинга записей из групп и публичных страниц ВКонтакте в Telegram. __В данный момент бот находится в разработке, код прокомментирован неполностью.__ 

Работающий бот: [@VKPstBot](https://telegram.me/VKPstBot) в Telegram

Бот создан [@kozak](https://telegram.me/kozak) на основе урока [@Groosha](https://telegram.me/Groosha) (https://kondra007.gitbooks.io/telegram-bot-lessons/content/chapter5.html).

### Возможности
* Все страницы VK бот хранит в базе данных SQLite
* При добавлении страницы можно указать, куда отправлять новые записи — пользователю в чат с ботом или в публичный канал Telegram
* Бот поддерживает отправку вложений к постам: фотографии, аудио и GIF-файлы. Также отправляет ссылки на видео и опросы VK
* После добавления страницу можно настроить: отправка репостов с других групп (да/нет), отправка вложений (да/нет) и отправка push-уведомлений о новых записях (да/нет)

## Установка
1. Для начала необходимо создать базу данных SQLite `data.db` в директории с ботом. Код запроса для Python:

```python
import sqlite3
    
con = sqlite3.connect('data.db')
data = con.cursor()
    
data.execute("""
CREATE TABLE storage (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    vk TEXT,
    vk_original TEXT,
    vk_type TEXT,
    type INTEGER,
    channel TEXT,
    is_reposts INTEGER,
    is_attachments INTEGER,
    last_id INTEGER,
    is_notify INTEGER
)
""")
con.commit()
```
2. После создания базы, пишем [@BotFather](https://telegram.me/BotFather) и создаём нового бота. [@BotFather](https://telegram.me/BotFather) создаст TOKEN, который необходимо прописать в `Core.py` и `VKPst.py` в соответствующую константу.
3. Бот использует фреймворк [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI), а также модули `requests`, `eventlet`. Чтобы установить необходимые зависимости:
```bash
pip install pyTelegramBotAPI
pip install requests
pip install eventlet
```
4. `VKPst.py` отвечает за работу самого бота и за добавление/настройку/удаление страниц в базе. `Core.py` проверяет новые записи в группах из базы и отправляет их пользователям/каналам. `SQLighter.py` обрабатывает все запросы в базу данных.
```bash
python VKPst.py
python Core.py
```
