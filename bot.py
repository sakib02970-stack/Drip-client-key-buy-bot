import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

import random
import string
import json
import threading
import traceback
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

ADMIN_GROUP_ID = -1003972224951
UPDATE_CHANNEL = "https://t.me/your_update_channel"
SUPPORT_URL = "https://t.me/MDKhairul223334"
YT_VIDEO_URL = "https://t.me/MDKhairul223334"
LATEST_FILE_URL = "https://t.me/djsksbdsknsn"
BKASH_NUMBER = "01780872594"

PRICES = {
    "1_day": {"days": 1, "price": 90, "label_bn": "1 DIN - 90 TAKA", "label_en": "1 Day - 90 Taka"},
    "3_day": {"days": 3, "price": 190, "label_bn": "3 DIN - 190 TAKA", "label_en": "3 Day - 190 Taka"},
    "7_day": {"days": 7, "price": 370, "label_bn": "7 DIN - 370 TAKA", "label_en": "7 Day - 370 Taka"},
    "15_day": {"days": 15, "price": 650, "label_bn": "15 DIN - 650 TAKA", "label_en": "15 Day - 650 Taka"},
    "30_day": {"days": 30, "price": 900, "label_bn": "30 DIN - 900 TAKA", "label_en": "30 Day - 900 Taka"},
}

# ==================== DATA PERSISTENCE ====================
DATA_FILE = "bot_data.json"

def load_data():
    """Load data from JSON file on startup"""
    global user_data, pending_payments, used_trxids, purchase_log
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_data = {int(k): v for k, v in data.get("user_data", {}).items()}
                pending_payments = data.get("pending_payments", {})
                used_trxids = set(data.get("used_trxids", []))
                purchase_log = data.get("purchase_log", [])
                print(f"✅ Data loaded: {len(user_data)} users, {len(used_trxids)} used TrxIDs, {len(purchase_log)} logs")
        else:
            print("📁 No data file found, starting fresh")
    except Exception as e:
        print(f"❌ Error loading data: {e}")

