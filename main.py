from config import TOKEN, OWNERID, Stages, KEYS, CODES, NOSUPTYPES

import telebot
from telebot import types
from datetime import datetime, timezone, timedelta

# модуль для работы с БД
import sqlite3 as sl
import time

# токен для доступа к боту
bot = telebot.TeleBot(TOKEN)

# приветственный текст и правила игры
start_txt = ('*Привет, я бот эко-фермы «Селково».*\n\nТут можно оставить обращение для нашего админа или выиграть промокод на скидку [♥](https://i.pinimg.com/originals/78/ff/48/78ff487a09f492514fc36a1bed5646f1.jpg)')
rules_txt = ('*Правила просты:*\n\nзадаём вам три вопроса и дарим промокод. Больше правильных ответов — больше скидка!\n\nВопрос первый:')

# подключаемся к файлу с базой данных и убираем ограничение на запись разных потоков
botbaze = sl.connect('botdata.db', check_same_thread=False)

# открываем файл БД
with botbaze:
    # получаем количество таблиц с нужным нам именем
    data = botbaze.execute("select count(*) from sqlite_master where type='table' and name='stages'")
    for row in data:
        # если таких таблиц нет
        if row[0] == 0:
            # создаём таблицы для отчётов и для учёта статусов игрового процесса
            # для большой аудитории имеет смысл создать третью таблицу — users, сейчас она как часть stages
            with botbaze:
                botbaze.execute("""
                    CREATE TABLE stages (
                        id VARCHAR(200) PRIMARY KEY,
                        stage INTEGER,
                        answers INTEGER DEFAULT 0,
                        first INTEGER DEFAULT 0
                    );
                """)

    data = botbaze.execute("select count(*) from sqlite_master where type='table' and name='feedback'")
    for row in data:
        if row[0] == 0:
            with botbaze:
                botbaze.execute("""
                    CREATE TABLE feedback (
                        date VARCHAR(20),
                        id VARCHAR(100),
                        name VARCHAR(200),
                        text VARCHAR(4000)
                    );
                """)
#сеттеры и геттеры
def get_stage(chat_id):
    with botbaze:
        try:
            cursor = botbaze.cursor()
            cursor.execute('SELECT stage FROM stages WHERE id = ?', (str(chat_id),))
            stages = cursor.fetchone()
            stage = int(stages[0])
            return stage
        except Exception as exx:
            print('❌ Сработало исключение get_stage: ', exx)
            return Stages.S_START.value

def set_stage(chat_id, stage):
    with botbaze:
        try:
            cursor = botbaze.cursor()
            cursor.execute('UPDATE stages SET stage = ? WHERE id = ?', (int(stage), str(chat_id)))
            return
        except Exception as exx:
            print('❌ Сработало исключение set_stage: ', exx)
            return

def get_ans(chat_id):
    with botbaze:
        try:
            cursor = botbaze.cursor()
            cursor.execute('SELECT answers FROM stages WHERE id = ?', (str(chat_id),))
            answers = cursor.fetchone()
            ans = int(answers[0])
            return ans
        except Exception as exx:
            print('❌ Сработало исключение get_ans: ', exx)
            return Stages.S_START.value

def set_ans(chat_id, stage):
    with botbaze:
        try:
            cursor = botbaze.cursor()
            cursor.execute('UPDATE stages SET answers = ? WHERE id = ?', (int(stage), str(chat_id)))
            return
        except Exception as exx:
            print('❌ Сработало исключение set_ans: ', exx)
            return

def set_fir(chat_id):
    with botbaze:
        try:
            cursor = botbaze.cursor()
            cursor.execute('UPDATE stages SET first = ? WHERE id = ?', (1, str(chat_id)))
            return
        except Exception as exx:
            print('❌ Сработало исключение set_fir: ', exx)
            return

def get_fir(chat_id):
    with botbaze:
        try:
            cursor = botbaze.cursor()
            cursor.execute('SELECT first FROM stages WHERE id = ?', (str(chat_id),))
            answers = cursor.fetchone()
            ans = int(answers[0])
            return ans
        except Exception as exx:
            print('❌ Сработало исключение get_fir: ', exx)
            return Stages.S_START.value

