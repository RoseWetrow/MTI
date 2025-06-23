from psycopg2.extras import execute_values             


# Вставка ланных в таблицу батчами 
def db_insert(conn, table_name, batch):
    with conn.cursor() as cur:

        base_query = "INSERT INTO {insert_condition} VALUES %s;"

        if "routes" in table_name:
            query = base_query.replace("{insert_condition}", f"{table_name} (route_id, route_short_name, route_long_name)")

        elif "route_flights" in table_name:
            query = base_query.replace("{insert_condition}", f"{table_name} (route_id, trip_id, direction_id)")

        elif "stops" in table_name:
            query = base_query.replace("{insert_condition}", f"{table_name} (stop_id, stop_name, lat, lng)")

        elif "route_schedule" in table_name:
            query = base_query.replace("{insert_condition}", f"{table_name} (trip_id, stop_id, stop_sequence)")

        execute_values(cur, query, batch)
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