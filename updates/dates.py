from datetime import datetime

# сохранение даты актуализации данных
def save_current_date_to_file():
    today = datetime.now().strftime("%d.%m.%Y")
    with open('./updates/relevance.txt', "w", encoding="utf-8") as f: # /usr/bin/MTI/updates/relevance.txt
        f.write(today)
# выгрузка даты актуализации данных
def read_last_date_from_file():
    try:
        with open('./updates/relevance.txt', "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None
