import telebot
from pymongo import MongoClient
from telebot import types
import ssl

# --- কনফিগারেশন ---
API_TOKEN = '8762986628:AAFDHx75rzOBJGWFp8ACTGliil2T4rItlbw'
# কানেকশন স্ট্রিং আপডেট করা হয়েছে
MONGODB_URI = "mongodb+srv://Musfiqur_rahman:musfiqur@cluster0.qxu7ycp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# --- ডাটাবেস কানেকশন ---
users_col = None

def connect_db():
    global users_col
    try:
        # tlsAllowInvalidCertificates=True সরাসরি এখানে দেওয়া হয়েছে DNS সমস্যা এড়াতে
        client = MongoClient(
            MONGODB_URI, 
            serverSelectionTimeoutMS=10000, 
            tlsAllowInvalidCertificates=True
        )
        db = client["RewardBotDB"]
        users_col = db["users"]
        # কানেকশন চেক
        client.admin.command('ping')
        print("✅ সফলভাবে MongoDB কানেক্ট হয়েছে!")
    except Exception as e:
        print(f"❌ ডাটাবেস কানেকশনে সমস্যা: {e}")
        print("পরামর্শ: ফোনে VPN চালু করে পুনরায় চেষ্টা করুন।")

# কানেকশন কল করুন
connect_db()

bot = telebot.TeleBot(API_TOKEN)

# --- ইউজার ডেটা ম্যানেজমেন্ট ---
def get_user_data(user_id, name="User"):
    if users_col is None:
        return {"user_id": user_id, "name": name, "balance": 0.0, "referrals": 0, "total_ads": 0}
    
    user = users_col.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id, 
            "name": name, 
            "balance": 0.0, 
            "referrals": 0, 
            "total_ads": 0
        }
        users_col.insert_one(user)
    return user

# --- কিবোর্ড সেটআপ ---
def main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📺 অ্যাড দেখে আয়", callback_data="watch_ad"),
        types.InlineKeyboardButton("👤 ড্যাশবোর্ড", callback_data="dashboard"),
        types.InlineKeyboardButton("🔗 রেফারেল লিঙ্ক", callback_data="ref_link"),
        types.InlineKeyboardButton("💳 টাকা তুলুন", callback_data="withdraw")
    )
    return markup

# --- কমান্ড হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # রেফারেল বোনাস লজিক
    text_parts = message.text.split()
    if len(text_parts) > 1 and text_parts[1].isdigit():
        inviter_id = int(text_parts[1])
        # চেক করুন ইউজার নতুন কিনা
        if users_col is not None:
            existing_user = users_col.find_one({"user_id": user_id})
            if not existing_user and inviter_id != user_id:
                users_col.update_one(
                    {"user_id": inviter_id}, 
                    {"$inc": {"balance": 2.0, "referrals": 1}}
                )
                try:
                    bot.send_message(inviter_id, "🎉 অভিনন্দন! নতুন রেফারেলের জন্য ২ টাকা পেয়েছেন।")
                except: pass

    get_user_data(user_id, user_name)
    bot.send_message(
        message.chat.id, 
        f"স্বাগতম {user_name}! 👋\nনিচের বাটনগুলো ব্যবহার করে আয় করা শুরু করুন।", 
        reply_markup=main_menu_markup()
    )

# --- বাটন হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    
    if users_col is None:
        bot.answer_callback_query(call.id, "ডেটাবেস কানেক্ট নেই। ইন্টারনেট চেক করুন।", show_alert=True)
        return

    if call.data == "dashboard":
        user = get_user_data(user_id)
        msg = (
            f"👤 **ইউজার প্রোফাইল**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 ব্যালেন্স: {round(user['balance'], 2)} টাকা\n"
            f"👥 রেফারেল: {user['referrals']} জন\n"
            f"📺 দেখা অ্যাড: {user['total_ads']} টি\n"
            f"━━━━━━━━━━━━━━━"
        )
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=main_menu_markup(), parse_mode="Markdown")

    elif call.data == "watch_ad":
        # এখানে আপনার অ্যাড লিঙ্ক দিতে পারেন
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Claim Bonus", callback_data="claim_money"))
        bot.send_message(call.message.chat.id, "বিজ্ঞাপনটি দেখা শেষ হলে নিচের বাটনে ক্লিক করুন।", reply_markup=kb)

    elif call.data == "claim_money":
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": 0.50, "total_ads": 1}})
        bot.answer_callback_query(call.id, "অভিনন্দন! ০.৫০ টাকা যোগ হয়েছে।", show_alert=True)
        # অটোমেটিক ড্যাশবোর্ড আপডেট
        user = get_user_data(user_id)
        bot.send_message(call.message.chat.id, f"আপনার বর্তমান ব্যালেন্স: {user['balance']} টাকা।", reply_markup=main_menu_markup())

    elif call.data == "ref_link":
        bot_info = bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(call.message.chat.id, f"🔗 আপনার রেফারেল লিঙ্ক:\n`{link}`\n\nপ্রতিটি সফল রেফারে পাবেন ২ টাকা!", parse_mode="Markdown")

    elif call.data == "withdraw":
        user = get_user_data(user_id)
        if user['balance'] < 50:
            bot.answer_callback_query(call.id, "মিনিমাম ৫০ টাকা প্রয়োজন।", show_alert=True)
        else:
            bot.send_message(call.message.chat.id, "টাকা তুলতে আপনার বিকাশ নাম্বার লিখে এডমিনকে জানান।")

# --- রান বট ---
if __name__ == "__main__":
    print("🚀 বট সফলভাবে চালু হয়েছে...")
    bot.infinity_polling()
