from psycopg2.extras import execute_values             


# Вставка ланных в таблицу батчами 
def db_insert(conn, table_name, batch):
    with conn.cursor() as cur:
        if "routes" in table_name:
            execute_values(cur, f"""INSERT INTO {table_name} (route_id, route_short_name, route_long_name) VALUES %s;""", batch)

        elif "route_flights" in table_name:
            execute_values(cur, f"""INSERT INTO {table_name} (route_id, trip_id, direction_id) VALUES %s;""", batch)

        elif "stops" in table_name:
            execute_values(cur, f"""INSERT INTO {table_name} (stop_id, stop_name, lat, lng) VALUES %s;""", batch)

        elif "route_schedule" in table_name:
            execute_values(cur, f"""INSERT INTO {table_name} (trip_id, stop_id, stop_sequence) VALUES %s;""", batch)

    conn.commit()


# Замена основной таблицы на временную / создание временной таблицы
def temp_table_actions(action, conn, dataset_name):

    temp_name = f"{dataset_name}_temp"
    with conn.cursor() as cur:

        if action == 'swap':
            try:
                cur.execute(f"DROP TABLE IF EXISTS {dataset_name};")              # удаление старой таблицы
                cur.execute(f"ALTER TABLE {temp_name} RENAME TO {dataset_name};") # переименование временной
                conn.commit()
                print(f"Таблица {dataset_name} успешно обновлена.")
            except Exception as e:
                print(f"Ошибка при замене временной таблицы {temp_name} на основную: {e}")
                conn.rollback()

        elif action == 'createmp': # создание временной таблицы с такой же структурой
            try:
                cur.execute(f"DROP TABLE IF EXISTS {temp_name};")
                if dataset_name == "routes":
                    cur.execute(f"""
                        CREATE TABLE {temp_name} (
                            route_id varchar NOT NULL,
                            route_short_name varchar NOT NULL,
                            route_long_name varchar NOT NULL,
                            PRIMARY KEY (route_id)
                        );""")
                elif dataset_name == "route_flights":
                    cur.execute(f"""
                        CREATE TABLE {temp_name} (
                            route_id varchar NOT NULL,
                            trip_id varchar NOT NULL,
                            direction_id int4 NOT NULL,
                            PRIMARY KEY (trip_id)
                        );""")
                elif dataset_name == "stops":
                    cur.execute(f"""
                        CREATE TABLE {temp_name} (
                            stop_id int4 NOT NULL,
                            stop_name varchar NOT NULL,
                            lat float8 NULL,
                            lng float8 NULL,
                            PRIMARY KEY (stop_id)
                        );""")
                elif dataset_name == "route_schedule":
                    cur.execute(f"""
                        CREATE TABLE {temp_name} (
                            trip_id varchar NOT NULL,
                            stop_id int4 NOT NULL,
                            stop_sequence int4 NOT NULL,
                            PRIMARY KEY (trip_id, stop_sequence)
                        );""")
                conn.commit()
                print(f"Временная таблица {temp_name} создана.")
            except Exception as e:
                print(f"Ошибка при создании временной таблицы {temp_name}: {e}")
                conn.rollback()


# Получение локальных версий из БД
def get_local_versions(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT dataset_name, release_number FROM dataset_versions;")
        rows = cur.fetchall()
        return {row[0]: row[1] for row in rows}
    

def update_local_versions(conn, for_updates):
    with conn.cursor() as cur:
        for name, new_version in for_updates:
            cur.execute("""
                UPDATE dataset_versions SET release_number = %s WHERE dataset_name = %s;
            """, (new_version, name))
    conn.commit()
    conn.close()


############################################### Методы функционала для бота


def get_stop_info():
    pass



# conn = await asyncpg.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, port=DB_PORT)
# conn = await asyncpg.create_conn(dsn=f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}") # создаем пул соединений с БД (передаем в каждую функцию пул, в нем открываем отдельное соединение)












































# # Асинхронная вставка батчами
# async def db_insert(pool: asyncpg.Pool, table_name: str, batch: list[tuple]):
#     async with pool.acquire() as conn:
#         if "routes" in table_name:
#             await conn.copy_records_to_table(table_name, records=batch, columns=["route_id", "route_short_name", "route_long_name"])

#         elif "route_flights" in table_name:
#             await conn.copy_records_to_table(table_name, records=batch, columns=["route_id", "trip_id", "direction_id"])

#         elif "stops" in table_name:
#             await conn.copy_records_to_table(table_name, records=batch, columns=["stop_id", "stop_name", "lat", "lng"])

#         elif "route_schedule" in table_name:
#             await conn.copy_records_to_table(table_name, records=batch, columns=["trip_id", "stop_id", "stop_sequence"])


# # Асинхронная работа с временными таблицами
# async def temp_table_actions(action: str, pool: asyncpg.Pool, dataset_name: str):
#     temp_name = f"{dataset_name}_temp"

#     async with pool.acquire() as conn:

#         if action == 'swap':
#             try:
#                 await conn.execute(f"DROP TABLE IF EXISTS {dataset_name};")
#                 await conn.execute(f"ALTER TABLE {temp_name} RENAME TO {dataset_name};")
#                 print(f"Таблица {dataset_name} успешно обновлена.")
#             except Exception as e:
#                 print(f"Ошибка при замене временной таблицы {temp_name} на {dataset_name}: {e}")

#         elif action == 'rename':
#             try:
#                 await conn.execute(f"DROP TABLE IF EXISTS {temp_name};")

#                 if dataset_name == "routes":
#                     await conn.execute(f"""
#                         CREATE TABLE {temp_name} (
#                             route_id varchar NOT NULL,
#                             route_short_name varchar NOT NULL,
#                             route_long_name varchar NOT NULL,
#                             PRIMARY KEY (route_id)
#                         );
#                     """)
#                 elif dataset_name == "route_flights":
#                     await conn.execute(f"""
#                         CREATE TABLE {temp_name} (
#                             route_id varchar NOT NULL,
#                             trip_id varchar NOT NULL,
#                             direction_id int4 NOT NULL,
#                             PRIMARY KEY (trip_id)
#                         );
#                     """)
#                 elif dataset_name == "stops":
#                     await conn.execute(f"""
#                         CREATE TABLE {temp_name} (
#                             stop_id int4 NOT NULL,
#                             stop_name varchar NOT NULL,
#                             lat float8 NULL,
#                             lng float8 NULL,
#                             PRIMARY KEY (stop_id)
#                         );
#                     """)
#                 elif dataset_name == "route_schedule":
#                     await conn.execute(f"""
#                         CREATE TABLE {temp_name} (
#                             trip_id varchar NOT NULL,
#                             stop_id int4 NOT NULL,
#                             stop_sequence int4 NOT NULL,
#                             PRIMARY KEY (trip_id, stop_sequence)
#                         );
#                     """)
#                 print(f"Временная таблица {temp_name} создана.")
#             except Exception as e:
#                 print(f"Ошибка при создании временной таблицы {temp_name}: {e}")


# # Получение локальных версий
# async def get_local_versions(pool: asyncpg.Pool):
#     async with pool.acquire() as conn:
#         rows = await conn.fetch("SELECT dataset_name, release_number FROM dataset_versions;")
#         return {row['dataset_name']: row['release_number'] for row in rows}


# # Обновление локальных версий
# async def update_local_versions(pool: asyncpg.Pool, for_updates):
#     async with pool.acquire() as conn:
#         for name, new_version in for_updates:
#             await conn.execute("""
#                 UPDATE dataset_versions
#                 SET release_number = $1
#                 WHERE dataset_name = $2;
#             """, new_version, name)