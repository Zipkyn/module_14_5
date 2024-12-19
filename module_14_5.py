from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from crud_functions import initiate_db, add_user, is_included, get_all_products
import asyncio


API_TOKEN = ''

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

initiate_db()

class Form(StatesGroup):
    age = State()
    growth = State()
    weight = State()

class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()

main_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text='Рассчитать')],
        [KeyboardButton(text='Купить')],
        [KeyboardButton(text='Регистрация')]
    ]
)

products_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Product1', callback_data='product_buying')],
        [InlineKeyboardButton(text='Product2', callback_data='product_buying')],
        [InlineKeyboardButton(text='Product3', callback_data='product_buying')],
        [InlineKeyboardButton(text='Product4', callback_data='product_buying')]
    ]
)

@dp.message(F.text.lower() == 'привет')
async def greet(message: types.Message):
    await message.answer("Введите команду /start, чтобы начать общение.")

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Я бот, помогающий твоему здоровью.", reply_markup=main_keyboard)

@dp.message(F.text == 'Рассчитать')
async def calculate_menu(message: types.Message, state: FSMContext):
    await message.answer("Введите свой возраст:")
    await state.set_state(Form.age)

@dp.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await message.answer("Введите свой рост:")
    await state.set_state(Form.growth)

@dp.message(Form.growth)
async def process_growth(message: types.Message, state: FSMContext):
    await state.update_data(growth=int(message.text))
    await message.answer("Введите свой вес:")
    await state.set_state(Form.weight)

@dp.message(Form.weight)
async def process_weight(message: types.Message, state: FSMContext):
    data = await state.get_data()
    weight = int(message.text)
    age = data['age']
    growth = data['growth']

    calories = 10 * weight + 6.25 * growth - 5 * age + 5

    await message.answer(f"Ваша норма калорий: {calories:.2f}")
    await state.clear()
import os
from crud_functions import get_all_products

@dp.message(F.text == 'Купить')
async def get_buying_list(message: types.Message):
    products = get_all_products()
    if not products:
        await message.answer("Нет доступных продуктов для покупки.")
        return

    for product in products:
        product_id, title, description, price = product
        photo_path = f'images/{title}.jpg'

        if os.path.exists(photo_path):
            await message.answer_photo(
                photo=FSInputFile(photo_path),
                caption=f"Название: {title}\nОписание: {description}\nЦена: {price}"
            )
        else:
            await message.answer(f"Название: {title}\nОписание: {description}\nЦена: {price}\n[Изображение не найдено: {photo_path}]")

    await message.answer("Выберите продукт для покупки:", reply_markup=products_inline_keyboard)


@dp.callback_query(F.data == 'product_buying')
async def send_confirm_message(call: types.CallbackQuery):
    await call.message.answer("Вы успешно приобрели продукт!")
    await call.answer()

@dp.message(F.text == 'Регистрация')
async def sign_up(message: types.Message, state: FSMContext):
    await message.answer("Введите имя пользователя (только латинский алфавит):")
    await state.set_state(RegistrationState.username)

@dp.message(RegistrationState.username)
async def set_username(message: types.Message, state: FSMContext):
    username = message.text
    if is_included(username):
        await message.answer("Пользователь существует, введите другое имя:")
        return
    await state.update_data(username=username)
    await message.answer("Введите свой email:")
    await state.set_state(RegistrationState.email)

@dp.message(RegistrationState.email)
async def set_email(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(email=email)
    await message.answer("Введите свой возраст:")
    await state.set_state(RegistrationState.age)

@dp.message(RegistrationState.age)
async def set_age(message: types.Message, state: FSMContext):
    age = message.text
    if not age.isdigit():
        await message.answer("Возраст должен быть числом. Введите свой возраст:")
        return
    age = int(age)
    data = await state.get_data()
    username = data['username']
    email = data['email']
    add_user(username, email, age)
    await message.answer(f"Пользователь {username} успешно зарегистрирован! Баланс: 1000")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())


