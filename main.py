import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from manager import TaskManager

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ERROR: BOT_TOKEN not found.")
    exit()

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = TaskManager()

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📝 My Tasks"), KeyboardButton(text="🚀 Focus Mode"))
    builder.row(KeyboardButton(text="📊 My Stats"), KeyboardButton(text="🌡 Weather"))
    builder.row(KeyboardButton(text="➕ Add Quick Task"))
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Select a service...")

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "🎓 **Welcome to FocusTrackBot!**\n\nUse the menu below to manage your productivity.",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# --- 📝 РАБОТА СО СПИСКОМ ЗАДАЧ (Чистый вид) ---

@dp.message(F.text == "📝 My Tasks")
async def list_tasks_btn(message: Message):
    user_data = db.get_user_data(message.from_user.id)
    tasks = user_data.get("tasks", [])
    
    if not tasks:
        return await message.answer("📝 Your task list is empty. Add something via /add!")

    text = "📋 **Your Current Tasks:**\n"
    for t in tasks:
        status = "✅" if t["completed"] else "⏳"
        text += f"\n{status} **ID: {t['id']}** — {t['title']}"
        for step in t.get("steps", []):
            s_status = "🔹" if step["completed"] else "▫️"
            text += f"\n   └ {s_status} {step['title']}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="⚙️ Manage Tasks", callback_data="manage_menu")
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- ⚙️ МЕНЮ УПРАВЛЕНИЯ (Выбор задачи) ---

@dp.callback_query(F.data == "manage_menu")
async def manage_menu(callback: CallbackQuery):
    user_data = db.get_user_data(callback.from_user.id)
    tasks = user_data.get("tasks", [])
    
    if not tasks:
        return await callback.answer("Nothing to manage.", show_alert=True)

    builder = InlineKeyboardBuilder()
    for t in tasks:
        # Показываем ID и часть названия
        builder.button(text=f"Task {t['id']}: {t['title'][:15]}...", callback_data=f"select_{t['id']}")
    
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="⬅️ Back to List", callback_data="back_to_list"))
    
    await callback.message.edit_text("🎯 **Select a task to edit:**", reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- 🛠 ДЕЙСТВИЯ С ВЫБРАННОЙ ЗАДАЧЕЙ ---

@dp.callback_query(F.data.startswith("select_"))
async def select_task_action(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Complete", callback_data=f"done_{task_id}")
    builder.button(text="🔹 Add Step", callback_data=f"addstep_{task_id}")
    builder.button(text="❌ Delete", callback_data=f"delete_{task_id}")
    builder.button(text="⬅️ Back", callback_data="manage_menu")
    builder.adjust(2)
    
    await callback.message.edit_text(f"🛠 **Editing Task ID: {task_id}**\nWhat would you like to do?", 
                                     reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("done_"))
async def complete_task_callback(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    if db.complete_task(callback.from_user.id, task_id):
        await callback.answer("Task completed! 🎉")
        await callback.message.edit_text(f"✅ **Task {task_id} is now complete!**", reply_markup=InlineKeyboardBuilder().button(text="⬅️ Back", callback_data="manage_menu").as_markup())
    else:
        await callback.answer("Task not found.", show_alert=True)

@dp.callback_query(F.data.startswith("delete_"))
async def delete_task_callback(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    # Проверяем наличие метода удаления в manager.py
    if hasattr(db, 'delete_task') and db.delete_task(callback.from_user.id, task_id):
        await callback.answer("Task deleted.")
        await manage_menu(callback) # Возвращаемся в меню управления
    else:
        await callback.answer("Action not supported or task missing.", show_alert=True)

@dp.callback_query(F.data.startswith("addstep_"))
async def add_step_hint(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    await callback.message.answer(f"📝 To add a step to Task {task_id}, type:\n`/step {task_id} Step name`", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "back_to_list")
async def back_to_list(callback: CallbackQuery):
    await callback.message.delete()
    await list_tasks_btn(callback.message)

# --- 🚀 ОСТАЛЬНЫЕ ФУНКЦИИ ---

@dp.message(F.text == "🚀 Focus Mode")
async def focus_btn(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="15 min", callback_data="focus_15")
    builder.button(text="25 min", callback_data="focus_25")
    builder.button(text="45 min", callback_data="focus_45")
    builder.adjust(3)
    await message.answer("Choose your focus duration:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("focus_"))
async def start_focus(callback: CallbackQuery):
    minutes = int(callback.data.split("_")[1])
    await callback.message.edit_text(f"🚀 Focus timer started for {minutes} min!")
    await asyncio.sleep(minutes * 60)
    db.add_focus_session(callback.from_user.id, minutes)
    await callback.message.answer(f"🏆 Session complete! Earned {minutes * 10} XP.")

@dp.message(F.text == "📊 My Stats")
async def stats_btn(message: Message):
    stats = db.get_user_stats(message.from_user.id)
    await message.answer(
        f"📊 **Your Progress:**\n\n🏆 Level: {stats.get('level', 1)}\n✨ XP: {stats.get('xp', 0)}\n⏳ Focus: {stats.get('focus_time', 0)} min",
        parse_mode="Markdown"
    )

@dp.message(F.text == "🌡 Weather")
async def weather_btn(message: Message):
    url = "https://api.open-meteo.com/v1/forecast?latitude=51.18&longitude=71.45&current_weather=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                temp = data["current_weather"]["temperature"]
                advice = "Perfect for AITU! 🏫" if temp > 10 else "Stay warm! ☕️"
                await message.answer(f"🌡 **Astana:** {temp}°C\n💡 {advice}", parse_mode="Markdown")

@dp.message(F.text == "➕ Add Quick Task")
async def add_quick_task(message: Message):
    await message.answer("Type: `/add Task Name`", parse_mode="Markdown")

@dp.message(Command("add"))
async def add_task(message: Message, command: Command):
    if command.args:
        db.add_task(message.from_user.id, command.args)
        await message.answer("✅ Task added!")
    else:
        await message.answer("Usage: `/add Task Name`", parse_mode="Markdown")

@dp.message(Command("step"))
async def add_step_cmd(message: Message, command: Command):
    try:
        parts = command.args.split(" ", 1)
        if db.add_step(message.from_user.id, int(parts[0]), parts[1]):
            await message.answer("✅ Step added!")
        else:
            await message.answer("❌ Task ID not found.")
    except:
        await message.answer("Usage: `/step [ID] [text]`")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())