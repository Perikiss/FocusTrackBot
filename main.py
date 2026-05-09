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

if not TOKEN:
    print("❌ ERROR: BOT_TOKEN not found in .env file.")
    exit()

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = TaskManager()

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        f"Hello, {message.from_user.first_name}!\n"
        "🎓 **Welcome to FocusTrackBot!**\n\n"
        "Available commands:\n"
        "/add - Create a new task\n"
        "/list - Show your task list\n"
        "/focus - Start focus timer\n"
        "/stats - View your progress\n"
        "/weather - Current weather in Astana",
        parse_mode="Markdown")

@dp.message(Command("add"))
async def add_task(message: Message, command: Command):
    if command.args:
        db.add_task(message.from_user.id, command.args)
        await message.answer("✅ Task added! View it: /list")
    else:
        await message.answer("Write the task name after the /add command")

@dp.message(Command("list"))
async def list_tasks(message: Message):
    user_data = db.get_user_data(message.from_user.id)
    tasks = user_data.get("tasks", [])
    
    if not tasks:
        return await message.answer("📝 Your list is empty. Add a task with /add.")

    text = "📋 **Your tasks:**\n"
    for t in tasks:
        status = "✅" if t["completed"] else "⏳"
        text += f"\n{status} **ID: {t['id']} — {t['title']}**\n"
        for step in t.get("steps", []):
            s_status = "🔹" if step["completed"] else "▫️"
            text += f"   {s_status} {step['title']}\n"
    
    text += "\n💡 To add a step: `/step [ID] [text]`\n💡 To complete: `/done [ID]`"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("focus"))
async def focus_menu(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="15 мин", callback_data="focus_15")
    builder.button(text="25 мин", callback_data="focus_25")
    builder.button(text="45 мин", callback_data="focus_45")
    builder.adjust(3)
    await message.answer("Choose the time for focus:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("focus_"))
async def start_focus(callback: CallbackQuery):
    minutes = int(callback.data.split("_")[1])
    await callback.message.edit_text(f"🚀 Timer started for {minutes} minutes! Don't get distracted.")
    
    await asyncio.sleep(minutes * 60) 
    
    db.add_focus_session(callback.from_user.id, minutes)
    await callback.message.answer(f"🏆 Time's up! You earned {minutes * 10} XP.")

@dp.message(Command("step"))
async def add_step_cmd(message: Message, command: Command):
    try:
        args = command.args.split(" ", 1)
        task_id = int(args[0])
        step_name = args[1]
        if db.add_step(message.from_user.id, task_id, step_name):
            await message.answer(f"✅ Step added to task {task_id}")
        else:
            await message.answer("❌ Task with such ID not found.")
    except:
        await message.answer("Write like this: `/step 0 Buy a book`")

@dp.message(Command("done"))
async def done_cmd(message: Message, command: Command):
    try:
        task_id = int(command.args)
        if db.complete_task(message.from_user.id, task_id):
            await message.answer(f"🎉 Task {task_id} completed!")
        else:
            await message.answer("❌ Task not found.")
    except:
        await message.answer("Write like this: `/done 0`")

@dp.message(Command("weather"))
async def get_weather(message: Message):
    # Координаты Аст
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
                    advice = "Perfect for going to university! 🏫" if temp > 10 else "A bit chilly, better to study at home or in a co-working space. ☕️"
                    
                    await message.answer(
                        f"🌡 **Weather in Astana:**\n\n"
                        f"Temperature: {temp}°C\n"
                        f"Wind speed: {wind} km/h\n\n"
                        f"💡 {advice}",
                        parse_mode="Markdown"
                    )
                else:
                    await message.answer("❌ Weather server is temporarily unavailable.")
    except Exception as e:
        print(f"Ошибка погоды: {e}")
        await message.answer("❌ Error fetching weather data.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())