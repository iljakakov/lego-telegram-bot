import os
import json
import urllib.parse
import urllib.request
from typing import List, Dict, Any, Optional
import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==========================
# CONFIG
# ==========================
BASE_URL = "https://rebrickable.com/api/v3"
PAGE_SIZE_API = 50         
PAGE_SIZE_UI = 5           
PREFS_FILE = "user_prefs.json" 

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
REBRICKABLE_API_KEY = os.getenv("REBRICKABLE_API_KEY", "").strip()


# ==========================
# I18N (RU/EN)
# ==========================
TEXTS = {
    "ru": {
        "start_title": "🧱 *LEGO Alternate Models Bot*",
        "start_body": (
            "Я нахожу *альтернативные модели* (alternate builds) для набора LEGO через Rebrickable.\n\n"
            "Как пользоваться:\n"
            "• Нажми *Поиск моделей* и введи номер набора (пример: `77244-1`)\n"
            "• Или команда: `/alts 77244-1`\n\n"
            "Ниже можно выбрать язык 👇"
        ),
        "btn_search": "🔎 Поиск моделей",
        "btn_lang": "🌍 Язык",
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_en": "🇬🇧 English",
        "ask_set": "📦 Введи номер набора в формате `77244-1`:",
        "bad_set": "⚠️ Нужен полный формат, например `77244-1` (с `-1`).",
        "fetching": "⏳ Ищу альтернативные модели для *{set_num}*…",
        "not_found": "😕 Для набора *{set_num}* альтернативные модели не найдены.",
        "error_api": "❌ Ошибка API: {msg}",
        "error_keys": "❌ Не настроены ключи. Добавь `BOT_TOKEN` и `REBRICKABLE_API_KEY` в переменные окружения.",
        "header": "🧱 *Альтернативные модели*\n📦 Набор: *{set_num}*\nПоказано: *{shown}* из *{total}* {filter_line}",
        "filter_on": "• 📄 Фильтр: *только с PDF*",
        "filter_off": "• 📄 Фильтр: *все модели*",
        "item_pdf_yes": "📄 PDF: *есть*",
        "item_pdf_no": "💰 PDF: *нет*",
        "btn_prev": "◀️ Назад",
        "btn_next": "Вперёд ▶️",
        "btn_toggle_pdf_on": "📄 Только с PDF",
        "btn_toggle_pdf_off": "📄 Показать все",
        "btn_change_lang": "🌍 Сменить язык",
        "btn_open": "🔗 Открыть модель",
        "lang_changed_ru": "✅ Язык установлен: Русский",
        "lang_changed_en": "✅ Language set: English",
        "help": (
            "Команды:\n"
            "• `/start` — меню\n"
            "• `/alts <set_num>` — поиск альтернатив (пример: `/alts 77244-1`)\n"
            "• `/lang` — выбрать язык\n"
        ),
    },
    "en": {
        "start_title": "🧱 *LEGO Alternate Models Bot*",
        "start_body": (
            "I find *alternate builds* for a LEGO set using Rebrickable.\n\n"
            "How to use:\n"
            "• Tap *Search models* and enter a set number (example: `77244-1`)\n"
            "• Or command: `/alts 77244-1`\n\n"
            "Choose a language below 👇"
        ),
        "btn_search": "🔎 Search models",
        "btn_lang": "🌍 Language",
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_en": "🇬🇧 English",
        "ask_set": "📦 Enter a set number like `77244-1`:",
        "bad_set": "⚠️ Please use full format like `77244-1` (with `-1`).",
        "fetching": "⏳ Searching alternate models for *{set_num}*…",
        "not_found": "😕 No alternate models found for *{set_num}*.",
        "error_api": "❌ API error: {msg}",
        "error_keys": "❌ Keys are not configured. Add `BOT_TOKEN` and `REBRICKABLE_API_KEY` as environment variables.",
        "header": "🧱 *Alternate models*\n📦 Set: *{set_num}*\nShowing: *{shown}* of *{total}* {filter_line}",
        "filter_on": "• 📄 Filter: *PDF only*",
        "filter_off": "• 📄 Filter: *all models*",
        "item_pdf_yes": "📄 PDF: *available*",
        "item_pdf_no": "💰 PDF: *not available*",
        "btn_prev": "◀️ Prev",
        "btn_next": "Next ▶️",
        "btn_toggle_pdf_on": "📄 PDF only",
        "btn_toggle_pdf_off": "📄 Show all",
        "btn_change_lang": "🌍 Change language",
        "btn_open": "🔗 Open model",
        "lang_changed_ru": "✅ Язык установлен: Русский",
        "lang_changed_en": "✅ Language set: English",
        "help": (
            "Commands:\n"
            "• `/start` — menu\n"
            "• `/alts <set_num>` — search alternates (example: `/alts 77244-1`)\n"
            "• `/lang` — choose language\n"
        ),
    },
}