def save_data():
    """Save data to JSON file"""
    try:
        data = {
            "user_data": user_data,
            "pending_payments": pending_payments,
            "used_trxids": list(used_trxids),
            "purchase_log": purchase_log
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("💾 Data saved successfully")
    except Exception as e:
        print(f"❌ Error saving data: {e}")

user_data = {}
pending_payments = {}
used_trxids = set()
purchase_log = []

def build_texts():
    texts = {"bn": {}, "en": {}}
    
    texts["bn"]["welcome"] = "👋 হেই {name}!\n\n🎉 WELCOME TO OUR PANEL BUY BOT\n\n📋 PANEL LIST: ONLY DRIP CLIENT"
    texts["bn"]["select_package"] = "🛒 DRIP CLIENT PRICE LIST\n\n📦 প্যাকেজ সিলেক্ট করুন:"
    texts["bn"]["purchase_summary"] = (
        "🛒 Purchase Summary\n"
        "📦 প্যাকেজ: {package}\n"
        "💰 মূল্য: {price} টাকা\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💳 Payment Methods:\n\n"
        "🟣 bKash (Send Money):\n"
        "📱 {number}\n"
        "👆 (ক্লিক করে কপি করুন)\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ উপরের নাম্বারে টাকা পাঠান\n"
        "2️⃣ Transaction ID (TrxID) কপি করুন\n"
        "3️⃣ TrxID এখানে পাঠান\n\n"
        "⚠️ স্ক্রিনশট পাঠাবেন না, শুধু TrxID টাইপ করুন"
    )
    texts["bn"]["payment_sent"] = (
        "⏳ আপনার পেমেন্ট রিভিউয়ের জন্য পাঠানো হয়েছে!\n\n"
        "📦 প্যাকেজ: {package_name}\n"
        "💰 মূল্য: {price_value} টাকা\n"
        "👤 ক্রেতা: {buyer_name}\n"
        "💳 TrxID: {trxid}\n"
        "🆔 Buying ID: {buying_id}\n\n"
        "👨‍💼 অ্যাডমিন চেক করার পর আপনাকে KEY দেওয়া হবে।\n\n"
        "⏱️ অনুগ্রহ করে অপেক্ষা করুন..."
    )
    texts["bn"]["payment_approved"] = (
        "✅ YOUR PAYMENT CHECK DONE\n\n"
        "🔑 YOUR KEY: {user_key}\n"
        "🆔 BUYING ID: {buying_id}\n"
        "📦 DRIP CLIENT APK : {update_channel}\n\n"
        "🎉 ধন্যবাদ! আপনার KEY সক্রিয় করা হয়েছে।"
    )
    texts["bn"]["payment_rejected"] = (
        "❌ PAYMENT CHECK\n\n"
        "⚠️ FAKE PAYMENT DETECTED\n\n"
        "🚫 আপনার পেমেন্ট সঠিক হয়নি।\n"
        "💳 সঠিক TrxID দিয়ে আবার চেষ্টা করুন।"
    )
    texts["bn"]["trxid_used"] = (
        "🚫 এই TrxID আগেই ব্যবহার করা হয়েছে!\n\n"
        "⚠️ TrxID: {trxid}\n"
        "❌ আপনি এই TrxID দিয়ে আবার অর্ডার করতে পারবেন না।\n\n"
        "💳 নতুন পেমেন্ট করুন এবং নতুন TrxID দিন।"
    )
    texts["bn"]["cancel"] = "❌ ক্যান্সেল"
    texts["bn"]["back"] = "🔙 ব্যাক"
    texts["bn"]["buy_key"] = "🛒 BUY DRIP CLIENT KEY"
    texts["bn"]["latest_files"] = "📁 LATEST FILES"
    texts["bn"]["how_to_buy"] = "❓ HOW TO BUY KEY"
    texts["bn"]["join_channel"] = "📢 JOIN UPDATE CHANNEL"
    texts["bn"]["support"] = "💬 SUPPORT"
    texts["bn"]["new_purchase"] = (
        "🆕 NEW PURCHASE\n\n"
        "📦 প্যাকেজ: {package}\n"
        "💰 মূল্য: {price} টাকা\n"
        "👤 ক্রেতা: {buyer_name}\n"
        "🆔 Buyer ID: {buyer_id}\n"
        "💳 TrxID: {trxid}\n"
        "🔢 Buying ID: {buying_id}\n\n"
        "⚠️ : @MDKhairul223334"
    )
    texts["bn"]["admin_approved"] = (
        "✅ Payment Approved!\n\n"
        "🔑 Key: {user_key}\n"
        "🆔 Buying ID: {buying_id}"
    )
    texts["bn"]["admin_rejected"] = (
        "❌ Payment Rejected!\n\n"
        "🆔 Buying ID: {buying_id}"
    )
    texts["bn"]["checking"] = "⏳ ADMIN CHECKING PAYMENT\n\nঅপেক্ষা করুন..."
    
    texts["en"]["welcome"] = "👋 Hey {name}!\n\n🎉 WELCOME TO OUR PANEL BUY BOT\n\n📋 PANEL LIST: ONLY DRIP CLIENT"
    texts["en"]["select_package"] = "🛒 DRIP CLIENT PRICE LIST\n\n📦 Click Package To Buy Key:"
    texts["en"]["purchase_summary"] = (
        "🛒 Purchase Summary\n"
        "📦 Package: {package}\n"
        "💰 Price: {price} Taka\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💳 Payment Methods:\n\n"
        "🟣 bKash (Send Money):\n"
        "📱 {number}\n"
        "👆 (Click to Copy)\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ Send amount to any number above\n"
        "2️⃣ Copy the Transaction ID (TrxID)\n"
        "3️⃣ Send the TrxID here\n\n"
        "⚠️ Please do not send screenshots, type the TrxID only"
    )
    texts["en"]["payment_sent"] = (
        "⏳ Your payment has been sent for review!\n\n"
        "📦 Package: {package_name}\n"
        "💰 Price: {price_value} Taka\n"
        "👤 Buyer: {buyer_name}\n"
        "💳 TrxID: {trxid}\n"
        "🆔 Buying ID: {buying_id}\n\n"
        "👨‍💼 Admin will check and give you the KEY.\n\n"
        "⏱️ Please wait..."
    )
    texts["en"]["payment_approved"] = (
        "✅ YOUR PAYMENT CHECK DONE\n\n"
        "🔑 YOUR KEY: {user_key}\n"
        "🆔 BUYING ID: {buying_id}\n"
        "📦 DRIP CLIENT APK : {update_channel}\n\n"
        "🎉 Thank you! Your key has been activated."
    )
    texts["en"]["payment_rejected"] = (
        "❌ PAYMENT CHECK\n\n"
        "⚠️ FAKE PAYMENT DETECTED\n\n"
        "🚫 Your payment was not correct.\n"
        "💳 Please try again with correct TrxID."
    )
    texts["en"]["trxid_used"] = (
        "🚫 This TrxID has already been used!\n\n"
        "⚠️ TrxID: {trxid}\n"
        "❌ You cannot order again with this TrxID.\n\n"
        "💳 Please make a new payment and send a new TrxID."
    )
    texts["en"]["cancel"] = "❌ Cancel"
    texts["en"]["back"] = "🔙 Back"
    texts["en"]["buy_key"] = "🛒 BUY DRIP CLIENT KEY"
    texts["en"]["latest_files"] = "📁 LATEST FILES"
    texts["en"]["how_to_buy"] = "❓ HOW TO BUY KEY"
    texts["en"]["join_channel"] = "📢 JOIN UPDATE CHANNEL"
    texts["en"]["support"] = "💬 SUPPORT"
    texts["en"]["new_purchase"] = (
        "🆕 NEW PURCHASE\n\n"
        "📦 Package: {package}\n"
        "💰 Price: {price} Taka\n"
        "👤 Buyer: {buyer_name}\n"
        "🆔 Buyer ID: {buyer_id}\n"
        "💳 TrxID: {trxid}\n"
        "🔢 Buying ID: {buying_id}\n\n"
        "⚠️ : @MDKhairul223334"
    )
    texts["en"]["admin_approved"] = (
        "✅ Payment Approved!\n\n"
        "🔑 Key: {user_key}\n"
        "🆔 Buying ID: {buying_id}"
    )
    texts["en"]["admin_rejected"] = (
        "❌ Payment Rejected!\n\n"
        "🆔 Buying ID: {buying_id}"
    )
    texts["en"]["checking"] = "⏳ ADMIN CHECKING PAYMENT\n\nPlease wait..."
    return texts

TEXTS = build_texts()

def generate_buying_id():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

def get_text(user_id, text_key, **kwargs):
    lang = user_data.get(user_id, {}).get("lang", "en")
    return TEXTS[lang].get(text_key, TEXTS["en"][text_key]).format(**kwargs)

def language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇧🇩 BANGLA", callback_data="lang_bn"),
         InlineKeyboardButton("🇺🇸 ENGLISH", callback_data="lang_en")]
    ])

