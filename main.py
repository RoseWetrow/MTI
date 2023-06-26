import telebot
from telebot import types # для указание типов
import psycopg2 # библиотека для работы с PostgreSQL
from config import host, user, password, db_name # переменные с файла config.py
from psycopg2 import pool # реализация пула соединений с PostgreSQL
from geo import getGeo


bot = telebot.TeleBot('...')

previous_message_markup = None  # переменная для хранения состояния разметки

@bot.message_handler(commands=['start']) # обработчик команды /start
def start(message):

    global previous_message_markup
            
    markupStart = types.InlineKeyboardMarkup() # создание разметки для клавиатуры
    about = types.InlineKeyboardButton('О боте', callback_data='about') # создание кнопки 'О боте'
    markupStart.add(about)

    # отправка сообщения
    bot.send_message(message.chat.id, f'<b>MoscowTransportInformationBot</b> приветствует вас, {message.from_user.username}!\n\nЧтобы получить информацио об интересующем вас маршруте, введите его номер в формате: /903', parse_mode='html', reply_markup=markupStart)
    # сохранение состояния разметки
    previous_message_markup = markupStart


@bot.callback_query_handler(func=lambda call: call.data == 'about') # обработчик нажатия на кнопку
def callback(call):

    global previous_message_markup

    if call.message: # если нажата кнопка

        # if call.data == 'about':
            markupBack = types.InlineKeyboardMarkup() # создание новой разметки
            back = types.InlineKeyboardButton('Назад', callback_data='aboutBack') # создание кнопки 'Назад'
            markupBack.add(back)
            # изменяем предыдущее сообщение
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='ℹ️ MTI (Moscow Transport Information Bot) — бот, предоставляющий информацию о любом, интересующем вас маршруте, в удобном формате.\nЗдесь вы можете узнать информацию об интересующем вас маршруте (наименование маршрута, список остановок по пути следования), а так же информацию об интересующей вас остановке (полный адрес, локация, список автобусов, останавливающихся на остановке и их маршрут).\n\n📊 Бот работает на данных, взятых с портала открытых данных Правительства Москвы. База данных содержит более 6 миллионов записей, сгруппированных между собой и оптимизированных для быстрого выполнения запросов.\n\nПо вопросам связанными с ботом писать сюда - @ZamirNowarov', reply_markup=markupBack)

@bot.callback_query_handler(func=lambda call: call.data == 'aboutBack') # обработчик нажатия на кнопку
def callback(call):
        
    if call.message: # если нажата кнопка
        # изменяем предыдущее сообщение и восстанавливаем исходную клавиатуру
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f'<b>MoscowTransportInformationBot</b> приветствует вас, {call.from_user.username}!\n\nЧтобы получить информацио об интересующем вас маршруте, введите его номер в формате: /903', parse_mode='html', reply_markup=previous_message_markup)



