import os
import time
import asyncio
import aiohttp
import psycopg2
from dotenv import load_dotenv
from api_work import get_remote_versions, get_dataset_count, get_dataset_data 
from db_work import get_local_versions, update_local_versions, db_insert, temp_table_actions
from dates import save_current_date_to_file


# Загрузка переменных окружения /usr/bin/папка/.env
load_dotenv(".env")
MOS_KEY = os.environ.get("MOS_KEY")
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")
DB_PORT = os.environ.get("DB_PORT")
DATASETS = {
    "routes": "60664",
    "route_flights": "60665",
    "route_schedule": "60661",
    "stops": "60662"
}


# Загрузка одной страницы (batch) и вставка в базу
async def fetch_page(client, conn, dataset_id, dataset_name, skip, top=1000):
    while True:
        try:
            data = await get_dataset_data(MOS_KEY, client, dataset_id, top, skip) # получаем кол-во записей в актуальном датасете по id
        except Exception as e:
            print(f"Ошибка при получении данных {dataset_id} {dataset_name}: {e}. Повтор...")
            await asyncio.sleep(5)
            continue

        if not data:
            print(f"Пустой ответ повторная попытка...")
            await asyncio.sleep(3)
            continue

        batch = []
        for item in data:
            fields = item["Cells"]
            try:
                if "routes" in dataset_name:
                    batch.append((
                        fields["route_id"],
                        fields["route_short_name"],
                        fields["route_long_name"]
                    ))
                elif "route_flights" in dataset_name:
                    batch.append((
                        fields["route_id"],
                        fields["trip_id"],
                        fields["direction_id"]
                    ))
                elif "stops" in dataset_name:
                    batch.append((
                        fields["stop_id"],
                        fields["stop_name"],
                        fields["geoData"]["coordinates"][1],  # долгота
                        fields["geoData"]["coordinates"][0]   # широта
                    ))
                elif "route_schedule" in dataset_name:
                    batch.append((
                        fields["trip_id"],
                        fields["stop_id"],
                        fields["stop_sequence"]
                    ))
            except Exception as e:
                print(f"Ошибка при подготовке данных {dataset_id} {dataset_name}: {e}")
                await asyncio.sleep(3)
                continue

        if batch:
            try:
                db_insert(conn, dataset_name, batch)

            except Exception as e:
                print(f"Ошибка при вставке batch в {dataset_id} {dataset_name}: {e}")
                await asyncio.sleep(5)
                continue

        return len(batch)  # возвращаем количество записей


# Параллельная загрузка всех страниц датасета
async def fetch_insert_datasets(conn, dataset_id, dataset_name):
    finished = False
    top = 1000
    skip = 0
    max_parallel_tasks = 10  # кол-во параллельных запросов
    semaphore = asyncio.Semaphore(max_parallel_tasks)

    async with aiohttp.ClientSession() as client:
        try:
            total_count = await get_dataset_count(MOS_KEY, client, dataset_id)   # получаем общее количество строк в датасете
            print(f"Всего строк в датасете {dataset_name}: {total_count}")

            temp_table_actions('createmp', conn, dataset_name) # создаем новую таблицу

            while not finished:
                tasks = []
                remaining = total_count - skip          # рассчет кол-ва задач, чтоб не выйти за total_count
                tasks_count = min(max_parallel_tasks, (remaining + top - 1) // top)  # округление вверх без потери остатков (берем 10 до того, как будет меньше)

                for i in range(tasks_count):            # формируем пачку из tasks_count задач (max_parallel_tasks или меньше)
                    current_skip = skip + i * top
                    current_top = min(top, total_count - current_skip)  # ограничиваем по количеству оставшихся строк для последнего запроса 

                    async def limited_fetch(skip_val=current_skip, top_val=current_top):
                        async with semaphore:           # каждую задачу оборачиваем в семафор для контроля
                            return await fetch_page(client, conn, dataset_id, f'{dataset_name}_temp', skip_val, top=top_val)

                    tasks.append(limited_fetch())       # добавляем задачу в список

                if not tasks:                           # все задачи были отброшены, т.к. skip >= total_count
                    break                               # завершить цикл

                results = await asyncio.gather(*tasks)  # ждем все параллельно
                total_received = sum(results)           # считаем, сколько всего строк пришло

                if total_received == 0:                 # пришло 0, но skip ещё не дошёл до конца (возможно ошибка API)
                    if skip < total_count:
                        print(f"Получено 0 строк, но skip={skip} < total_count={total_count}. Возможно ошибка API.")
                    finished = True                     # заканчиваем процесс, т.к. больше данных нет

                skip += tasks_count * top               # смещение указателя на следующую пачку из n задач

        except Exception as e:
            print(f"Ошибка при работе с пачками в методе fetch_insert_datasets: {e}")

    print(f"Завершение загрузки данных для {dataset_name}")


# Основной процесс
async def checkingForUpdates():
    while True:
        start_time = time.perf_counter()
        try:
            conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME, port=DB_PORT)
            
            local_versions = get_local_versions(conn)
            remote_versions = await get_remote_versions(MOS_KEY, DATASETS)

            for_updates = []

            for name, remote_version in remote_versions.items():
                local_version = local_versions.get(name)

                if local_version != remote_version:
                    print(f"Локальная версия {local_version} набора {name} устарела, новая -> {remote_version}\nОбновление данных...")
                    dataset_id = DATASETS[name]
                    await fetch_insert_datasets(conn, dataset_id, name)

                    for_updates.append((name, remote_version))
           
            if for_updates:
                for updates in for_updates:
                    update_local_versions(conn, for_updates)       # обновление локальной версии датасета
                    temp_table_actions('swap', conn, updates[0])   # переименование временных таблиц в основные

                end_time = time.perf_counter()
                print(f"Обновление завершено за {end_time - start_time:.2f} секунд.")
                save_current_date_to_file()                        # сохранение текущей даты актуализации
            else:
                print("Данные актуальны. Обновление не требуется.")
        except Exception as e:
            print(f"Ошибка в методе checkingForUpdates: {e}")
            await asyncio.sleep(60) # повтор при ошибке
        finally:
            if conn:
                conn.close()
            await asyncio.sleep(30 * 24 * 60 * 60)  # повтор через 30 суток


# Запуск
asyncio.run(checkingForUpdates())