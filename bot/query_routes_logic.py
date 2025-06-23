from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.state import messageDict


async def getTrip(route_id = None, route_name = None, direction_id = None, conn = None):
    print('Функция getTrip ---------------------------------- ')  
    try:
        # Базовый запрос с проверкой существования в route_schedule
        base_query = """
            SELECT rf.trip_id 
            FROM route_flights rf
            WHERE rf.direction_id = $1
            AND EXISTS (
                SELECT 1 FROM route_schedule rs 
                WHERE rs.trip_id = rf.trip_id
            )
            {route_condition}
            ORDER BY rf.trip_id DESC 
            LIMIT 1
        """
        
        if route_id:       # несколько route_id для одного маршрута
            query = base_query.replace("{route_condition}", "AND rf.route_id = $2")
            params = (direction_id, route_id)
        elif route_name:   # один route_id для одного маршрута
            if isOneRoute: # маршрут один
                query = base_query.replace("{route_condition}", "AND rf.route_id = (SELECT route_id FROM routes WHERE route_short_name = $2 LIMIT 1)")
            else:          # маршрутов больше одного 
                query = base_query.replace("{route_condition}", "AND rf.route_id = (SELECT route_id FROM routes WHERE route_long_name = $2 LIMIT 1)")
            params = (direction_id, route_name)
        
        print(f'query = {query}')
        print(f'params = {params}')
        trip_record = await conn.fetchrow(query, *params) # выполняем запрос
        print(f'trip_record = {trip_record}')
        
        if not trip_record:
            print(f"Не найден действительный trip_id для route_id={route_id}, route_name={route_name}, direction={direction_id}")
        elif trip_record is not None:
            print(f"Найден trip_id: {trip_record['trip_id']} для direction {direction_id}")
            return trip_record
    
    except Exception as e:
        print(f"Ошибка в getTrip: {str(e)}")


async def route_idQuery(route_name, conn):
    global route_id_count
    route_id_list = await conn.fetch(f"SELECT route_id FROM routes WHERE route_long_name = '{route_name}'")
    if len(route_id_list) > 1:
        # await message.answer(message.chat.id, f'❗️ <b>В базе данных было найдено {len(route_id_list)} вариаций маршрута {route_name}</b>, и мы не можем определить, какой из них верный!', parse_mode='html')
        route_id_count = len(route_id_list)
    return route_id_list 


# Функция по получению коллекции trip_id в двух направлениях (1 и 0)
async def tripQuery(route_short_name, route_long_name, conn, message):  
    global onlyOneRoute_id 
    onlyOneRoute_id = []
    global route_id_list

    if not isOneRoute: # если проверка в routeToTrip выдала несколько route_long_name
        trip_id_list = []       # инициализация списка для соханения коллекции trip_id
    
        for routes in route_long_name:  # [(название,), (название,)]  
            for route_name in routes:   # (название,) 
                
                # Обработка наличия нескольких route_id для одного маршрута
                route_id_list = await route_idQuery(route_name, conn)

                if len(route_id_list) > 1: # если больше одной вариации маршрута
                    onlyOneRoute_id.append(False)

                    print(f'Для route_name {route_name} найдено несколько route_id: {route_id_list}')

                    trip_id_sublist = []

                    for route_turple in route_id_list:
                        for route_id in route_turple:
                            
                            trip_id_1 = await getTrip(route_id = route_id, direction_id = 1, conn = conn) # получение кода рейса в направлении 1
                            trip_id_0 = await getTrip(route_id = route_id, direction_id = 0, conn = conn) # получение кода рейса в направлении 0

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

                    trip_id_1 = await getTrip(route_name = route_name, direction_id = 1, conn = conn) # получение кода рейса в направлении 1
                    trip_id_0 = await getTrip(route_name = route_name, direction_id = 0, conn = conn) # получение кода рейса в направлении 0

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
                        await message.answer(f'ℹ️ <b>Для маршрута {route_name} не найдено существующих рейсов!</b>')
                        return
                        # создать кнопку для расширенного сканирования функцией tripCheck() (проверка каждого trip_id)
                
        return trip_id_list
    
    elif isOneRoute: # если проверка в routeToTrip выдала один route_long_name  
        trip_id_list = [] # инициализация списка для соханения коллекции trip_id
        
        for routes in route_long_name:  # [(название,), (название,)]  
            for route_name in routes:   # (название,) 
                # Обработка наличия нескольких route_id для одного маршрута
                route_id_list = await route_idQuery(route_name, conn)

                if len(route_id_list) > 1: # если больше одной вариации маршрута
                    onlyOneRoute_id.append(False)
                    trip_id_sublist = []

                    print(f'Для route_name {route_name} найдено несколько route_id: {route_id_list}')
                    for route_turple in route_id_list:
                        for route_id in route_turple:

                            trip_id_1 = await getTrip(route_id = route_id, direction_id = 1, conn=conn) # получение кода рейса в направлении 1
                            trip_id_0 = await getTrip(route_id = route_id, direction_id = 0, conn = conn) # получение кода рейса в направлении 0

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

                    trip_id_1 = await getTrip(route_name = route_short_name, direction_id = 1, conn = conn) # получение кода рейса в направлении 1
                    trip_id_0 = await getTrip(route_name = route_short_name, direction_id = 0, conn = conn) # получение кода рейса в направлении 0

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
                        await message.answer(message.chat.id,f'ℹ️ <b>Для маршрута {route_short_name} не найдено существующих рейсов!</b>', parse_mode='html')
                        exit()
                        # создать кнопку для расширенного сканирования функцией tripCheck() (проверка каждого trip_id)
                return trip_id_list