def main_menu_keyboard(lang):
    t = TEXTS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["buy_key"], callback_data="buy_key")],
        [InlineKeyboardButton(t["latest_files"], url=LATEST_FILE_URL),
         InlineKeyboardButton(t["how_to_buy"], url=YT_VIDEO_URL)],
        [InlineKeyboardButton(t["join_channel"], url=UPDATE_CHANNEL),
         InlineKeyboardButton(t["support"], url=SUPPORT_URL)],
    ])

def package_keyboard(lang):
    t = TEXTS[lang]
    keyboard = []
    for key, data in PRICES.items():
        label = data["label_bn"] if lang == "bn" else data["label_en"]
        keyboard.append([InlineKeyboardButton(label, callback_data="pkg_" + key)])
    keyboard.append([InlineKeyboardButton(t["back"], callback_data="back_menu")])
    return InlineKeyboardMarkup(keyboard)

def payment_keyboard(lang, buying_id):
    t = TEXTS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["cancel"], callback_data="cancel_" + buying_id)]
    ])

async def start(update: Update, context):
    user = update.effective_user
    user_id = user.id
    if user_id in user_data and "lang" in user_data[user_id]:
        lang = user_data[user_id]["lang"]
        text = get_text(user_id, "welcome", name=user.first_name)
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(lang))
    else:
        await update.message.reply_text(
            "🌐 PLEASE SELECT LANGUAGE / ভাষা নির্বাচন করুন:\n\n"
            "🇧🇩 BANGLA\n🇺🇸 ENGLISH",
            reply_markup=language_keyboard()
        )

async def language_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    lang = query.data.split("_")[1]
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["lang"] = lang
    save_data()  # Save after language change
    name = update.effective_user.first_name
    text = get_text(user_id, "welcome", name=name)
    await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang))

