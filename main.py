import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from manager import TaskManager

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = os.getenv("BOT_TOKEN")

# Проверка, чтобы бот не падал с непонятной ошибкой
if not TOKEN:
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("BOT_TOKEN="):
                    TOKEN = line.strip().split("=")[1]
    except:
        pass

if not TOKEN:
    print("❌ ОШИБКА: Токен не найден. Проверь файл .env еще раз.")
    exit()

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = TaskManager()

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("🎓 FocusTrackBot готов к работе!\n/add - задача\n/list - список\n/focus - таймер\n/stats - прогресс\n/weather - погода в Астане")

@dp.message(Command("add"))
async def add_task(message: Message, command: Command):
    if command.args:
        db.add_task(message.from_user.id, command.args)
        await message.answer("✅ Задача добавлена! Посмотреть: /list")
    else:
        await message.answer("Напиши название задачи после команды /add")

@dp.message(Command("list"))
async def list_tasks(message: Message):
    user_data = db.get_user_data(message.from_user.id)
    tasks = user_data.get("tasks", [])
    
    if not tasks:
        return await message.answer("📝 Список пуст. Добавь задачу через /add")

    text = "📋 **Твои задачи:**\n"
    for t in tasks:
        status = "✅" if t["completed"] else "⏳"
        text += f"\n{status} **ID: {t['id']} — {t['title']}**\n"
        for step in t.get("steps", []):
            s_status = "🔹" if step["completed"] else "▫️"
            text += f"   {s_status} {step['title']}\n"
    
    text += "\n💡 Чтобы добавить шаг: `/step [ID] [текст]`\n💡 Чтобы закрыть: `/done [ID]`"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("focus"))
async def focus_menu(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="15 мин", callback_data="focus_15")
    builder.button(text="25 мин", callback_data="focus_25")
    builder.button(text="45 мин", callback_data="focus_45")
    builder.adjust(3)
    await message.answer("Выбери время для фокусировки:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("focus_"))
async def start_focus(callback: CallbackQuery):
    minutes = int(callback.data.split("_")[1])
    await callback.message.edit_text(f"🚀 Таймер запущен на {minutes} минут! Не отвлекайся.")
    
    await asyncio.sleep(minutes * 60) 
    
    db.add_focus_session(callback.from_user.id, minutes)
    await callback.message.answer(f"🏆 Время вышло! Ты заработала {minutes * 10} XP.")

@dp.message(Command("step"))
async def add_step_cmd(message: Message, command: Command):
    try:
        args = command.args.split(" ", 1)
        task_id = int(args[0])
        step_name = args[1]
        if db.add_step(message.from_user.id, task_id, step_name):
            await message.answer(f"✅ Шаг добавлен к задаче {task_id}")
        else:
            await message.answer("❌ Задача с таким ID не найдена.")
    except:
        await message.answer("Пиши так: `/step 0 Купить книгу`")

@dp.message(Command("done"))
async def done_cmd(message: Message, command: Command):
    try:
        task_id = int(command.args)
        if db.complete_task(message.from_user.id, task_id):
            await message.answer(f"🎉 Задача {task_id} выполнена!")
        else:
            await message.answer("❌ Задача не найдена.")
    except:
        await message.answer("Пиши так: `/done 0`")

@dp.message(Command("weather"))
async def get_weather(message: Message):
    # Координаты Астаны (AITU)
    url = "https://api.open-meteo.com/v1/forecast?latitude=51.18&longitude=71.45&current_weather=true"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    current = data["current_weather"]
                    temp = current["temperature"]
                    wind = current["windspeed"]
                    
                    # Маленький совет в зависимости от температуры
                    advice = "Идеально, чтобы пойти в универ! 🏫" if temp > 10 else "Холодновато, лучше ботать дома или в коворкинге. ☕️"
                    
                    await message.answer(
                        f"🌡 **Погода в Астане:**\n\n"
                        f"Температура: {temp}°C\n"
                        f"Скорость ветра: {wind} км/ч\n\n"
                        f"💡 {advice}",
                        parse_mode="Markdown"
                    )
                else:
                    await message.answer("❌ Сервер погоды временно недоступен.")
    except Exception as e:
        print(f"Ошибка погоды: {e}")
        await message.answer("❌ Произошла ошибка при получении погоды. Проверь интернет-соединение.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())