# обрабатываем старт бота
@bot.message_handler(commands=['who'])
def welcome(message):
    chat_id = message.chat.id
    if str(chat_id) == str(OWNERID):
        bot.send_message(chat_id, "Вы админ ♥", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "Вы не админ! [Написать админу 🍪](https://t.me/ogne3)", parse_mode='Markdown')
@bot.message_handler(commands=['dayrep'])
def fb(message):
    chat_id = message.chat.id
    if str(chat_id) == str(OWNERID):
        # подключаемся к базе
        botbaze = sl.connect('botdata.db')
        # получаем сегодняшнюю дату
        now = datetime.now(timezone.utc)
        date = now.date()
        # пустая строка для будущих отчётов
        s = ''
        # работаем с базой
        with botbaze:
            # выполняем запрос к базе
            data = botbaze.execute('SELECT * FROM feedback WHERE date = :Date;', {'Date': str(date)})
            # перебираем все результаты
            for row in data:
                # формируем строку в общем отчёте
                s = s + '*' + row[2] + '*' + ': ' + row[3] + '\n\n'
        # если отчётов не было за сегодня
        if s == '':
            # формируем новое сообщение
            s = 'Сегодня мы без фидбека!'
        # отправляем общий отчёт обратно в телеграм
        bot.send_message(message.from_user.id, s, parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "Эта команда только для админа, увы.", parse_mode='Markdown')
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    with botbaze:
        try:
            cursor = botbaze.cursor()
            cursor.execute('SELECT id FROM stages WHERE id = ?', (str(chat_id),))
            results = cursor.fetchone()
            print(results)
            if str(results) == 'None':
                # Добавляем нового пользователя
                cursor.execute('INSERT INTO stages (id, stage) VALUES (?, ?)',
                               (str(chat_id), 0))
            else:
                set_stage(chat_id, 0)
            cursor.execute('SELECT * FROM stages')
            results=cursor.fetchall()
            print(results)
        except Exception as exx:
            print('❌ Сработало исключение внесения юзера в БД: ', exx)

    btn_fb = telebot.types.KeyboardButton(text="Оставить обращение!")
    btn_pl = telebot.types.KeyboardButton(text="Сыграть!")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(btn_fb, btn_pl)
    bot.send_message(chat_id, start_txt, parse_mode='Markdown', reply_markup=keyboard)
    print(get_stage(message.chat.id))

@bot.message_handler(func=lambda message: get_stage(message.chat.id) == Stages.S_START.value, content_types=['text'])
def option(message):
    keyboard = telebot.types.ReplyKeyboardRemove()
    if message.text=="Оставить обращение!":
        set_stage(message.chat.id, -1)
        bot.send_message(message.chat.id,'Напишите отзыв о нашей работе. От 8 до 4000 знаков, пожалуйста.', reply_markup=keyboard)
    elif message.text=="Сыграть!":
        print(get_stage(message.chat.id))
        bot.send_message(message.chat.id, rules_txt, parse_mode='Markdown', reply_markup=keyboard)
        time.sleep(1)
        quess(message, get_stage(message.chat.id))
        print(get_stage(message.chat.id), get_fir(message.chat.id), get_ans(message.chat.id))
    elif message.text == "/who":
        welcome(message)
    elif message.text == "/dayrep":
        fb(message)
    else:
        bot.send_message(message.chat.id, 'Выберите один из предложенных вариантов.')

def question(message, q, a1, a2, a3, key):
    chat_id = message.chat.id
    keyboard = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text=a1, callback_data='1')
    btn2 = telebot.types.InlineKeyboardButton(text=a2, callback_data='2')
    btn3 = telebot.types.InlineKeyboardButton(text=a3, callback_data='3')
    keyboard.add(btn1, btn2, btn3)
    bot.send_message(chat_id, q, parse_mode="Markdown", reply_markup=keyboard)

