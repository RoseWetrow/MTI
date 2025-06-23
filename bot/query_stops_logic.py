from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.geo import getGeo
from app.keyboards import clear_markup
from bot.state import messageDict


async def stops(stops_count, stops_names_ids, stop_name, conn, message):
    print('Начало метода stops')
    markup = InlineKeyboardMarkup(inline_keyboard=[]) # создание разметки клавиатуры
    num = 0
    messageDict.clear()
    print(f'stops_count = {stops_count}')
    try:
        if stops_count <= 4:

            for stop_name_id in stops_names_ids: #   0 - stop_name | 1 - stop_id
                stop_name_concrete = stop_name_id[0]
                stop_id = int(stop_name_id[1])

                query = await conn.fetch(f"SELECT lat, lng FROM stops WHERE stop_id = {stop_id}")

                stop_lat = query[0][0]
                stop_lng = query[0][1]
                print(f'stop_lat = {stop_lat}')
                print(f'stop_lng = {stop_lng}')

                short_long_info = await conn.fetch(f"""SELECT DISTINCT routes.route_long_name, routes.route_short_name FROM stops JOIN route_schedule ON stops.stop_id = route_schedule.stop_id 
                                                   JOIN route_flights ON route_schedule.trip_id = route_flights.trip_id JOIN routes ON route_flights.route_id = routes.route_id WHERE stops.stop_id = {stop_id};""")
                stop_info = await getGeo(stop_lat, stop_lng, stop_name_concrete, short_long_info) # получаем информацию об остановке в виде текста

                if stops_count == 1:  # если найдена 1 остановка, информация выводится сразу
                    await message.answer(f'ℹ️ <b>По запросу "{stop_name}" найдена остановка {stop_name_concrete}:</b>\n{stop_info}', reply_markup=clear_markup())
                    return
            
                else:   # если найлдено <= 4 остановки, выводим кнопки (информация выводится по нажатию на конкретную кнопку)
                    num += 1
                    button = InlineKeyboardButton(text=f'{stop_name_concrete}', callback_data=f'stop_{num}_({stop_name_concrete})') # aiogram рекомендует snake_case
                    markup.inline_keyboard.append([button])
                    messageDict[f'stop_{num}_({stop_name_concrete})'] = stop_info
                    
            await message.answer(f'ℹ️ <b>По запросу "{stop_name}" остановок найдено {stops_count}:</b>', reply_markup=markup) # вынести
                
        elif 4 < stops_count < 20:
            global names
            names = []

            for stop_name_id in stops_names_ids:
                stop_name_concrete = stop_name_id[0]
                stop_id = stop_name_id[1]

                num = num + 1
                button = InlineKeyboardButton(text=f'{stop_name_concrete}', callback_data=f'stop_{num}_({stop_name_concrete})')
                markup.inline_keyboard.append([button])
                messageDict[f'stop_{num}_({stop_name_concrete})'] = ''
                
                names.append(stop_name_concrete) # формируется массив names из названий остановок (оптимизированно для нагрузки)
            await message.answer(f'ℹ️ <b>По запросу "{stop_name}" остановок найдено {stops_count}:</b>', reply_markup=markup)

        elif stops_count >= 20:
            await message.answer(f'ℹ️ <b>По запросу "{stop_name}" найдено слишком много остановок ({stops_count})!</b>\n\nКонкретизируйте ваш запрос и повторите попытку.')

    except Exception as e:
        print('Ошибка при обработке остановок внутри stops()')
        await message.answer(f'ℹ️ <b>По запросу "{stop_name}" найдено много остановок.</b>\n\nКонкретизируйте ваш запрос и повторите попытку.')
        

async def multi_outstops(conn, stop_name, key):
    try:
        num = key.split()
        num = int(num[1])
        
        query = await conn.fetchrow(f"SELECT lat, lng, stop_id FROM stops WHERE stop_name ILIKE '%{stop_name}%' LIMIT 1 OFFSET {num-1}") 
        stop_lat = query[0]
        stop_lng = query[1]
        stop_id = query[2]

        short_long_info = await conn.fetch(f"""SELECT DISTINCT routes.route_long_name, routes.route_short_name FROM stops 
                                           JOIN route_schedule ON stops.stop_id = route_schedule.stop_id JOIN route_flights ON route_schedule.trip_id = route_flights.trip_id 
                                           JOIN routes ON route_flights.route_id = routes.route_id WHERE stops.stop_id = '{stop_id}';""")
        # print(f'route_shortLong_name: {short_long_info}')
        stop_info = await getGeo(stop_lat, stop_lng, names[num-1], short_long_info)
        return stop_info
    except Exception as e:
        print('Ошибка при обработке остановок внутри multi_outstops()\nНе получилось вернуть координаты или список автобусов для остановки.')