# ==========================
# Simple user prefs (language)
# ==========================
def load_prefs() -> Dict[str, Any]:
    try:
        with open(PREFS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_prefs(prefs: Dict[str, Any]) -> None:
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)


PREFS = load_prefs()


def get_lang(user_id: int) -> str:
    lang = PREFS.get(str(user_id), {}).get("lang")
    return lang if lang in ("ru", "en") else "ru"


def set_lang(user_id: int, lang: str) -> None:
    if lang not in ("ru", "en"):
        return
    PREFS.setdefault(str(user_id), {})["lang"] = lang
    save_prefs(PREFS)


def t(user_id: int, key: str) -> str:
    lang = get_lang(user_id)
    return TEXTS[lang][key]


# ==========================
# Rebrickable API
# ==========================
def fetch_alternates(set_num: str, page_size: int = PAGE_SIZE_API) -> List[Dict[str, Any]]:
    url = f"{BASE_URL}/lego/sets/{urllib.parse.quote(set_num)}/alternates/?page_size={page_size}"
    req = urllib.request.Request(url, headers={"Authorization": f"key {REBRICKABLE_API_KEY}"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("results", [])


def normalize_set_num(raw: str) -> str:
    return raw.strip()


def looks_like_set_num(s: str) -> bool:
    # простая проверка: нужен дефис и что-то после него
    if "-" not in s:
        return False
    left, right = s.split("-", 1)
    return left.isdigit() and right.isdigit()


# ==========================
# UI rendering
# ==========================
def format_page(
    user_id: int,
    set_num: str,
    models: List[Dict[str, Any]],
    page: int,
    pdf_only: bool,
) -> str:
    total = len(models)
    start = page * PAGE_SIZE_UI
    end = min(start + PAGE_SIZE_UI, total)
    shown = end - start

    filter_line = t(user_id, "filter_on") if pdf_only else t(user_id, "filter_off")
    header = t(user_id, "header").format(set_num=set_num, shown=shown, total=total, filter_line=f"\n{filter_line}")

    lines = [header, ""]

    for i in range(start, end):
        m = models[i]
        name = m.get("name", "Unnamed")
        designer = m.get("designer_name", "Unknown")
        parts = m.get("num_parts", "-")
        has_instr = bool(m.get("moc_has_building_instructions"))
        instr = t(user_id, "item_pdf_yes") if has_instr else t(user_id, "item_pdf_no")
        url = m.get("moc_url", "")

        lines.append(
            f"*{i+1}.* *{name}*\n"
            f"👤 {designer} • 🧩 {parts}\n"
            f"{instr}\n"
            f"{url}"
        )
        lines.append("")  

    return "\n".join(lines).strip()


def build_nav_keyboard(user_id: int, page: int, total_pages: int, pdf_only: bool) -> InlineKeyboardMarkup:
    btn_prev = InlineKeyboardButton(t(user_id, "btn_prev"), callback_data="nav:prev")
    btn_next = InlineKeyboardButton(t(user_id, "btn_next"), callback_data="nav:next")

    toggle_text = t(user_id, "btn_toggle_pdf_off") if pdf_only else t(user_id, "btn_toggle_pdf_on")
    btn_toggle = InlineKeyboardButton(toggle_text, callback_data="filter:toggle")

    btn_lang = InlineKeyboardButton(t(user_id, "btn_change_lang"), callback_data="lang:menu")

    row1 = []
    if page > 0:
        row1.append(btn_prev)
    if page < total_pages - 1:
        row1.append(btn_next)

    keyboard = []
    if row1:
        keyboard.append(row1)
    keyboard.append([btn_toggle, btn_lang])

    return InlineKeyboardMarkup(keyboard)


def build_start_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t(user_id, "btn_search"), callback_data="start:search")],
            [InlineKeyboardButton(t(user_id, "btn_lang"), callback_data="lang:menu")],
        ]
    )


def build_lang_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(TEXTS["ru"]["btn_lang_ru"], callback_data="lang:set:ru"),
                InlineKeyboardButton(TEXTS["en"]["btn_lang_en"], callback_data="lang:set:en"),
            ]
        ]
    )


# ==========================
# Handlers
# ==========================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not BOT_TOKEN or not REBRICKABLE_API_KEY:
        await update.message.reply_text(t(user_id, "error_keys"))
        return

    text = f"{t(user_id, 'start_title')}\n\n{t(user_id, 'start_body')}"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=build_start_keyboard(user_id))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(t(user_id, "help"))


async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("Choose / Выбери:", reply_markup=build_lang_keyboard(user_id))


