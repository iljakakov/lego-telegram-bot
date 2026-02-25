import json
import urllib.parse
import urllib.request
from typing import List, Dict, Any
import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==========================
# ВСТАВЬ СВОИ КЛЮЧИ
# ==========================
BOT_TOKEN = "8779809354:AAH1FLP0NIFCR0SpOM2zcIoBIYhQOGIEASQ"
REBRICKABLE_API_KEY = "9e2919625307185f62a1404f1cb0872c"
BASE_URL = "https://rebrickable.com/api/v3"


def fetch_alternates(set_num: str, page_size: int = 10) -> List[Dict[str, Any]]:
    url = f"{BASE_URL}/lego/sets/{urllib.parse.quote(set_num)}/alternates/?page_size={page_size}"
    req = urllib.request.Request(url, headers={"Authorization": f"key {REBRICKABLE_API_KEY}"})

    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("results", [])


def format_models(models: List[Dict[str, Any]], set_num: str) -> str:
    if not models:
        return f"Для набора {set_num} альтернативные модели не найдены."

    lines = [f"Alternate models for *{set_num}* (top {len(models)}):\n"]
    for i, m in enumerate(models, 1):
        name = m.get("name", "Unnamed")
        designer = m.get("designer_name", "Unknown")
        parts = m.get("num_parts", "-")
        url = m.get("moc_url", "")

        # ВАЖНО: is_free ненадёжно. Лучше показывать наличие инструкций.
        has_instr = bool(m.get("moc_has_building_instructions"))
        instr = "📄 PDF available" if has_instr else "💰 No instructions"

        line = f"{i}) *{name}* — {designer} ({parts} parts) {instr}"
        if url:
            line += f"\n{url}"
        lines.append(line)

    return "\n\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "Привет! Я LEGO Alternate Models Bot.\n\n"
        "Команды:\n"
        "/alts <set_num> — показать альтернативные модели\n"
        "Пример: /alts 77244-1\n"
    )
    await update.message.reply_text(msg)


async def alts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Напиши номер набора: /alts 77244-1")
        return

    set_num = context.args[0].strip()

    if "-" not in set_num:
        await update.message.reply_text("Нужен полный формат, например 77244-1 (с '-1').")
        return

    try:
        models = fetch_alternates(set_num, page_size=12)
        text = format_models(models, set_num)
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"Ошибка при запросе к API: {e}")


def main():
    if "PUT_YOUR_TELEGRAM_BOT_TOKEN_HERE" in BOT_TOKEN or not BOT_TOKEN.strip():
        raise RuntimeError("Вставь BOT_TOKEN от @BotFather в переменную BOT_TOKEN.")
    if "PUT_YOUR_REBRICKABLE_API_KEY_HERE" in REBRICKABLE_API_KEY or not REBRICKABLE_API_KEY.strip():
        raise RuntimeError("Вставь Rebrickable API key в переменную REBRICKABLE_API_KEY.")

    # ✅ ФИКС ДЛЯ Windows + Python 3.14: создаём loop явно
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alts", alts))

    print("Bot is running...")
    app.run_polling(close_loop=False)  # close_loop=False помогает на некоторых сборках Windows


if __name__ == "__main__":
    main()