# Функция проверки кол-ва маршрутов для route_short_name
async def routeToTrip(route_short_name, route_long_name, conn, message):
    print('ФУНКЦИЯ routeToTrip -------------------------')

    global isOneRoute # флаг для сохранения кол-ва маршрутов (True - один маршрут/False - более одного)
    global routes_info

    if len(route_long_name) > 1: # если маршрутов больше одного
        print(f'Для route_short_name {route_short_name} найдено несколько маршрутов: {route_long_name}')
        isOneRoute = False

        # Получение кодов рейсов 
        trip_list = []
        trip_list = await tripQuery(route_short_name, route_long_name, conn, message)
        print(f'Для {route_short_name} найдены маршруты (trip_list): {trip_list}')

        return trip_list # список из кортежей с элементами [(trip_id_0, trip_id_1), (trip_id_0, trip_id_1)] или [(trip_id_0), (trip_id_0, trip_id_1)] и наоборот

    elif len(route_long_name) == 1: # если найден один маршрут
        print(f'Для route_short_name {route_short_name} найден один маршрут: {route_long_name}')
        isOneRoute = True

        # Получение кодов рейсов
        trip_list = await tripQuery(route_short_name, route_long_name, conn, message)
        print(f'Для {route_short_name} найдены маршруты (trip_list): {trip_list}')

        return trip_list # список из элементов [trip_id_0, trip_id_1] или [trip_id_0] и наоборо

    
# Функция для отправки запроса на получение остановок для каждого trip_id из кортежа
async def stopsQuery(trip_id, conn):
        print({trip_id})
        query = await conn.fetch(f"SELECT fs.stop_sequence, s.stop_name FROM stops s JOIN route_schedule fs ON fs.stop_id = s.stop_id WHERE fs.trip_id = '{trip_id}' ORDER BY fs.stop_sequence;")
        print(query)
        result = convertResult(query) # вызов функции для преобразования результатов
        return result 


# Метод получения названий остановок и их порядка по trip_id и группировка по порядку следования stop_sequence   
async def getStopsList(route_short_name, trip_id_list, conn):
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
                        stops_0 = await stopsQuery(trip_subtuple[0], conn)
                        stops_1 = await stopsQuery(trip_subtuple[1], conn)
                        stops_sublist.append((stops_0, stops_1), conn) # (списки остановок добавляются парами для 0 и 1 направления)
                    # Если есть только одно направление
                    elif len(trip_subtuple) == 1: 
                        stops = await stopsQuery(trip_subtuple[0], conn)
                        stops_sublist.append((stops,))
                stops_list.append(stops_sublist)

            # Если есть оба направления 
            elif len(trip_tuple) == 2:
                stops_0 = await stopsQuery(trip_tuple[0], conn)
                stops_1 = await stopsQuery(trip_tuple[1], conn)
                stops_list.append((stops_0, stops_1)) # (списки остановок добавляются парами для 0 и 1 направления)
            # Если есть только одно направление
            elif len(trip_tuple) == 1: 
                stops = await stopsQuery(trip_tuple[0], conn)
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
                        stops_0 = await stopsQuery(trip_subtuple[0], conn)
                        stops_1 = await stopsQuery(trip_subtuple[1], conn)
                        stops_sublist.append((stops_0, stops_1)) # (списки остановок добавляются парами для 0 и 1 направления)
                    # Если есть только одно направление
                    elif len(trip_subtuple) == 1: 
                        stops = await stopsQuery(trip_subtuple[0], conn)
                        stops_sublist.append((stops,))
                stops_list.append(stops_sublist)

            else:
                stops = await stopsQuery(trip_id, conn)
                stops_list.append(stops)

        return stops_list


