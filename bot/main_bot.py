import asyncio
import asyncpg
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # корень проекта для реализации импорта
from dotenv import load_dotenv
from updates.dates import read_last_date_from_file
from app.keyboards import start_markup, about_markup, clear_markup
from bot.state import messageDict
from query_routes_logic import routes
from query_stops_logic import stops, multi_outstops


# Загрузка переменных окружения
load_dotenv(".env")
TG_TOKEN = os.environ.get("TG_TOKEN")
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")
DB_PORT = os.environ.get("DB_PORT")

# Создание бота и диспетчера
bot = Bot(token=TG_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

try:
    # Устанавливаем соединение с PostgreSQL
    async def create_pool():
        return await asyncpg.create_pool(user=DB_USER, password=DB_PASS, database=DB_NAME, host=DB_HOST, port=DB_PORT)


    # Приветственное сообщение
    @dp.message(CommandStart())
    async def start_handler(message: Message):
        relevance_date = read_last_date_from_file()
        await message.answer(f"<b>Moscow Transport Information</b> приветствует вас, {message.from_user.username}!\n\nЯ бот, который поможет узнать остановки маршрута или маршрут по остановке.\n"
                            "Введите команду в формате:\n/903 — чтобы получить список остановок для маршрута\n"
                            "//политехнический университет — чтобы найти маршруты, проходящие через остановку\n\n"
                            f"(данные актуальны на {relevance_date})", reply_markup=start_markup())


    # Обработка нажатия "О боте"
    @dp.callback_query(F.data == "about")
    async def about_callback(callback: CallbackQuery):
        await callback.message.edit_text(
            "ℹ️ <b>MTI (Moscow Transport Information Bot)</b> — бот, предоставляющий информацию о любом, интересующем вас маршруте/остановке, в удобном формате.\n\n"
            "Здесь по номеру общественного транспорта вы можете узнать:\n"
            "• наименование маршрута\n"
            "• список остановок по пути следования\n"
            "• информацию об интересующей вас остановке (адрес, список маршрутов, координаты)\n\n"
            "📊 Бот работает на информации с портала открытых данных Правительства Москвы. База данных содержит более 6,5 миллионов записей и постоянно актуализируется.\n\n"
            "Если у вас есть вопросы или предложения по работе с ботом, пишите @RsdtUub",
            reply_markup=about_markup()
        )
        await callback.answer()  # обязательно, чтобы не было "loading" у кнопки


    # Обработка нажатия "Назад"
    @dp.callback_query(F.data == "about_back")
    async def about_back_callback(callback: CallbackQuery):
        await callback.message.edit_text(
            f"<b>Moscow Transport Information</b> приветствует вас, {callback.from_user.username}!\n\nЯ бот, который поможет узнать остановки маршрута или маршрут по остановке.\n"
            "Введите команду в формате:\n/903 — чтобы получить список остановок для маршрута\n"
            "//политехнический университет — чтобы найти маршруты, проходящие через остановку",
            reply_markup=start_markup()
        )
        await callback.answer()


    # Обработка нажатия кнопки маршрута
    @dp.callback_query(F.data.startswith("route_"))
    async def route_callback(callback: CallbackQuery):
        print("Нажата кнопка маршрута!")
        # key = callback.data.replace("route_", "route ")
        key = callback.data
        # print(key)
        # print(messageDict)
        if key in messageDict:
            await callback.message.answer(messageDict[key], reply_markup=clear_markup())

        await callback.answer()

    # Обработка нажатия кнопки остановки
    @dp.callback_query(F.data.startswith("stop_"))
    async def route_callback(callback: CallbackQuery):
        print("Нажата кнопка остановки!")
        key = callback.data
        print(f'key: {key}')
        print(f'messageDict: {messageDict}')
        print(f'stops_count: {stops_count}')
        
        if stops_count <= 4:
            if key in messageDict:
                await callback.message.answer(messageDict[key], reply_markup=clear_markup())
        elif stops_count > 4:
            if key in messageDict:
                pool = await create_pool()
                async with pool.acquire() as conn:
                    stop_info = await multi_outstops(conn, stop_name, key)
                    
                await callback.message.answer(stop_info, reply_markup=clear_markup())
                        
        await callback.answer()


    @dp.callback_query(F.data == "clear")
    async def clear_callback(callback: CallbackQuery):
        await callback.message.delete()
        await callback.answer() 


    # Логика обработки сообщения (маршрут/остановка)
    @dp.message()
    async def main_handler(message: Message):
        text = message.text.strip()

        # Если введен номер маршрута
        if text.startswith("/") and not text.startswith("//"):
            route_short_name = text[1:].strip()

            pool = await create_pool()
            async with pool.acquire() as conn:
                
                route_long_name = await conn.fetch("SELECT route_long_name FROM routes WHERE route_short_name ILIKE $1;", f'{route_short_name}') # Получаем route_long_name по route_short_name (один или список)
            
                if not route_long_name:
                    await message.answer(f"<b>По запросу '{route_short_name}' ни один маршрут не найден!</b>\n\nПроверьте запрос и повторите попытку.")
                    return
                else:
                    await routes(route_short_name, route_long_name, conn, message)  # логика routes() находим остановки на марушруте

        # Если введено название остановки
        elif text.startswith("//"):
            global stops_count # (для доступа внутри метода обработчика нажатий на кнопку остановки)
            global stop_name # (для доступа внутри метода обработчика нажатий на кнопку остановки)
            stop_name = text[2:].rstrip()

            pool = await create_pool()
            async with pool.acquire() as conn:
                # stops_names = await conn.fetch("SELECT stop_name FROM stops WHERE stop_name ILIKE $1;", f'%{stop_name}%') # находим регистронезависимо остановки
                stops_names_ids = await conn.fetch("SELECT stop_name, stop_id FROM stops WHERE stop_name ILIKE $1;", f'%{stop_name}%') # находим регистронезависимо остановки\
                stops_count = len(stops_names_ids)
                
                if not stops_names_ids:
                    await message.answer(f"<b>По запросу '{stop_name}' ни одна остановка не найдена!</b>\n\nПроверьте запрос и повторите попытку.")
                    return
                else:
                    await stops(stops_count, stops_names_ids, stop_name, conn, message) # логика stops() находим маршруты на останвоке
            
        else:
            await message.answer("Неправильный формат команды. Используй /номер_маршрута или //название_остановки.")

except KeyboardInterrupt:
    print('Exit...')


async def main():
    await bot.delete_webhook(drop_pending_updates=True) # Очищаем pending updates перед стартом
    await dp.start_polling(bot) # Теперь старые сообщения не будут обрабатываться

if __name__ == "__main__":
    asyncio.run(main())