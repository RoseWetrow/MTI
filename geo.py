from geopy.geocoders import Nominatim
import json

def getGeo(stop_geo, stop_name, short_long_info):
    print(f"stop_geo: {stop_geo}")
    data = json.loads(stop_geo)
    # print(data['coordinates'])
    # print(data['coordinates'][0])
    
    geolocator = Nominatim(user_agent='my_bot')
    location = geolocator.reverse(f"{data['coordinates'][1]}, {data['coordinates'][0]}")
    full_address = location.address

    link = f"https://maps.google.com/maps?q={data['coordinates'][1]},{data['coordinates'][0]}"

    stop_info = '<b>ℹ️ На остановке останавливается:</b>\n\n'
    for info_tuple in short_long_info:
        stop_info += f'🔹 Автобус <b>/{info_tuple[1]}</b> по маршруту <b>{info_tuple[0]}</b>\n'
    
    mess = f'<b>📍 Точный адрес остановки {stop_name}:</b>\n\n{full_address}\n\n{link}\n\n{stop_info}'
    # print(mess)

    return mess
    

# def stopInfo(stops_names):

    # if len(stops_names) <= 3:
        

    # if len(stops_names) > 3:
    #     pass
    

    # cursor.execute("SELECT geodata_center FROM stops WHERE stop_name = %s ORDER BY geodata_center desc;", (input_data,))

    # geolocator = Nominatim(user_agent='my_bot')
    # location = geolocator.reverse(f"{55.7089038}, {37.62170311}")
    # location2 = geolocator.reverse(f"{55.70700843}, {37.62090917}")
    # full_address = location.address
    # full_address2 = location2.address
    # print(full_address, full_address2)
    

    # https://maps.google.com/maps?q=55.7089038,37.62170311