async def alts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not BOT_TOKEN or not REBRICKABLE_API_KEY:
        await update.message.reply_text(t(user_id, "error_keys"))
        return

    if not context.args:
        await update.message.reply_text(t(user_id, "ask_set"), parse_mode=ParseMode.MARKDOWN)
        context.user_data["awaiting_set"] = True
        return

    set_num = normalize_set_num(context.args[0])
    await run_search_and_show(update, context, set_num)


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод номера набора после нажатия кнопки Search."""
    user_id = update.effective_user.id
    if not context.user_data.get("awaiting_set"):
        return

    set_num = normalize_set_num(update.message.text)
    context.user_data["awaiting_set"] = False
    await run_search_and_show(update, context, set_num)


async def run_search_and_show(update: Update, context: ContextTypes.DEFAULT_TYPE, set_num: str):
    user_id = update.effective_user.id

    if not looks_like_set_num(set_num):
        await update.message.reply_text(t(user_id, "bad_set"), parse_mode=ParseMode.MARKDOWN)
        return

    await update.message.reply_text(t(user_id, "fetching").format(set_num=set_num), parse_mode=ParseMode.MARKDOWN)

    try:
        models = fetch_alternates(set_num, page_size=PAGE_SIZE_API)
    except Exception as e:
        await update.message.reply_text(t(user_id, "error_api").format(msg=str(e)))
        return

    if not models:
        await update.message.reply_text(t(user_id, "not_found").format(set_num=set_num), parse_mode=ParseMode.MARKDOWN)
        return

    # по умолчанию показываем все, но запомним фильтр
    context.user_data["set_num"] = set_num
    context.user_data["all_models"] = models
    context.user_data["pdf_only"] = False
    context.user_data["page"] = 0

    await show_current_page(update, context, edit=False)


def apply_filter(models: List[Dict[str, Any]], pdf_only: bool) -> List[Dict[str, Any]]:
    if not pdf_only:
        return models
    return [m for m in models if bool(m.get("moc_has_building_instructions"))]


async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool):
    user_id = update.effective_user.id

    set_num = context.user_data.get("set_num")
    all_models = context.user_data.get("all_models", [])
    pdf_only = bool(context.user_data.get("pdf_only"))
    page = int(context.user_data.get("page", 0))

    models = apply_filter(all_models, pdf_only)
    if not models:
        # если включили PDF-only и стало пусто
        await (update.callback_query.message.edit_text if edit else update.effective_message.reply_text)(
            t(user_id, "not_found").format(set_num=set_num),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    total_pages = (len(models) + PAGE_SIZE_UI - 1) // PAGE_SIZE_UI
    page = max(0, min(page, total_pages - 1))
    context.user_data["page"] = page

    text = format_page(user_id, set_num, models, page, pdf_only)
    kb = build_nav_keyboard(user_id, page, total_pages, pdf_only)

    if edit:
        await update.callback_query.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb,
            disable_web_page_preview=True,
        )
    else:
        await update.effective_message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb,
            disable_web_page_preview=True,
        )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data or ""

    # Language menu
    if data == "lang:menu":
        await query.message.reply_text("Choose / Выбери:", reply_markup=build_lang_keyboard(user_id))
        return

    # Set language
    if data.startswith("lang:set:"):
        lang = data.split(":")[-1]
        set_lang(user_id, lang)
        msg = TEXTS[lang]["lang_changed_ru"] if lang == "ru" else TEXTS[lang]["lang_changed_en"]
        await query.message.reply_text(msg)
        # показать старт-меню уже на новом языке
        text = f"{t(user_id, 'start_title')}\n\n{t(user_id, 'start_body')}"
        await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=build_start_keyboard(user_id))
        return

    # Start search button
    if data == "start:search":
        context.user_data["awaiting_set"] = True
        await query.message.reply_text(t(user_id, "ask_set"), parse_mode=ParseMode.MARKDOWN)
        return

    # Navigation/filter requires having a search context
    if "all_models" not in context.user_data:
        await query.message.reply_text(t(user_id, "help"))
        return

    if data == "nav:prev":
        context.user_data["page"] = int(context.user_data.get("page", 0)) - 1
        await show_current_page(update, context, edit=True)
        return

    if data == "nav:next":
        context.user_data["page"] = int(context.user_data.get("page", 0)) + 1
        await show_current_page(update, context, edit=True)
        return

    if data == "filter:toggle":
        context.user_data["pdf_only"] = not bool(context.user_data.get("pdf_only"))
        context.user_data["page"] = 0
        await show_current_page(update, context, edit=True)
        return


# ==========================
# MAIN
# ==========================
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Set it as environment variable BOT_TOKEN.")
    if not REBRICKABLE_API_KEY:
        raise RuntimeError("REBRICKABLE_API_KEY is missing. Set it as environment variable REBRICKABLE_API_KEY.")

    # Fix for some Windows/Python builds: ensure event loop exists
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))
    app.add_handler(CommandHandler("alts", alts_cmd))

    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

    print("Bot is running...")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
