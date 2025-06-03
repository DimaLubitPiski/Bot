from bot.main import dp, bot

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.run_polling(bot))