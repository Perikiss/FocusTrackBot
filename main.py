import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from manager import TaskManager

TOKEN = "8772653607:AAFtZDfGKuw4xWP0CBehUeK7kBizyquI2jA"

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = TaskManager()

# --- Блок команд ---

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("FocusTrack приветствует тебя! \nИспользуй /add [задача], чтобы записать дело, или /focus для таймера.")

@dp.message(Command("add"))
async def add_task(message: Message, command: Command):
    if command.args:
        db.add_task(message.from_user.id, command.args)
        await message.answer(f"Задача '{command.args}' добавлена!")
    else:
        await message.answer("Пример: /add Учить Python")

@dp.message(Command("list"))
async def list_tasks(message: Message):
    tasks = db.get_tasks(message.from_user.id)
    if tasks:
        response = "\n".join([f"- {t}" for t in tasks])
        await message.answer(f"Твои задачи:\n{response}")
    else:
        await message.answer("Список пуст.")

# --- Шаг 2: Таймер фокусировки ---

@dp.message(Command("focus"))
async def focus_handler(message: Message):
    # Создаем кнопку через Builder (удобно для динамических меню)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="🚀 Старт (25 мин)", callback_data="start_focus")
    )
    
    await message.answer(
        "Режим концентрации: телефон в сторону, работаем!",
        reply_markup=builder.as_markup()
    )

# Обработка нажатия на кнопку (Callback Query)
@dp.callback_query(F.data == "start_focus")
async def process_callback_start(callback: types.CallbackQuery):
    # Отправляем уведомление в верхней части экрана
    await callback.answer("Таймер запущен!")
    
    # Редактируем текущее сообщение, чтобы показать статус
    await callback.message.edit_text("⏳ Фокус пошел! Вернусь через 25 минут.")
    
    # Для теста в университете лучше поставить 5-10 секунд, чтобы показать работу
    await asyncio.sleep(5) 
    await callback.message.answer(f"@{callback.from_user.username}, время вышло! Пора отдохнуть. ☕️")

# --- Запуск бота ---

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())