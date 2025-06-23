from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="О боте", callback_data="about")]
    ])


def about_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="about_back")]
    ])


def clear_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Скрыть", callback_data="clear")]
    ])