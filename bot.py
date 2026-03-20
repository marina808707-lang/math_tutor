"""
Бот репетитора по математике
Получает заявки из Mini App и отправляет уведомления репетитору
"""

import logging
import json
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

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
SHEET_NAME = "Заявки репетитор"       # Название Google-таблицы
GOOGLE_CREDS_FILE = "google_creds.json"  # Файл ключей Google API

# ─── НАСТРОЙКА ЛОГОВ ──────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── GOOGLE SHEETS ────────────────────────────────────────────────────────────

def get_sheet():
    """Подключение к Google Sheets"""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    return sheet

def save_to_sheet(data: dict):
    """Сохранить заявку в Google Sheets"""
    try:
        sheet = get_sheet()
        # Если таблица пустая — создать заголовки
        if sheet.row_count == 0 or sheet.cell(1, 1).value != 'Дата':
            headers = [
                'Дата', 'Имя', 'Кто', 'Класс', 'Успеваемость', 'Цель',
                'Доп: Проверка 2 части', 'Решал варианты', 'Баллы',
                'Темы для разбора', 'Текущие оценки', 'Формат',
                'Учебники', 'Пожелания', 'Telegram'
            ]
            sheet.insert_row(headers, 1)

        row = [
            datetime.now().strftime("%d.%m.%Y %H:%M"),
            data.get('name', ''),
            data.get('who', ''),
            data.get('grade', ''),
            data.get('perf', ''),
            data.get('goal', ''),
            data.get('check_part2', ''),
            data.get('solved_variants', ''),
            data.get('scores', ''),
            data.get('topics', ''),
            data.get('grades_current', ''),
            data.get('format', ''),
            data.get('books', ''),
            data.get('notes', ''),
            data.get('tgNick', ''),
        ]
        sheet.append_row(row)
        logger.info("✅ Заявка сохранена в Google Sheets")
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении в таблицу: {e}")

# ─── ФОРМАТИРОВАНИЕ УВЕДОМЛЕНИЯ ───────────────────────────────────────────────

def format_notification(d: dict) -> str:
    """Форматировать заявку для отправки репетитору"""
    lines = [
        "📬 <b>Новая заявка!</b>",
        "",
        f"👤 <b>Имя:</b> {d.get('name', '—')}",
        f"🎭 <b>Кто:</b> {d.get('who', '—')}",
        f"📚 <b>Класс:</b> {d.get('grade', '—')}",
        f"📊 <b>Успеваемость:</b> {d.get('perf', '—')}",
        f"🎯 <b>Цель:</b> {d.get('goal', '—')}",
    ]

    # Доп. поля в зависимости от цели
    if d.get('solved_variants') and d['solved_variants'] != '—':
        lines.append(f"✍️ <b>Решал варианты:</b> {d['solved_variants']}")
    if d.get('scores') and d['scores'] != '—':
        lines.append(f"🔢 <b>Баллы:</b> {d['scores']}")
    if d.get('topics') and d['topics'] != '—':
        lines.append(f"📌 <b>Темы:</b> {d['topics']}")
    if d.get('grades_current') and d['grades_current'] != '—':
        lines.append(f"📋 <b>Текущие оценки:</b> {d['grades_current']}")

    lines += [
        f"👥 <b>Формат:</b> {d.get('format', '—')}",
        f"🔍 <b>Проверка 2 части:</b> {d.get('check_part2', '—')}",
    ]

    if d.get('books') and d['books'] != '—':
        lines.append(f"📖 <b>Учебники:</b> {d['books']}")
    if d.get('notes') and d['notes'] != '—':
        lines.append(f"💬 <b>Пожелания:</b> {d['notes']}")

    lines += [
        "",
        f"📱 <b>Telegram:</b> {d.get('tgNick', '—')}",
        "",
        f"🕐 {datetime.now().strftime('%d.%m.%Y в %H:%M')}",
    ]

    return "\n".join(lines)

# ─── БОТ ──────────────────────────────────────────────────────────────────────

from aiogram.client.default import DefaultBotProperties
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    """Приветствие при /start"""
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
        "Я помогу вам записаться на занятия по математике.\n\n"
        "Нажмите кнопку ниже, чтобы заполнить анкету — "
        "это займёт не больше 2 минут 🎯",
        reply_markup=kb
    )

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    """Обработка данных из Mini App"""
    try:
        raw = message.web_app_data.data
        data = json.loads(raw)
        logger.info(f"Получена заявка от {data.get('tgNick', '?')}")

        # 1. Сохранить в Google Sheets
        save_to_sheet(data)

        # 2. Отправить уведомление репетитору
        text = format_notification(data)
        await bot.send_message(TUTOR_CHAT_ID, text)

        # 3. Подтвердить ученику
        await message.answer(
            "✅ <b>Заявка отправлена!</b>\n\n"
            "Я свяжусь с вами в ближайшее время.\n"
            "Если хотите уточнить что-то срочно — пишите напрямую 😊"
        )

    except Exception as e:
        logger.error(f"Ошибка обработки заявки: {e}")
        await message.answer("⚠️ Что-то пошло не так. Попробуйте ещё раз или напишите напрямую.")

# ─── ЗАПУСК ───────────────────────────────────────────────────────────────────

async def main():
    logger.info("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