async def main_menu_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    lang = user_data.get(user_id, {}).get("lang", "en")
    data = query.data
    if data == "buy_key":
        text = get_text(user_id, "select_package")
        await query.edit_message_text(text, reply_markup=package_keyboard(lang))
    elif data == "back_menu":
        name = update.effective_user.first_name
        text = get_text(user_id, "welcome", name=name)
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang))

async def package_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    try:
        user_id = update.effective_user.id
        lang = user_data.get(user_id, {}).get("lang", "en")
        pkg_key = query.data.replace("pkg_", "")
        if pkg_key not in PRICES:
            await query.edit_message_text("❌ Invalid package. Try /start")
            return
        pkg = PRICES[pkg_key]
        buying_id = generate_buying_id()
        pending_payments[buying_id] = {
            "user_id": user_id,
            "package": pkg_key,
            "days": pkg["days"],
            "price": pkg["price"],
            "username": update.effective_user.username or "NoUsername",
            "first_name": update.effective_user.first_name,
            "status": "pending"
        }
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["current_buying_id"] = buying_id
        save_data()  # Save after creating payment
        package_name = pkg["label_bn"] if lang == "bn" else pkg["label_en"]
        text = get_text(user_id, "purchase_summary", package=package_name, price=pkg["price"], number=BKASH_NUMBER)
        await query.edit_message_text(text, reply_markup=payment_keyboard(lang, buying_id))
    except Exception as e:
        print("❌ PACKAGE ERROR:", e)
        traceback.print_exc()
        await query.edit_message_text("❌ Error. Try /start again.")

async def cancel_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    buying_id = query.data.replace("cancel_", "")
    if buying_id in pending_payments:
        del pending_payments[buying_id]
        save_data()  # Save after cancel
    lang = user_data.get(user_id, {}).get("lang", "en")
    name = update.effective_user.first_name
    text = get_text(user_id, "welcome", name=name)
    await query.edit_message_text(text, reply_markup=main_menu_keyboard(lang))

async def handle_trxid(update: Update, context):
    print("=" * 60)
    print("📝 TRXID HANDLER CALLED")
    print("=" * 60)
    try:
        user_id = update.effective_user.id
        print(f"👤 User ID: {user_id}")
        lang = user_data.get(user_id, {}).get("lang", "en")
        print(f"🌐 Lang: {lang}")
        trxid = update.message.text.strip().upper()
        print(f"💳 TrxID: {trxid}")
        
        # CHECK IF TRXID ALREADY USED
        if trxid in used_trxids:
            print(f"🚫 DUPLICATE TRXID DETECTED: {trxid}")
            await update.message.reply_text(
                get_text(user_id, "trxid_used", trxid=trxid)
            )
            return
        
        buying_id = user_data.get(user_id, {}).get("current_buying_id")
        print(f"🆔 Current buying_id: {buying_id}")
        
        if not buying_id:
            print("❌ ERROR: No buying_id found")
            await update.message.reply_text("❌ No pending payment. Start with /start")
            return
            
        if buying_id not in pending_payments:
            print(f"❌ ERROR: buying_id {buying_id} not in pending_payments")
            print(f"📋 Pending payments: {list(pending_payments.keys())}")
            await update.message.reply_text("❌ Payment expired. Start with /start")
            return
            
        payment = pending_payments[buying_id]
        payment["trxid"] = trxid
        print(f"💰 Payment found: {payment}")
        
        # ADD TRXID TO USED SET
        used_trxids.add(trxid)
        print(f"✅ TrxID added to used list. Total used: {len(used_trxids)}")
        
        pkg = PRICES[payment["package"]]
        package_name = pkg["label_en"]
        buyer_name = payment.get("first_name", "Unknown")
        price_value = payment["price"]
        print(f"📦 Package: {package_name}, 💰 Price: {price_value}")
        
        # LOG THE PURCHASE
        log_entry = {
            "time": str(datetime.now()),
            "buying_id": buying_id,
            "user_id": user_id,
            "buyer_name": buyer_name,
            "package": package_name,
            "price": price_value,
            "trxid": trxid,
            "status": "pending"
        }
        purchase_log.append(log_entry)
        save_data()  # Save after logging
        print(f"📝 Purchase logged. Total logs: {len(purchase_log)}")
        
        # Build admin message
        admin_msg = (
            f"🆕 NEW PURCHASE\n\n"
            f"📦 প্যাকেজ: {package_name}\n"
            f"💰 মূল্য: {price_value} টাকা\n"
            f"👤 ক্রেতা: {buyer_name}\n"
            f"🆔 Buyer ID: {user_id}\n"
            f"💳 TrxID: {trxid}\n"
            f"🔢 Buying ID: {buying_id}\n\n"
            f"⚠️ : @MDKhairul223334"
        )
        print(f"📨 Admin message built")
        
        # Send to admin group
        print(f"📤 Sending to admin group: {ADMIN_GROUP_ID}")
        await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_msg)
        print("✅ Admin message sent successfully!")
        
        # Reply to user - FIX: use price_value instead of payment["price"]
        user_msg = get_text(user_id, "payment_sent", 
                          package_name=package_name, 
                          price_value=price_value, 
                          buyer_name=buyer_name, 
                          trxid=trxid, 
                          buying_id=buying_id)
        await update.message.reply_text(user_msg)
        print("✅ User reply sent successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in handle_trxid: {e}")
        traceback.print_exc()
        try:
            await update.message.reply_text("❌ Error processing payment. Please contact @MDKhairul223334")
        except:
            pass

