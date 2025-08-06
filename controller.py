from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import subprocess
import asyncio
import os 
from dotenv import load_dotenv 
load_dotenv() 
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY = os.getenv('NASA_API_KEY')


async def start_bot(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Starting Nasabot now...")
    # Launch nasabot.py as a subprocess
    subprocess.Popen(["python3", "nasabot.py"])

app = ApplicationBuilder().token(TELEGRAM_TOKEN_TOKEN).build()
app.add_handler(CommandHandler("startbot", start_bot))

if __name__ == "__main__":
    asyncio.run(app.run_polling())
