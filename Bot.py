from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# پیکربندی اولیه
logging.basicConfig(level=logging.INFO)
TOKEN = "7642204785:AAH9a1_uVbEyPUqb0zKW0dfxwg-MnJiWRww"
ADMIN_ID = 7213670865  # آیدی تلگرام ادمین

# مراحل گفتگو
LANG, ID, ACTION, PROJECT, WORK_DESC = range(5)

# حافظه موقت برای هر کارگر
user_data = {}

# پیام‌ها به زبان‌های مختلف
messages = {
    "en": {
        "welcome": "Please select your language:",
        "ask_id": "Please enter your personnel code:",
        "menu": "Select action:",
        "start_work": "Start Work",
        "end_work": "End Work",
        "ask_project": "Which construction site?",
        "ask_work": "What was built?",
        "logged_in": "You started work at {time}",
        "logged_out": "You ended work at {time}",
        "report": "🗓 Date: {date}\n🆔 ID: {id}\n⏱ In: {in_time}\n⏱ Out: {out_time}\n⌛ Worked: {duration}\n🏗 Site: {site}\n🧱 Work: {desc}",
    },
    "de": {
        "welcome": "Bitte wählen Sie Ihre Sprache:",
        "ask_id": "Bitte geben Sie Ihren Personalkode ein:",
        "menu": "Aktion wählen:",
        "start_work": "Arbeit beginnen",
        "end_work": "Arbeit beenden",
        "ask_project": "Welche Baustelle?",
        "ask_work": "Was wurde gebaut?",
        "logged_in": "Sie haben die Arbeit um {time} begonnen",
        "logged_out": "Sie haben die Arbeit um {time} beendet",
        "report": "🗓 Datum: {date}\n🆔 ID: {id}\n⏱ Start: {in_time}\n⏱ Ende: {out_time}\n⌛ Dauer: {duration}\n🏗 Baustelle: {site}\n🧱 Arbeit: {desc}",
    },
    "pl": {
        "welcome": "Wybierz swój język:",
        "ask_id": "Wprowadź swój kod pracownika:",
        "menu": "Wybierz działanie:",
        "start_work": "Rozpocznij pracę",
        "end_work": "Zakończ pracę",
        "ask_project": "Na której budowie?",
        "ask_work": "Co zostało zbudowane?",
        "logged_in": "Rozpocząłeś pracę o {time}",
        "logged_out": "Zakończyłeś pracę o {time}",
        "report": "🗓 Data: {date}\n🆔 ID: {id}\n⏱ Start: {in_time}\n⏱ Koniec: {out_time}\n⌛ Czas pracy: {duration}\n🏗 Budowa: {site}\n🧱 Praca: {desc}",
    }
}

# زبان‌های موجود
langs = {"🇬🇧 English": "en", "🇩🇪 Deutsch": "de", "🇵🇱 Polski": "pl"}

# شروع گفتگو
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(k, callback_data=v)] for k, v in langs.items()]
    await update.message.reply_text("Please select your language:", reply_markup=InlineKeyboardMarkup(keyboard))
    return LANG

# انتخاب زبان
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data["lang"] = lang
    await query.message.reply_text(messages[lang]["ask_id"])
    return ID

# ذخیره کد پرسنلی
async def save_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["id"] = update.message.text.strip()
    lang = context.user_data["lang"]
    buttons = [
        [InlineKeyboardButton(messages[lang]["start_work"], callback_data="start")],
        [InlineKeyboardButton(messages[lang]["end_work"], callback_data="end")]
    ]
    await update.message.reply_text(messages[lang]["menu"], reply_markup=InlineKeyboardMarkup(buttons))
    return ACTION

# شروع یا پایان کار
async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    user_id = query.from_user.id
    lang = context.user_data["lang"]
    
    if action == "start":
        context.user_data["in_time"] = datetime.now()
        await query.message.reply_text(messages[lang]["logged_in"].format(time=context.user_data["in_time"].strftime("%H:%M")))
        return ConversationHandler.END
    else:
        context.user_data["out_time"] = datetime.now()
        await query.message.reply_text(messages[lang]["ask_project"])
        return PROJECT

# دریافت محل پروژه
async def get_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["project"] = update.message.text.strip()
    lang = context.user_data["lang"]
    await update.message.reply_text(messages[lang]["ask_work"])
    return WORK_DESC

# دریافت شرح کار و ارسال گزارش
async def get_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["desc"] = update.message.text.strip()
    lang = context.user_data["lang"]

    in_time = context.user_data["in_time"]
    out_time = context.user_data["out_time"]
    duration = out_time - in_time
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60

    report = messages[lang]["report"].format(
        date=in_time.strftime("%Y-%m-%d"),
        id=context.user_data["id"],
        in_time=in_time.strftime("%H:%M"),
        out_time=out_time.strftime("%H:%M"),
        duration=f"{hours}h {minutes}m",
        site=context.user_data["project"],
        desc=context.user_data["desc"]
    )

    await update.message.reply_text(messages[lang]["logged_out"].format(time=out_time.strftime("%H:%M")))
    await context.bot.send_message(chat_id=ADMIN_ID, text=report)
    return ConversationHandler.END

# اجرای بات
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [CallbackQueryHandler(set_language)],
            ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_id)],
            ACTION: [CallbackQueryHandler(handle_action)],
            PROJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_project)],
            WORK_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_work)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.run_polling()
