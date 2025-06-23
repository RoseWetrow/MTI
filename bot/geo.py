import os
import asyncio
import aiohttp
from dotenv import load_dotenv


load_dotenv(".env")
YANDEX_KEY = os.environ.get("YANDEX_KEY")

async def getGeo(stop_lat, stop_lng, stop_name, short_long_info):
    print(f'Метод getGeo!')

    url = f'https://geocode-maps.yandex.ru/1.x/?apikey={YANDEX_KEY}&geocode={stop_lng},{stop_lat}&format=json'
    print(url)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()
                full_address = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
                print(full_address)

    except Exception as e:
        print(f"Ошибка при получении адреса остановки по координатам. Повтор...")
        await asyncio.sleep(5)

    # link = f"https://maps.google.com/maps?q={stop_lat},{stop_lng}"
    link = f"https://yandex.ru/maps/213/moscow/?ll={stop_lng}%2C{stop_lat}&mode=whatshere&whatshere%5Bpoint%5D={stop_lng}%2C{stop_lat}&whatshere%5Bzoom%5D=16.21&z=16"

    stop_info = '<b>ℹ️ На остановке останавливается:</b>\n\n'
    for info_tuple in short_long_info:
        stop_info += f'🔹 Автобус <b>/{info_tuple[1]}</b> по маршруту <b>{info_tuple[0]}</b>\n'
    
    mess = f'<b>📍 Точный адрес остановки {stop_name}:</b>\n\n{full_address}\n\n{link}\n\n{stop_info}'

    return mess