def answ(call):
    mess = call.message
    chid = mess.chat.id
    messid = mess.message_id
    an = get_ans(chid)
    print(KEYS[get_stage(chid)], '|', call.data)
    if str(KEYS[get_stage(chid)]) == call.data:
        set_ans(chid, an + 1)
    bot.edit_message_text(chat_id=chid, message_id=messid,
                          text=str(str(get_stage(chid)+ 1) + '. Ответ принят.'))
    set_stage(chid, get_stage(chid) + 1)
    time.sleep(1)
    if get_stage(chid) <= 3:
        quess(mess, get_stage(chid))

def quess(message, a):
    if a == 0:
        question(message, "Сколько литров молока нужно, чтобы сделать один килограмм сыра? [🥛](https://www.timeoutabudhabi.com/cloud/timeoutabudhabi/2021/11/04/cheese-and-grape-nights-in-Abu-Dhabi-2021-1024x768.jpg)", "100", '10', '1', 1)
    elif a == 1:
        question(message,
                 "Как называется эта порода коров? [🐮](https://i.ytimg.com/vi/fTBF-S_22_8/maxresdefault.jpg)",
                 "Джерси", 'Хайленд', 'Костромская', 3)
    elif a == 2:
        question(message, "В каком веке сыр появился в России? [🧀](https://live.staticflickr.com/3894/32976515421_c3596105ab_b.jpg)", "10 в.",
                 '15 в.', '18 в.', 2)
    elif a == 3:
        print('Юзер завершил игру.')
        gift(message)

def gift(message):
    chid=message.chat.id
    gift_txt = str('Правильных ответов: ' + str(get_ans(chid)))
    if get_fir(chid) == 0:
        gift_txt += str(', поэтому дарим вам промокод: '+ CODES[get_ans(chid)] +'. Используйте его при заказе на сайте salkovo.ru.')
    else:
        gift_txt += str('. Вы уже проходили игру и получили промокод ранее.')
    set_fir(chid)
    set_ans(chid, 0)
    set_stage(chid, 0)
    bot.send_message(message.chat.id, gift_txt, parse_mode='Markdown')
    bot.send_message(message.chat.id, 'Для возвращения к началу отправьте в чат команду /start.', parse_mode='Markdown')


@bot.callback_query_handler(func=lambda call: call.data == '1')
def go(call):
    answ(call)
@bot.callback_query_handler(func=lambda call: call.data == '2')
def go(call):
    answ(call)
@bot.callback_query_handler(func=lambda call: call.data == '3')
def go(call):
    answ(call)

def func(message):
    sql = 'INSERT INTO feedback (date, id, name, text) values(?, ?, ?, ?)'
    now = datetime.now(timezone.utc)
    date = now.date()
    data = [
        (str(date), str(message.from_user.id), str(message.from_user.username), str(message.text[:4000]))
    ]
    # добавляем с помощью запроса данные
    with botbaze:
        try:
            botbaze.executemany(sql, data)
            set_stage(message.chat.id, 0)
            bot.send_message(message.from_user.id, 'Принято, спасибо!', parse_mode='Markdown')
            bot.send_message(message.chat.id, 'Для возвращения к началу отправьте в чат команду /start.',
                             parse_mode='Markdown')
        except Exception as eins:
            print('❌ Сработало исключение внесения в БД: ', eins)
            bot.send_message(message.from_user.id, 'Неполадки с базой данных. Пожалуйста, отправьте отзыв повторно!', parse_mode='Markdown')
   # отправляем пользователю сообщение о том, что отчёт принят
@bot.message_handler(content_types=NOSUPTYPES)
def give_photo(message):
    bot.send_message(message.chat.id, text="Изображения и другие файлы не принимаю, увы! Только текст.")
@bot.message_handler(func=lambda message: get_stage(message.chat.id) == Stages.S_FB.value, content_types=['text'])
def insert(message):
    if len(message.text)>=8 and len(message.text)<=4000:
        func(message)
    else:
        bot.send_message(message.from_user.id, 'Присмотритесь к требованиям выше и попробуйте снова.', parse_mode='Markdown')

# запускаем бота
if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as emain:
            print('❌ Сработало исключение polling: ', emain)