@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text.startswith('/') and message.text not in ['/start', '/help', '/settings']:
        
        # Получение номера маршрута
        input_data = message.text[1:] # удаление символа '/'
        route_short_name = input_data.upper() # перевод символов в верхний регистр
        print(f'!Input data: {input_data}, upper: {route_short_name}')

        # Создание пула соединений
        connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=host,
            user=user,
            password=password,
            database=db_name
        )

        # Получение соединения из пула
        connection = connection_pool.getconn()
        
        try:

            with connection.cursor() as cursor: # Создание курсора (объект с методами для выполнения SQL команд)


                # def getTrip(route_name, route_id_list):
                #     trip_id_list = []

                #     if not isOneRoute:

                #         if len(route_id_list) > 1: # если больше одной вариации маршрута
                #             onlyOneRoute_id.append(False)

                #             for route_turple in route_id_list:
                #                 for route_id in route_turple:
                #                     trip_id_sublist = []

                #                     # Получение кода рейса в направлении 1
                #                     cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = '{route_id}' AND direction_id = '1' ORDER BY trip_id DESC LIMIT 1;")
                #                     trip_id_1 = cursor.fetchone()
                #                     print(f'Результат: trip_id_1 для {route_name} с route_id {route_id}: {trip_id_1}')

                #                     # Получение кода рейса в направлении 0
                #                     cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = '{route_id}' AND direction_id = '0' ORDER BY trip_id DESC LIMIT 1;")
                #                     trip_id_0 = cursor.fetchone()
                #                     print(f'Результат: trip_id_0 для {route_name} с route_id {route_id}: {trip_id_0}')

                #                     # обработка случая, когда у маршрута только одно направление
                #                     if trip_id_1 is None and trip_id_0 is not None:
                #                         trip_id_sublist.append((trip_id_0[0],))
                #                     elif trip_id_1 is not None and trip_id_0 is None:
                #                         trip_id_sublist.append((trip_id_1[0],))
                #                     # Если два направления
                #                     elif trip_id_0 is not None and trip_id_1 is not None:
                #                         trip_id_sublist.append((trip_id_0[0], trip_id_1[0]))
                #                     # Если направлений нет
                #                     elif trip_id_1 is None and trip_id_0 is None:
                #                         print(f'У маршрута {route_short_name} нет рейсов')
                #                         continue
                                                    
                #             trip_id_list.append((trip_id_sublist))
                            
                #         elif len(route_id_list) == 1:  # если одна вариация маршрута
                #             onlyOneRoute_id.append(True)
                #             print(f'Для route_name {route_name} найден один route_id {route_id_list}') 
                                    
                #             # Получение кода рейса в направлении 1
                #             cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = (SELECT route_id FROM routes WHERE route_long_name = '{route_name}') AND direction_id = '1' ORDER BY trip_id DESC LIMIT 1;")
                #             trip_id_1 = cursor.fetchone()
                #             print(f'Результат: trip_id_1 для {route_name}: {trip_id_1}')

                #             # Получение кода рейса в направлении 0
                #             cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = (SELECT route_id FROM routes WHERE route_long_name = '{route_name}') AND direction_id = '0' ORDER BY trip_id DESC LIMIT 1;")
                #             trip_id_0 = cursor.fetchone()
                #             print(f'Результат trip_id_0 для {route_name}: {trip_id_0}')

                #             # обработка случая, когда у маршрута только одно направление
                #             if trip_id_1 is None and trip_id_0 is not None:
                #                 trip_id_list.append((trip_id_0[0],))
                #             elif trip_id_1 is not None and trip_id_0 is None:
                #                 trip_id_list.append((trip_id_1[0],))
                #             # Если два направления
                #             elif trip_id_0 is not None and trip_id_1 is not None: 
                #                  trip_id_list.append((trip_id_0[0], trip_id_1[0]))
                #             # Если направлений нет
                #             elif trip_id_1 is None and trip_id_0 is None:
                #                 print(f'У маршрута {route_short_name} нет рейсов')
                #                 bot.send_message(message.chat.id,f'ℹ️ <b>Для маршрута {route_name} не найдено существующих рейсов!</b>', parse_mode='html')
                #                 exit()
                #                 # создать кнопку для расширенного сканирования функцией tripCheck() (проверка каждого trip_id)
                        
                #     elif isOneRoute:
                #         if len(route_id_list) > 1: # если больше одной вариации маршрута
                #             onlyOneRoute_id.append(False)
                #             trip_id_sublist = []

                #             print(f'Для route_name {route_name} найдено несколько route_id: {route_id_list}')
                #             for route_turple in route_id_list:
                #                 for route_id in route_turple:
                #                     # Получение кода рейса в направлении 1
                #                     cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = '{route_id}' AND direction_id = '1' ORDER BY trip_id DESC LIMIT 1;")
                #                     trip_id_1 = cursor.fetchone()
                #                     print(f'Результат: trip_id_1 для {route_name} с route_id {route_id}: {trip_id_1}')

                #                     # Получение кода рейса в направлении 0
                #                     cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = '{route_id}' AND direction_id = '0' ORDER BY trip_id DESC LIMIT 1;")
                #                     trip_id_0 = cursor.fetchone()
                #                     print(f'Результат: trip_id_0 для {route_name} с route_id {route_id}: {trip_id_0}')

                #                     # обработка случая, когда у маршрута только одно направление
                #                     if trip_id_1 is None and trip_id_0 is not None:
                #                         trip_id_sublist.append((trip_id_0[0],))
                #                     elif trip_id_1 is not None and trip_id_0 is None:
                #                         trip_id_sublist.append((trip_id_1[0],))
                #                     # Если два направления
                #                     elif trip_id_0 is not None and trip_id_1 is not None:
                #                         trip_id_sublist.append((trip_id_0[0], trip_id_1[0]))
                #                     # Если направлений нет
                #                     elif trip_id_1 is None and trip_id_0 is None:
                #                         print(f'У маршрута {route_short_name} нет рейсов')
                #                         continue
                                                        
                #                 trip_id_list.append((trip_id_sublist))

                #         elif len(route_id_list) == 1: # если одна вариация маршрута
                #             onlyOneRoute_id.append(True)

                #             # Получение кода рейса в направлении 1
                #             cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = (SELECT route_id FROM routes WHERE route_short_name = '{route_short_name}') AND direction_id = '1' ORDER BY trip_id DESC LIMIT 1;")
                #             trip_id_1 = cursor.fetchone()
                #             print(f'Результат: trip_id_1: {trip_id_1}')

                #             # Получение кода рейса в направлении 0
                #             cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = (SELECT route_id FROM routes WHERE route_short_name = '{route_short_name}') AND direction_id = '0' ORDER BY trip_id DESC LIMIT 1;")
                #             trip_id_0 = cursor.fetchone()
                #             print(f'Результат: trip_id_0: {trip_id_0}')

                #             # обработка случая, когда у маршрута только одно направление
                #             if trip_id_1 is None and trip_id_0 is not None:
                #                 trip_id_list = [trip_id_0[0]]
                #                 print(f'trip_id_list: {trip_id_list}')
                #                 # return trip_id_list
                #             elif trip_id_1 is not None and trip_id_0 is None:
                #                 trip_id_list = [trip_id_1[0]]
                #                 print(f'trip_id_list: {trip_id_list}')
                #                 # return trip_id_list
                #             # Если два направления
                #             elif trip_id_0 is not None and trip_id_1 is not None:
                #                 trip_id_list = [trip_id_0[0], trip_id_1[0]]
                #                 print(f'trip_id_list: {trip_id_list}')
                #                 # return trip_id_list
                #             # Если направлений нет
                #             elif trip_id_1 is None and trip_id_0 is None:
                #                 print(f'У маршрута {route_short_name} нет рейсов')
                #                 bot.send_message(message.chat.id,f'ℹ️ <b>Для маршрута {route_short_name} не найдено существующих рейсов!</b>', parse_mode='html')
                #                 exit()
                #                         # создать кнопку для расширенного сканирования функцией tripCheck() (проверка каждого trip_id)
                #     return trip_id_list 
                        


                def getTrip(route_id = None, route_name = None, direction_id = None):
                    if not isOneRoute:
                        if route_id is not None:
                            if direction_id == 1:
                                # Получение кода рейса в направлении 1
                                cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = '{route_id}' AND direction_id = '1' ORDER BY trip_id DESC LIMIT 1;")
                                trip_id_1 = cursor.fetchone()
                                print(f'Результат: trip_id_1 для {route_name} с route_id {route_id}: {trip_id_1}')
                                return trip_id_1
                            elif direction_id == 0:
                                # Получение кода рейса в направлении 0
                                cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = '{route_id}' AND direction_id = '0' ORDER BY trip_id DESC LIMIT 1;")
                                trip_id_0 = cursor.fetchone()
                                print(f'Результат: trip_id_0 для {route_name} с route_id {route_id}: {trip_id_0}')
                                return trip_id_0
                        elif route_name is not None:
                            if direction_id == 1:
                                # Получение кода рейса в направлении 1
                                cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = (SELECT route_id FROM routes WHERE route_long_name = '{route_name}') AND direction_id = '1' ORDER BY trip_id DESC LIMIT 1;")
                                trip_id_1 = cursor.fetchone()
                                print(f'Результат: trip_id_1 для {route_name}: {trip_id_1}')
                                return trip_id_1
                            elif direction_id == 0:
                                # Получение кода рейса в направлении 0
                                cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = (SELECT route_id FROM routes WHERE route_long_name = '{route_name}') AND direction_id = '0' ORDER BY trip_id DESC LIMIT 1;")
                                trip_id_0 = cursor.fetchone()
                                print(f'Результат trip_id_0 для {route_name}: {trip_id_0}')
                                return trip_id_0
                    elif isOneRoute:
                        if route_id is not None:
                            if direction_id == 1:
                                # Получение кода рейса в направлении 1
                                cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = '{route_id}' AND direction_id = '1' ORDER BY trip_id DESC LIMIT 1;")
                                trip_id_1 = cursor.fetchone()
                                print(f'Результат: trip_id_1 для route_id {route_id}: {trip_id_1}')
                                return trip_id_1
                            elif direction_id == 0:
                                # Получение кода рейса в направлении 0
                                cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = '{route_id}' AND direction_id = '0' ORDER BY trip_id DESC LIMIT 1;")
                                trip_id_0 = cursor.fetchone()
                                print(f'Результат: trip_id_0 для route_id {route_id}: {trip_id_0}')
                                return trip_id_0
                        elif route_name is not None:
                            if direction_id == 1:
                                # Получение кода рейса в направлении 1
                                cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = (SELECT route_id FROM routes WHERE route_short_name = '{route_name}') AND direction_id = '1' ORDER BY trip_id DESC LIMIT 1;")
                                trip_id_1 = cursor.fetchone()
                                print(f'Результат: trip_id_1: {trip_id_1}')
                                return trip_id_1
                            if direction_id == 0:
                                # Получение кода рейса в направлении 0
                                cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = (SELECT route_id FROM routes WHERE route_short_name = '{route_name}') AND direction_id = '0' ORDER BY trip_id DESC LIMIT 1;")
                                trip_id_0 = cursor.fetchone()
                                print(f'Результат: trip_id_0: {trip_id_0}')
                                return trip_id_0


                def route_idQuery(route_name):
                    global route_id_count
                    cursor.execute(f"SELECT route_id FROM routes WHERE route_long_name = '{route_name}'")
                    route_id_list = cursor.fetchall() # список кортежей из route_id
                    if len(route_id_list) > 1:
                        # bot.send_message(message.chat.id, f'❗️ <b>В базе данных было найдено {len(route_id_list)} вариаций маршрута {route_name}</b>, и мы не можем определить, какой из них верный!', parse_mode='html')
                        route_id_count = len(route_id_list)
                    return route_id_list 
                

                # Функция по получению коллекции trip_id в двух направлениях (1 и 0)
                def tripQuery(route_short_name, route_long_name):  
                    global onlyOneRoute_id 
                    onlyOneRoute_id = []
                    global route_id_list

                    if not isOneRoute: # если проверка в routeToTrip выдала несколько route_long_name
                        trip_id_list = []       # инициализация списка для соханения коллекции trip_id
                    
                        for routes in route_long_name:  # [(название,), (название,)]  
                            for route_name in routes:   # (название,) 
                                
                                # Обработка наличия нескольких route_id для одного маршрута
                                route_id_list = route_idQuery(route_name)

                                if len(route_id_list) > 1: # если больше одной вариации маршрута
                                    onlyOneRoute_id.append(False)

                                    print(f'Для route_name {route_name} найдено несколько route_id: {route_id_list}')

                                    trip_id_sublist = []

                                    for route_turple in route_id_list:
                                        for route_id in route_turple:
                                           
                                            trip_id_1 = getTrip(route_id = route_id, direction_id = 1) # получение кода рейса в направлении 1
                                            trip_id_0 = getTrip(route_id = route_id, direction_id = 0) # получение кода рейса в направлении 0

                                            # обработка случая, когда у маршрута только одно направление
                                            if trip_id_1 is None and trip_id_0 is not None:
                                                trip_id_sublist.append((trip_id_0[0],))
                                            elif trip_id_1 is not None and trip_id_0 is None:
                                                trip_id_sublist.append((trip_id_1[0],))
                                            # Если два направления
                                            elif trip_id_0 is not None and trip_id_1 is not None:
                                                trip_id_sublist.append((trip_id_0[0], trip_id_1[0]))
                                            # Если направлений нет
                                            elif trip_id_1 is None and trip_id_0 is None:
                                                print(f'У маршрута {route_short_name} нет рейсов')
                                                continue
                                                
                                    trip_id_list.append((trip_id_sublist))

                                elif len(route_id_list) == 1:  # если одна вариация маршрута
                                    onlyOneRoute_id.append(True)

                                    print(f'Для route_name {route_name} найден один route_id {route_id_list}') 

                                    trip_id_1 = getTrip(route_name = route_name, direction_id = 1) # получение кода рейса в направлении 1
                                    trip_id_0 = getTrip(route_name = route_name, direction_id = 0) # получение кода рейса в направлении 0

                                    # обработка случая, когда у маршрута только одно направление
                                    if trip_id_1 is None and trip_id_0 is not None:
                                        trip_id_list.append((trip_id_0[0],))
                                    elif trip_id_1 is not None and trip_id_0 is None:
                                        trip_id_list.append((trip_id_1[0],))
                                    # Если два направления
                                    elif trip_id_0 is not None and trip_id_1 is not None: 
                                        trip_id_list.append((trip_id_0[0], trip_id_1[0]))
                                    # Если направлений нет
                                    elif trip_id_1 is None and trip_id_0 is None:
                                        print(f'У маршрута {route_short_name} нет рейсов')
                                        bot.send_message(message.chat.id,f'ℹ️ <b>Для маршрута {route_name} не найдено существующих рейсов!</b>', parse_mode='html')
                                        exit()
                                        # создать кнопку для расширенного сканирования функцией tripCheck() (проверка каждого trip_id)
                                
                        return trip_id_list
                    
                    elif isOneRoute: # если проверка в routeToTrip выдала один route_long_name  
                        trip_id_list = [] # инициализация списка для соханения коллекции trip_id
                        
                        for routes in route_long_name:  # [(название,), (название,)]  
                            for route_name in routes:   # (название,) 
                                # Обработка наличия нескольких route_id для одного маршрута
                                route_id_list = route_idQuery(route_name)

                                if len(route_id_list) > 1: # если больше одной вариации маршрута
                                    onlyOneRoute_id.append(False)
                                    trip_id_sublist = []

                                    print(f'Для route_name {route_name} найдено несколько route_id: {route_id_list}')
                                    for route_turple in route_id_list:
                                        for route_id in route_turple:

                                            trip_id_1 = getTrip(route_id = route_id, direction_id = 1) # получение кода рейса в направлении 1
                                            trip_id_0 = getTrip(route_id = route_id, direction_id = 0) # получение кода рейса в направлении 0

                                            # обработка случая, когда у маршрута только одно направление
                                            if trip_id_1 is None and trip_id_0 is not None:
                                                trip_id_sublist.append((trip_id_0[0],))
                                            elif trip_id_1 is not None and trip_id_0 is None:
                                                trip_id_sublist.append((trip_id_1[0],))
                                            # Если два направления
                                            elif trip_id_0 is not None and trip_id_1 is not None:
                                                trip_id_sublist.append((trip_id_0[0], trip_id_1[0]))
                                            # Если направлений нет
                                            elif trip_id_1 is None and trip_id_0 is None:
                                                print(f'У маршрута {route_short_name} нет рейсов')
                                                continue
                                                        
                                    trip_id_list.append((trip_id_sublist))

                                elif len(route_id_list) == 1: # если одна вариация маршрута
                                    onlyOneRoute_id.append(True)

                                    trip_id_1 = getTrip(route_name = route_short_name, direction_id = 1) # получение кода рейса в направлении 1
                                    trip_id_0 = getTrip(route_name = route_short_name, direction_id = 0) # получение кода рейса в направлении 0

                                    # обработка случая, когда у маршрута только одно направление
                                    if trip_id_1 is None and trip_id_0 is not None:
                                        trip_id_list = [trip_id_0[0]]
                                        print(f'trip_id_list: {trip_id_list}')
                                        # return trip_id_list
                                    elif trip_id_1 is not None and trip_id_0 is None:
                                        trip_id_list = [trip_id_1[0]]
                                        print(f'trip_id_list: {trip_id_list}')
                                        # return trip_id_list
                                    # Если два направления
                                    elif trip_id_0 is not None and trip_id_1 is not None:
                                        trip_id_list = [trip_id_0[0], trip_id_1[0]]
                                        print(f'trip_id_list: {trip_id_list}')
                                        # return trip_id_list
                                    # Если направлений нет
                                    elif trip_id_1 is None and trip_id_0 is None:
                                        print(f'У маршрута {route_short_name} нет рейсов')
                                        bot.send_message(message.chat.id,f'ℹ️ <b>Для маршрута {route_short_name} не найдено существующих рейсов!</b>', parse_mode='html')
                                        exit()
                                        # создать кнопку для расширенного сканирования функцией tripCheck() (проверка каждого trip_id)
                                return trip_id_list




                # Функция проверки кол-ва маршрутов для route_short_name
                def routeToTrip(route_short_name, route_long_name):
                    print('ФУНКЦИЯ routeToTrip -------------------------')

                    global isOneRoute # флаг для сохранения кол-ва маршрутов (True - один маршрут/False - более одного)
                    global routes_info
                    global markup

                    if len(route_long_name) > 1: # если маршрутов больше одного
                        print(f'Для route_short_name {route_short_name} найдено несколько маршрутов: {route_long_name}')
                        isOneRoute = False

                        # Вывод сообщения
                        # markup = types.InlineKeyboardMarkup() # разметка для клавиатуры
                       
                        # routes_info = f'<b>Для маршрута с номером {route_short_name} найдено несколько маршрутов:</b>\n'
                        
                        # for route_name in route_long_name:
                            
                        #     routes_info += f'{route_name[0]}\n'
                        #     button = types.InlineKeyboardButton(f'📍 {route_name[0]}', callback_data=f'{route_name[0]}') # создание кнопки 'О боте'
                        #     markup.add(button)
                        
                        # Получение кодов рейсов 
                        trip_list = []
                        trip_list = tripQuery(route_short_name, route_long_name)
                        print(f'Для {route_short_name} найдены маршруты (trip_list): {trip_list}')

                        return trip_list # список из кортежей с элементами [(trip_id_0, trip_id_1), (trip_id_0, trip_id_1)] или [(trip_id_0), (trip_id_0, trip_id_1)] и наоборот

                    elif len(route_long_name) == 1: # если найден один маршрут
                        print(f'Для route_short_name {route_short_name} найден один маршрут: {route_long_name}')
                        isOneRoute = True

                        # Получение кодов рейсов
                        trip_list = tripQuery(route_short_name, route_long_name)
                        print(f'Для {route_short_name} найдены маршруты (trip_list): {trip_list}')

                        return trip_list # список из элементов [trip_id_0, trip_id_1] или [trip_id_0] и наоборо

                    


                # Функция для отправки запроса на получение остановок для каждого trip_id из кортежа
                def stopsQuery(trip_id):
                        cursor.execute("SELECT fs.stop_sequence, s.stop_name FROM stops s JOIN "+' "flightSchedule" fs ON fs.stop_id = s.stop_id'+f" WHERE fs.trip_id = '{trip_id}' ORDER BY CAST(fs.stop_sequence AS INTEGER);")
                        result = convertResult(cursor.fetchall()) # вызов функции для преобразования результатов
                        return result 
                
                # Метод получения названий остановок и их порядка по trip_id и группировка по порядку следования stop_sequence   
                def getStopsList(trip_id_list):
                    stops_list = []  

                    if isOneRoute == False: # в случае, если маршрутов больше одного (больше 2 рейсов)
                        print(f'(у route_short_name {route_short_name} несколько маршрутов)')
                        
                        for trip_tuple in trip_id_list: #  [('trip_id', 'trip_id'), ('trip_id', 'trip_id')]
                            print(f'Длинна trip_tuple: {len(trip_tuple)}')

                            if isinstance(trip_tuple[0], tuple): # Если больше одной вариации маршрута
                                
                                stops_sublist = []
                                for trip_subtuple in trip_tuple:
                                    # Если есть оба направления 
                                    if len(trip_subtuple) == 2:
                                        stops_0 = stopsQuery(trip_subtuple[0])
                                        stops_1 = stopsQuery(trip_subtuple[1])
                                        stops_sublist.append((stops_0, stops_1)) # (списки остановок добавляются парами для 0 и 1 направления)
                                    # Если есть только одно направление
                                    elif len(trip_subtuple) == 1: 
                                        stops = stopsQuery(trip_subtuple[0])
                                        stops_sublist.append((stops,))
                                stops_list.append(stops_sublist)

                            # Если есть оба направления 
                            elif len(trip_tuple) == 2:
                                stops_0 = stopsQuery(trip_tuple[0])
                                stops_1 = stopsQuery(trip_tuple[1])
                                stops_list.append((stops_0, stops_1)) # (списки остановок добавляются парами для 0 и 1 направления)
                            # Если есть только одно направление
                            elif len(trip_tuple) == 1: 
                                stops = stopsQuery(trip_tuple[0])
                                stops_list.append((stops,))

                        return stops_list 

                    elif isOneRoute == True: # в случае, если один маршрут
                        print(f'(у route_short_name {route_short_name} один маршрут)')
                        stops_sublist = []

                        for trip_id in trip_id_list:

                            # Если внутри кортежи (больше одной вариации маршрута)
                            if isinstance(trip_id[0], tuple):
                                
                                for trip_subtuple in trip_id:
                                    # Если есть оба направления 
                                    if len(trip_subtuple) == 2:
                                        stops_0 = stopsQuery(trip_subtuple[0])
                                        stops_1 = stopsQuery(trip_subtuple[1])
                                        stops_sublist.append((stops_0, stops_1)) # (списки остановок добавляются парами для 0 и 1 направления)
                                    # Если есть только одно направление
                                    elif len(trip_subtuple) == 1: 
                                        stops = stopsQuery(trip_subtuple[0])
                                        stops_sublist.append((stops,))
                                stops_list.append(stops_sublist)

                            else:
                                stops = stopsQuery(trip_id)
                                stops_list.append(stops)

                        return stops_list


            

                # def makeMessage(stops_list, route_long_name):
                #     messageDict = {}

                #     if isOneRoute: # если один route_long_name 

                #         for route in route_long_name:

                #             if isinstance(stops_list[0], tuple): # несколько вариаций маршрута

                #                 for stops_subtyple in stops_tuple:
                #                     for stops in stops_subtyple:
                #                         print(f'len(stops_tuple): {len(stops_tuple)}')
                #                         if len(stops_tuple) > 1:
                #                             print('Сработало условие len(stops_tuple) > 1')
                #                             bot.send_message(message.chat.id, f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops}\n\n', parse_mode='html')
                #                         elif len(stops_tuple) == 1:
                #                             print('Сработало условие  if len(stops_tuple) == 1')
                #                             bot.send_message(message.chat.id, f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops[0]}\n\n', parse_mode='html')
                           
                #             else: # одна вариация маршрута
                #                 route_long_name_LIST = route[0].split(' - ', 1) # разбиение route_long_name для получения начальной и конечной остановки

                #                 if len(stops_list) == 2:
                #                     bot.send_message(message.chat.id, f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок от {route_long_name_LIST[0]} до {route_long_name_LIST[1]}:</b>\n{stops_list[0]}\n\n📍 <b>Список остановок от {route_long_name_LIST[1]} до {route_long_name_LIST[0]}:</b>\n{stops_list[1]}', parse_mode='html')
                #                 elif len(stops_list) == 1:
                #                     bot.send_message(message.chat.id, f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_list[0]}\n\n', parse_mode='html')
                                
                #     if not isOneRoute: # если более одного route_long_name 
                        
                #         for isOneRoute_id, route, stops_tuple in zip(onlyOneRoute_id, route_long_name, stops_list): # флаг, маршрут, кортеж остановок
                #             route_long_name_LIST = route[0].split(' - ', 1)

                #             if isOneRoute_id == True: # одна вариация маршрута
                #                 print('Сработало условие if isOneRoute_id == True')

                #                 if len(stops_tuple) == 2:
                #                     bot.send_message(message.chat.id, f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок от {route_long_name_LIST[0]} до {route_long_name_LIST[1]}:</b>\n{stops_tuple[0]}\n\n📍 <b>Список остановок от {route_long_name_LIST[1]} до {route_long_name_LIST[0]}:</b>\n{stops_tuple[1]}', parse_mode='html')
                #                 elif len(stops_tuple) == 1:
                #                     bot.send_message(message.chat.id, f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_tuple[0]}\n\n', parse_mode='html')

                #             elif isOneRoute_id == False: # несколько вариаций маршрута
                #                 print('Сработало условие isOneRoute_id == False')

                #                 for stops_subtyple in stops_tuple:
                #                     for stops in stops_subtyple:
                #                         print(f'len(stops_tuple): {len(stops_tuple)}')
                #                         if len(stops_tuple) > 1:
                #                             print('Сработало условие len(stops_tuple) > 1')
                #                             bot.send_message(message.chat.id, f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops}\n\n', parse_mode='html')
                #                         elif len(stops_tuple) == 1:
                #                             print('Сработало условие  if len(stops_tuple) == 1')
                #                             bot.send_message(message.chat.id, f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops[0]}\n\n', parse_mode='html')

                def makeMessage(stops_list, route_long_name):
                    global messageDict
                    messageDict = {} # словарь для сохранения информации о маршрутах
                    mess = ''
                    num = 0
                    if isOneRoute: # если один route_long_name 
                        
                        for route in route_long_name:

                            if isinstance(stops_list[0], list): # несколько вариаций маршрута

                                for stops_subtyple in stops_list:
                                    for stops_tuple in stops_subtyple:
                                        print(f'len(stops_tuple): {len(stops_tuple)}')
                                        print(f'stops_tuple: {stops_tuple}')
                                        if len(stops_tuple) > 1: # два направления у вариации
                                            mess = f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_tuple[0]}\n\n📍 <b>Список остановок:</b>\n{stops_tuple[0]}\n\n'
                                            num = num + 1
                                            messageDict[f'route {num} ({route_short_name})'] = mess
                                        elif len(stops_tuple) == 1: # одно направление у вариации
                                            mess = f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_tuple[0]}\n\n'
                                            num = num + 1
                                            messageDict[f'route {num} ({route_short_name})'] = mess
                                printMessage(route_long_name)
                            else: # одна вариация маршрута
                                markup = types.InlineKeyboardMarkup() # разметка для клавиатуры
                                route_long_name_LIST = route[0].split(' - ', 1) # разбиение route_long_name для получения начальной и конечной остановки

                                if len(stops_list) == 2:
                                    bot.send_message(message.chat.id, f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок от {route_long_name_LIST[0]} до {route_long_name_LIST[1]}:</b>\n{stops_list[0]}\n\n📍 <b>Список остановок от {route_long_name_LIST[1]} до {route_long_name_LIST[0]}:</b>\n{stops_list[1]}', parse_mode='html', reply_markup=markup)
                                elif len(stops_list) == 1:
                                    bot.send_message(message.chat.id, f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_list[0]}\n\n', parse_mode='html', reply_markup=markup)
                             
                            # printMessage(route_long_name)
                            
                    elif not isOneRoute: # если более одного route_long_name 
                        # num = 0
                        print(f'stops_list: {stops_list}')
                        for isOneRoute_id, route, stops_tuple in zip(onlyOneRoute_id, route_long_name, stops_list): # флаг, маршрут, кортеж остановок
                            
                            route_long_name_LIST = route[0].split(' - ', 1)

                            if isOneRoute_id == True: # одна вариация маршрута
                                print('Сработало условие if isOneRoute_id == True')

                                if len(stops_tuple) == 2:
                                    mess = f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок от {route_long_name_LIST[0]} до {route_long_name_LIST[1]}:</b>\n{stops_tuple[0]}\n\n📍 <b>Список остановок от {route_long_name_LIST[1]} до {route_long_name_LIST[0]}:</b>\n{stops_tuple[1]}'
                                    # messageDict[route[0]] = mess
                                    num = num + 1
                                    messageDict[f'route {num} ({route_short_name})'] = mess
                                elif len(stops_tuple) == 1:
                                    mess = f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_tuple[0]}\n\n'
                                    # messageDict[route[0]] = mess
                                    num = num + 1
                                    messageDict[f'route {num} ({route_short_name})'] = mess

                            elif isOneRoute_id == False: # несколько вариаций маршрута
                                print('Сработало условие isOneRoute_id == False')
                                  
                                for stops_subtuple in stops_tuple:
                                        print(f'len(stops_tuple): {len(stops_subtuple)}')
                                        if len(stops_subtuple) > 1: # два направления у вариации
                                            print('Сработало условие len(stops_tuple) > 1')
                                            mess = f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_subtuple[0]}\n\n📍 <b>Список остановок:</b>\n{stops_subtuple[1]}'
                                            num = num + 1
                                            messageDict[f'route {num} ({route_short_name})'] = mess
                                        elif len(stops_subtuple) == 1: # одно направление у вариации
                                            print('Сработало условие  if len(stops_tuple) == 1')
                                            mess = f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_subtuple[0]}\n\n'
                                            num = num + 1
                                            messageDict[f'route {num} ({route_short_name})'] = mess
                        printMessage(route_long_name)


                
                
                def printMessage(route_long_name):
                     
                    print(messageDict)
                    num = 0
                    
                    markup = types.InlineKeyboardMarkup() # разметка для клавиатуры

                    if isOneRoute:
                        
                        if route_id_count > 1:
                            # markup = types.InlineKeyboardMarkup() # разметка для клавиатуры
                             
                            for route_name in route_long_name:
                                for number in range(route_id_count):
                                        num = num + 1
                                        button = types.InlineKeyboardButton(f'📍 {route_name[0]} ({num})', callback_data=f'route {num} ({route_short_name})') # создание кнопки 'О боте'
                                        markup.add(button)

                            bot.send_message(message.chat.id, f'❗️ <b>Для маршрута с номером {route_short_name} был найден один маршрут с {route_id_count} вариациями:\n{route_name[0]}</b>, и мы не можем определить, какой из них верный!', parse_mode='html', reply_markup=markup)
                        
                    elif not isOneRoute:
                        routes_info = f'<b>Для маршрута с номером {route_short_name} найдено несколько маршрутов:</b>\n'
                        # markup = types.InlineKeyboardMarkup() # разметка для клавиатуры

                        for route_name in route_long_name: # создание сообщения о найденных маршрутах
                            routes_info += f'{route_name[0]}\n'

                        for isOneRoute_id, route_name in zip(onlyOneRoute_id, route_long_name): 
                            print(isOneRoute_id)
                            if isOneRoute_id == True:
                                num = num + 1
                                button = types.InlineKeyboardButton(f'📍 {route_name[0]}', callback_data=f'route {num} ({route_short_name})') 
                                markup.add(button)
                            if isOneRoute_id == False:
                                bot.send_message(message.chat.id, f'❗️ <b>В базе данных было найдено {route_id_count} вариаций маршрута {route_name[0]}</b>, и мы не можем определить, какой из них верный!', parse_mode='html')
                                for number in range(route_id_count):
                                    num = num + 1
                                    button = types.InlineKeyboardButton(f'📍 {route_name[0]} ({num})', callback_data=f'route {num} ({route_short_name})') 
                                    markup.add(button)
                            
                        bot.send_message(message.chat.id, routes_info, parse_mode='html', reply_markup=markup)

                
                @bot.callback_query_handler(func=lambda call: call.data.startswith('route')) # обработчик нажатия на кнопку
                def route_callback(call):
                    print('Нажата кнопка маршрута!')
                    
                    if call.message: # если нажата кнопка
                        
                        for key in messageDict: 
                            # print(f'for {key} in {messageDict}:')

                            if call.data == key:
                                markupBack = types.InlineKeyboardMarkup() # создание новой разметки
                                back = types.InlineKeyboardButton('Скрыть', callback_data='back') # создание кнопки 'Назад'
                                markupBack.add(back)
                                
                                bot.send_message(call.message.chat.id, messageDict[key], parse_mode='html', reply_markup=markupBack)
                               

                
                def stops(stops_names, input_stop):
                    markup = types.InlineKeyboardMarkup()
                    num = 0
                    global stopsDict
                    stopsDict = {}
                    

                    if len(stops_names) <= 4:
                        # markup = types.InlineKeyboardMarkup() # разметка для клавиатуры

                        for stop_name in stops_names:
                            concrete = stop_name[0][:3]
                            print(f'concrete: {concrete}')
                            
                            num = num + 1
                            button = types.InlineKeyboardButton(f'{stop_name[0]}', callback_data=f'stop {num} ({concrete})') 

                            cursor.execute(f"SELECT geodata_center, stop_id FROM stops WHERE stop_name ILIKE '%{input_stop}%' LIMIT 1 OFFSET {num-1}") 
                            query = cursor.fetchone()
                            stop_geo = query[0]
                            stop_id = query[1]
                            # print(f'stop_geo: {stop_geo}')
                            # print(f'stop_id: {stop_id}')

                            cursor.execute(f'SELECT DISTINCT routes.route_long_name, routes.route_short_name FROM stops JOIN "flightSchedule" ON stops.stop_id = "flightSchedule".stop_id JOIN "flightsRoutes" ON "flightSchedule".trip_id = "flightsRoutes".trip_id JOIN routes ON "flightsRoutes".route_id = routes.route_id WHERE stops.stop_id = ' + f"'{stop_id}';")
                            short_long_info = cursor.fetchall()
                            # print(f'route_shortLong_name: {short_long_info}')
                            stop_info = getGeo(stop_geo, stop_name[0], short_long_info)
                            stopsDict[f'stop {num} ({concrete})'] = stop_info
                            
                            markup.add(button)

                        if len(stops_names) == 1:
                            bot.send_message(message.chat.id, f'ℹ️ <b>По запросу "{input_stop}" найдена {len(stops_names)} остановка:</b>', parse_mode='html', reply_markup=markup)
                        else:
                            bot.send_message(message.chat.id, f'ℹ️ <b>По запросу "{input_stop}" найдены {len(stops_names)} остановки:</b>', parse_mode='html', reply_markup=markup)

                    elif len(stops_names) > 4:
                        # markup = types.InlineKeyboardMarkup() # разметка для клавиатуры

                        global names
                        names = []

                        for stop_name in stops_names:

                            concrete = stop_name[0][:3]

                            print(f'stop_name: {stop_name[0]}')

                            num = num + 1
                            button = types.InlineKeyboardButton(f'{stop_name[0]}', callback_data=f'stop {num} ({concrete})') 
                            stopsDict[f'stop {num} ({concrete})'] = ''

                            names.append(stop_name[0])
                            markup.add(button)
                        print(stopsDict)
                        bot.send_message(message.chat.id, f'ℹ️ <b>По запросу "{input_stop}" найдены {len(stops_names)} остановки:</b>', parse_mode='html', reply_markup=markup)

                    elif len(stops_names) >= 100:
                        bot.send_message(message.chat.id, f'ℹ️ <b>По запросу "{input_stop}" найдено слишком много остановок ({len(stops_names)})!</b>\n\nКонкретизируйте ваш запрос и повторите попытку.', parse_mode='html')
                        
                @bot.callback_query_handler(func=lambda call: call.data.startswith('stop')) 
                def stop_callback(call):
                    print('Нажата кнопка осановки')

                    if call.message: # если нажата кнопка

                        if len(stops_names) <= 4:
                            for key in stopsDict: 
                                if call.data == key:
                                    markupBack = types.InlineKeyboardMarkup() # создание новой разметки
                                    back = types.InlineKeyboardButton('Назад', callback_data='back') # создание кнопки 'Назад'
                                    markupBack.add(back)
                                    bot.send_message(message.chat.id, stopsDict[key], parse_mode='html', reply_markup=markupBack)

                        elif len(stops_names) > 4:

                            for key in stopsDict:
                                if call.data == key:

                                    num = key.split()
                                    num = int(num[1])
                                    # print(num-1)

                                    with connection.cursor() as cursor: 
                                        cursor.execute(f"SELECT geodata_center, stop_id FROM stops WHERE stop_name ILIKE '%{input_stop}%' LIMIT 1 OFFSET {num-1}") 
                                        query = cursor.fetchone()
                                        stop_geo = query[0]
                                        stop_id = query[1]

                                        cursor.execute(f'SELECT DISTINCT routes.route_long_name, routes.route_short_name FROM stops JOIN "flightSchedule" ON stops.stop_id = "flightSchedule".stop_id JOIN "flightsRoutes" ON "flightSchedule".trip_id = "flightsRoutes".trip_id JOIN routes ON "flightsRoutes".route_id = routes.route_id WHERE stops.stop_id = ' + f"'{stop_id}';")
                                        short_long_info = cursor.fetchall()
                                        # print(f'route_shortLong_name: {short_long_info}')
                                        stop_info = getGeo(stop_geo, names[num-1], short_long_info)

                                    markupBack = types.InlineKeyboardMarkup() # создание новой разметки
                                    back = types.InlineKeyboardButton('Скрыть', callback_data='back') # создание кнопки 'Назад'
                                    markupBack.add(back)
                                    bot.send_message(message.chat.id, stop_info, parse_mode='html', reply_markup=markupBack)

                
                
                @bot.callback_query_handler(func=lambda call: call.data == 'back') 
                def back_callback(call):
                    if call.message:
                        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)

                

                
                def route():
                    trip_id_list = routeToTrip(route_short_name, route_long_name)  # получение trip_id по route_short_name
                    # contunue
                    stops_list = getStopsList(trip_id_list) # получение списка остановок по trip_id

                    # print(f'Вот такая у trip_id_list длина: {len(trip_id_list)}')
                    # print(f'Вот такая у stops_list длина: {len(stops_list)}')
                    # print(f'Вот stops_list: {stops_list}')
                    # print(f'onlyOneRoute_id: {onlyOneRoute_id}')

                    # Вывод результатов
                    makeMessage(stops_list, route_long_name)


                    

                                
                def main():
                                   
                    # Получение наименования маршрута по route_short_name
                    def is_route_or_stop():
                        global trip_id_list
                        global route_long_name
                        global stops_names
                        global input_stop #

                        if input_data.startswith('/'): # остановка
                            input_stop = input_data[1:]
                            cursor.execute("SELECT stop_name FROM stops WHERE stop_name ILIKE %s;", ('%{}%'.format(input_stop),))
                            stops_names = cursor.fetchall()
                            print(f'Поиск по stop_name: {stops_names}')

                            # Если ни одна остановка не найдена
                            if stops_names == []:
                                print(f'Для input_data: {route_short_name} ни один маршрут и остановка не найдена!')
                                bot.send_message(message.chat.id, f'<b>По запросу "{input_stop}" ни одна остановка не найдена!</b>\n\nПроверьте запрос и повторите попытку.', parse_mode='html')
                                exit() 
                            # Если остановка найдена
                            elif stops_names != []:
                                stops(stops_names, input_stop)

                        else:
                            cursor.execute("SELECT route_long_name FROM routes WHERE route_short_name = %s;", (route_short_name,))
                            route_long_name = cursor.fetchall()
                            print(f'Поиск по route_long_name: {route_long_name}')
                        
                            # Если ни один маршрут не найден
                            if route_long_name == []:
                                print(f'Для input_data: {route_short_name} ни один маршрут и остановка не найдена!')
                                bot.send_message(message.chat.id, f'<b>По запросу {route_short_name} ни один маршрут не найден!</b>\n\nПроверьте запрос и повторите попытку.', parse_mode='html')
                                exit() 
                            # Если маршрут найден
                            elif route_long_name != []:
                                route()

                    # start
                    is_route_or_stop()

                    

                main()


            



            # # функция проверки trip_id    
                # def tripCheck(trip_id):

                #     isFound = False  # Флаг для отслеживания наличия работающего trip_id

                #     for trip in trip_id:
                       
                #         trip = convertResult(trip)

                #         cursor.execute("SELECT fs.stop_sequence, s.stop_name FROM stops s JOIN"+' "flightSchedule" fs ON fs.stop_id = s.stop_id'+f" WHERE fs.trip_id = '{trip}' ORDER BY CAST(fs.stop_sequence AS INTEGER);")
                #         result = cursor.fetchall()

                #         # Проверка на пустой список
                #         if result != []: # если trip_id не возвращает пустой список
                #             isFound = True
                #             print(result)
                #             break
                        
                #     if isFound == False:
                #         print('Ни один trip_id не возвращает список остановок')

                # # Получение кода рейса в направлении 1
                # cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = (SELECT route_id FROM routes WHERE route_short_name = '{route_short_name}') AND direction_id = '1';")
                # trip_id_1 = tripCheck(cursor.fetchall())

                # # Получение кода рейса в направлении 0
                # cursor.execute("SELECT trip_id FROM"+' "flightsRoutes"'+f" WHERE route_id = (SELECT route_id FROM routes WHERE route_short_name = '{route_short_name}') AND direction_id = '0';")
                # trip_id_0 = tripCheck(cursor.fetchall())
        except psycopg2.InterfaceError as e:
            print(e)
            connection = connection_pool.getconn()
            # cursor = connection.cursor()


        except Exception as ex: 
            print('Error:', ex)
            

        finally:
            if connection:
                connection_pool.putconn(connection)
                print('Connection returned to the connection pool.')



# Функция преобразования результатов         
def convertResult(string):

    if isinstance(string, list): # ((номер, название_остановки), (номер, название_остановки), (номер, название_остановки))
        result = []
        for element in string:
            stop = f'{element[0]}. {element[1]}'
            result.append(stop)

        result_string = '\n'.join(result)  # Объединение элементов списка через перенос строки
        # print(f"Список остановок: {result_string}")

        return result_string
    else:
        print(f'Передаваемый в функцию convertResult аргумент не является списком!\nПередаваемый писок: {string}')



bot.polling(non_stop=True)



