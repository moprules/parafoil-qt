import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from dotenv import dotenv_values, set_key

async def a_send_OK(msg):
    config = dotenv_values(".env")
    bot = Bot(token=config["TOKEN"])
    await bot.send_message(config["ADMIN_ID"], f"ОК -> {msg}")

def send_OK(msg):
    asyncio.run(a_send_OK(msg))


config = dotenv_values(".env")
bot = Bot(token=config["TOKEN"])
# Диспетчер
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    ADMIN_ID = str(message.from_user.id)
    set_key(".env", "ADMIN_ID", ADMIN_ID)
    await message.answer("ADMIN_ID ADD!")
    await bot.set_my_commands([])
    await dp.stop_polling()


async def a_get_admin_id():
    info = await bot.get_me()
    print(f"https://t.me/{info.username}")

    commands = [types.BotCommand(command="/start", description="Задать администратора")]
    await bot.set_my_commands(commands)
    await dp.start_polling(bot)

def get_admin_id():
    asyncio.run(a_get_admin_id())


if __name__ == "__main__":
    get_admin_id()