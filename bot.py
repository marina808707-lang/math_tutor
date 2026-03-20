import logging
import json
import asyncio
import os
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties
 
# ─── ВЕБ-СЕРВЕР ДЛЯ RENDER ───────────────────────────────────────────────────
 
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass
 
def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()
 
threading.Thread(target=run_health_server, daemon=True).start()
 
# ─── НАСТРОЙКИ ────────────────────────────────────────────────────────────────
 
BOT_TOKEN = "8670573269:AAFdtY1kUPZwLfale4q-HWk6uYCh6ACViC0"
TUTOR_CHAT_ID = 742886023
MINI_APP_URL = "https://marina808707-lang.github.io/math_tutor/"
 
# ─── НАСТРОЙКА ЛОГОВ ──────────────────────────────────────────────────────────
 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
 
# ─── БОТ ──────────────────────────────────────────────────────────────────────
 
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
 
@dp.message(CommandStart())
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text="📝 Записаться на занятие",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ]],
        resize_keyboard=True
    )
    await message.answer(
        "👋 <b>Привет!</b>\n\n"
        "Нажмите кнопку ниже, чтобы заполнить анкету 🎯",
        reply_markup=kb
    )
 
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        logger.info(f"Получена заявка от {data.get('tgNick', '?')}")
 
        gm = {
            'few': 'Пара уроков',
            'long': 'Долгосрочные занятия',
            'oge': 'Подготовка к ОГЭ',
            'ege': 'Подготовка к ЕГЭ',
            'part2': 'Проверка второй части'
        }
        fm = {
            'individual': 'Индивидуально — 3000₽/ч',
            'pair_f': 'В паре с другом — 2000₽/ч',
            'pair_s': 'В паре (подберу пару) — 2000₽/ч',
            'group': 'Группа 3–5 человек — 1200₽/ч'
        }
 
        text = (
            "📬 <b>Новая заявка!</b>\n\n"
            f"👤 <b>Имя:</b> {data.get('name', '—')}\n"
            f"🎭 <b>Кто:</b> {data.get('who', '—')}\n"
            f"📚 <b>Класс:</b> {data.get('grade', '—')}\n"
            f"📊 <b>Успеваемость:</b> {data.get('perf', '—')}\n"
            f"🎯 <b>Цель:</b> {data.get('goal', '—')}\n"
        )
 
        if data.get('part2') and data.get('part2') != '—':
            text += f"✏️ <b>Проверка 2 части:</b> {data.get('part2')}\n"
        if data.get('part2sum') and data.get('part2sum') != '—':
            text += f"💰 <b>Сумма за проверку:</b> {data.get('part2sum')}\n"
        if data.get('solved') and data.get('solved') != '—':
            text += f"✍️ <b>Решал варианты:</b> {data.get('solved')}\n"
        if data.get('scores') and data.get('scores') != '—':
            text += f"🔢 <b>Баллы:</b> {data.get('scores')}\n"
        if data.get('topics') and data.get('topics') != '—':
            text += f"📌 <b>Темы:</b> {data.get('topics')}\n"
        if data.get('gcur') and data.get('gcur') != '—':
            text += f"📋 <b>Текущие оценки:</b> {data.get('gcur')}\n"
        if data.get('format') and data.get('format') != '—':
            text += f"👥 <b>Формат:</b> {data.get('format')}\n"
        if data.get('books') and data.get('books') != '—':
            text += f"📖 <b>Учебники:</b> {data.get('books')}\n"
        if data.get('notes') and data.get('notes') != '—':
            text += f"💬 <b>Пожелания:</b> {data.get('notes')}\n"
 
        text += (
            f"\n📱 <b>Telegram:</b> {data.get('tgNick', '—')}\n"
            f"🕐 {datetime.now().strftime('%d.%m.%Y в %H:%M')}"
        )
 
        await bot.send_message(TUTOR_CHAT_ID, text)
        await message.answer("✅ <b>Заявка отправлена!</b>\n\nСвяжусь с вами в ближайшее время 😊")
 
    except Exception as e:
        logger.error(f"Ошибка обработки заявки: {e}")
        await message.answer("⚠️ Что-то пошло не так. Попробуйте ещё раз.")
 
# ─── ЗАПУСК ───────────────────────────────────────────────────────────────────
 
async def main():
    logger.info("🤖 Бот запущен!")
    await dp.start_polling(bot)
 
if __name__ == "__main__":
    asyncio.run(main())