async def ok_command(update: Update, context):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Usage: /ok <buying_id> <key>")
            return
        buying_id = args[0]
        user_key = args[1]
        if buying_id not in pending_payments:
            await update.message.reply_text("❌ Buying ID not found!")
            return
        payment = pending_payments[buying_id]
        user_id = payment["user_id"]
        
        # UPDATE LOG STATUS
        for log in purchase_log:
            if log["buying_id"] == buying_id:
                log["status"] = "approved"
                log["key"] = user_key
                break
        
        user_text = get_text(user_id, "payment_approved", 
                          user_key=user_key, 
                          buying_id=buying_id, 
                          update_channel=UPDATE_CHANNEL)
        await context.bot.send_message(chat_id=user_id, text=user_text)
        admin_text = get_text(user_id, "admin_approved", user_key=user_key, buying_id=buying_id)
        await update.message.reply_text(admin_text)
        del pending_payments[buying_id]
        save_data()  # Save after approval
        if user_id in user_data and "current_buying_id" in user_data[user_id]:
            del user_data[user_id]["current_buying_id"]
    except Exception as e:
        print("❌ OK COMMAND ERROR:", e)
        traceback.print_exc()
        await update.message.reply_text("❌ Error: " + str(e))

async def no_command(update: Update, context):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    try:
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("❌ Usage: /no <buying_id>")
            return
        buying_id = args[0]
        if buying_id not in pending_payments:
            await update.message.reply_text("❌ Buying ID not found!")
            return
        payment = pending_payments[buying_id]
        user_id = payment["user_id"]
        
        # UPDATE LOG STATUS
        for log in purchase_log:
            if log["buying_id"] == buying_id:
                log["status"] = "rejected"
                break
        
        user_text = get_text(user_id, "payment_rejected")
        await context.bot.send_message(chat_id=user_id, text=user_text)
        admin_text = get_text(user_id, "admin_rejected", buying_id=buying_id)
        await update.message.reply_text(admin_text)
        del pending_payments[buying_id]
        save_data()  # Save after rejection
        if user_id in user_data and "current_buying_id" in user_data[user_id]:
            del user_data[user_id]["current_buying_id"]
    except Exception as e:
        print("❌ NO COMMAND ERROR:", e)
        traceback.print_exc()
        await update.message.reply_text("❌ Error: " + str(e))

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Bot is Running!"

@flask_app.route("/health")
def health():
    return {"status": "ok", "pending": len(pending_payments), "used_trxids": len(used_trxids), "total_logs": len(purchase_log)}

@flask_app.route("/logs")
def logs():
    return {"logs": purchase_log}

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

def main():
    # Load saved data on startup
    load_data()
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^(buy_key|back_menu)$"))
    application.add_handler(CallbackQueryHandler(package_callback, pattern="^pkg_"))
    application.add_handler(CallbackQueryHandler(cancel_callback, pattern="^cancel_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_trxid))
    application.add_handler(CommandHandler("ok", ok_command))
    application.add_handler(CommandHandler("no", no_command))
    print("=" * 60)
    print("🤖 BOT IS RUNNING - Data persisted to bot_data.json")
    print("=" * 60)
    application.run_polling()

if __name__ == "__main__":
    main()