async def makeMessage(route_short_name, stops_list, route_long_name, message):
    messageDict.clear()
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
                            messageDict[f'route_{num}_({route_short_name})'] = mess
                        elif len(stops_tuple) == 1: # одно направление у вариации
                            mess = f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_tuple[0]}\n\n'
                            num = num + 1
                            messageDict[f'route_{num}_({route_short_name})'] = mess
                await printMessage(route_short_name, route_long_name, message)
            else: # одна вариация маршрута
                markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Скрыть", callback_data="clear")]])
                route_long_name_LIST = route[0].split(' - ', 1) # разбиение route_long_name для получения начальной и конечной остановки

                if len(stops_list) == 2:
                    await message.answer(f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок от {route_long_name_LIST[0]} до {route_long_name_LIST[1]}:</b>\n{stops_list[0]}\n\n📍 <b>Список остановок от {route_long_name_LIST[1]} до {route_long_name_LIST[0]}:</b>\n{stops_list[1]}', reply_markup=markup)
                elif len(stops_list) == 1:
                    await message.answer(f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_list[0]}\n\n', reply_markup=markup)
                
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
                    messageDict[f'route_{num}_({route_short_name})'] = mess
                elif len(stops_tuple) == 1:
                    mess = f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_tuple[0]}\n\n'
                    # messageDict[route[0]] = mess
                    num = num + 1
                    messageDict[f'route_{num}_({route_short_name})'] = mess

            elif isOneRoute_id == False: # несколько вариаций маршрута
                print('Сработало условие isOneRoute_id == False')
                    
                for stops_subtuple in stops_tuple:
                        print(f'len(stops_tuple): {len(stops_subtuple)}')
                        if len(stops_subtuple) > 1: # два направления у вариации
                            print('Сработало условие len(stops_tuple) > 1')
                            mess = f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_subtuple[0]}\n\n📍 <b>Список остановок:</b>\n{stops_subtuple[1]}'
                            num = num + 1
                            messageDict[f'route_{num}_({route_short_name})'] = mess
                        elif len(stops_subtuple) == 1: # одно направление у вариации
                            print('Сработало условие  if len(stops_tuple) == 1')
                            mess = f'ℹ️ <b>Информация о маршруте {route_short_name}</b>:\n\n<b>📜 Наименование маршрута</b>: {route[0]}.\n\n📍 <b>Список остановок:</b>\n{stops_subtuple[0]}\n\n'
                            num = num + 1
                            messageDict[f'route_{num}_({route_short_name})'] = mess
        await printMessage(route_short_name, route_long_name, message)


async def printMessage(route_short_name, route_long_name, message):

    markup = InlineKeyboardMarkup(inline_keyboard=[])
    num = 0

    if isOneRoute:
        if route_id_count > 1:
            for route_name in route_long_name:
                for number in range(route_id_count):
                    num += 1
                    button = InlineKeyboardButton(text=f'📍 {route_name[0]} ({num})', callback_data=f'route_{num}_({route_short_name})') # aiogram рекомендует snake_case
                    markup.inline_keyboard.append([button])

            await message.answer(f'❗️ <b>Для маршрута с номером {route_short_name} был найден один маршрут с {route_id_count} вариациями:\n{route_name[0]}</b>, и мы не можем определить, какой из них верный!',reply_markup=markup)

    elif not isOneRoute:
        routes_info = f'<b>Для маршрута с номером {route_short_name} найдено несколько маршрутов:</b>\n'
        
        for route_name in route_long_name:
            routes_info += f'{route_name[0]}\n'

        for is_one_id, route_name in zip(onlyOneRoute_id, route_long_name):
            if is_one_id:
                num += 1
                button = InlineKeyboardButton(
                    text=f'📍 {route_name[0]}',
                    callback_data=f'route_{num}_({route_short_name})'
                )
                markup.inline_keyboard.append([button])
            else:
                await message.answer(
                    f'❗️ <b>В базе данных было найдено {route_id_count} вариаций маршрута {route_name[0]}</b>, и мы не можем определить, какой из них верный!'
                )
                for number in range(route_id_count):
                    num += 1
                    button = InlineKeyboardButton(
                        text=f'📍 {route_name[0]} ({num})',
                        callback_data=f'route_{num}_({route_short_name})'
                    )
                    markup.inline_keyboard.append([button])

        await message.answer(routes_info, reply_markup=markup)
            

async def routes(route_short_name, route_long_name, conn, message):
    trip_id_list = await routeToTrip(route_short_name, route_long_name, conn, message)  # получение trip_id по route_short_name

    stops_list = await getStopsList(route_short_name, trip_id_list, conn) # получение списка остановок по trip_id
    
    await makeMessage(route_short_name, stops_list, route_long_name, message) # Вывод результатов


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