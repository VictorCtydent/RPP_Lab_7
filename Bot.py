import logging
import os
import psycopg2 as pg
import re
import requests
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import BotCommand, BotCommandScopeDefault

bot_token = os.getenv('API_TOKEN')
bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())

conn = pg.connect(user='postgres', password='5577', host='localhost', database='lr7')
cursor = conn.cursor()


class Form(StatesGroup):
    check = State()
    num = State()
    con = State()
    save_base = State()
    save_base_rate = State()
    save_converted = State()
    save_converted_rate = State()
    save = State()


user_commands = [
    BotCommand(command='/start', description='Начать'),
    BotCommand(command='/convert', description='Конвертирование')
]
admin_commands = [
    BotCommand(command='/start', description='Начать'),
    BotCommand(command='/manage_currency', description='Менеджер валют'),
    BotCommand(command='/convert', description='Конвертирование')
]

param = {}


def get_id():
    cursor.execute("""SELECT chat_id FROM admins""")
    Admin_id = cursor.fetchall()

    Admin_id = re.sub(r"[^0-9]", r"", str(Admin_id))
    admins_list = []
    if Admin_id in admins_list:
        return admins_list
    else:
        admins_list.append(Admin_id)
        return admins_list


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    await message.reply("Привет! Я бот для конвертации валюты!")


@dp.message_handler(commands=['manage_currency'])
async def manage_command(message: types.Message):
    admin_id = get_id()
    admin = str(message.chat.id)

    if admin in admin_id:
        await Form.save_base.set()
        await message.reply("Введите название конвертируемой (основной) валюты")
    else:
        await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
        await message.reply("Нет доступа к команде")


@dp.message_handler(state=Form.save_base)
async def save_base_command(message: types.Message, state: FSMContext):
    await state.update_data(baseCurrency=message.text)
    await Form.save_converted.set()
    await message.reply("Введите название валюты, в которую хотите конвертировать указанную ранее валюту")


@dp.message_handler(state=Form.save_converted)
async def save_converted_command(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)
    await Form.save_converted_rate.set()
    await message.reply("Введите курс")


@dp.message_handler(state=Form.save_converted_rate)
async def save_converted_rate_command(message: types.Message, state: FSMContext):
    d = await state.get_data()
    code_ = d['code']

    try:
        rates_ = d['rates']
    except Exception:
        rates_ = []

    rates_.append({'code': code_, 'rate': float(message.text)})

    await state.update_data(rates=rates_)
    await Form.save.set()

    await message.reply("Желаете добавить еще валюту, в которую может быть сконвертирована основная валюта? Да/Нет")


@dp.message_handler(state=Form.save)
async def save_command(message: types.Message, state: FSMContext):
    cur = await state.get_data()
    check = message.text
    if check.lower() == 'да':
        await message.reply("Введите название валюты, в которую хотите конвертировать")
        await Form.save_converted.set()
    else:
        param["baseCurrency"] = str(cur["baseCurrency"])
        param["rates"] = cur["rates"]
        requests.post("http://localhost:10670/load", json=param)
        await message.reply("Вы завершили настройку валюты")
        param.clear()
        await state.finish()


@dp.message_handler(commands=['convert'])
async def convert_command(message: types.Message):
    await Form.check.set()
    await message.reply("Введите название базовой валюты")


@dp.message_handler(state=Form.check)
async def process_check(message: types.Message, state: FSMContext):
    await state.update_data(baseCurrency=message.text)
    await Form.num.set()
    await message.reply("Введите название валюты, в которую будет конвертироваться")


@dp.message_handler(state=Form.num)
async def process_convert(message: types.Message, state: FSMContext):
    await state.update_data(convertedCurrency=message.text)
    await Form.con.set()
    await message.reply("Введите сумму для конвертации")


@dp.message_handler(state=Form.con)
async def process_convert2(message: types.Message, state: FSMContext):
    num = message.text
    if not num:
        await message.reply("Неверный ввод. Пожалуйста, введите корректное число")
        return

    try:
        amount = float(num)
    except ValueError:
        await message.reply("Неверный ввод. Пожалуйста, введите корректное число")
        return

    cur = await state.get_data()
    param = {
        "baseCurrency": str(cur["baseCurrency"]),
        "convertedCurrency": str(cur["convertedCurrency"]),
        "sum": amount
    }

    result = requests.get("http://localhost:10607/convert", params=param)

    if result.status_code == 500:
        await message.reply('Во время конвертации валюты произошла ошибка')
        await state.finish()
    else:
        res = result.json()
        converted_amount = res.get('converted')
        if converted_amount is not None:
            await message.reply(f'Результат конвертации: {converted_amount}')
        else:
            await message.reply('Во время конвертации валюты произошла ошибка')
        await state.finish()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
