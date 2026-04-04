import os
import telebot
from flask import Flask, render_template, jsonify
from pymongo import MongoClient
import threading
import time

# --- নতুন API টোকেন ---
API_TOKEN = '8762986628:AAFEBHZ2x7jTNWkC8Z-BaXvGWMaS-es4K2U'

# --- ডাটাবেস কানেকশন ---
MONGODB_URI = "mongodb+srv://Musfiqur_rahman:musfiqur@cluster0.qxu7ycp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

app = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN)

try:
    client = MongoClient(MONGODB_URI)
    db = client['reward_bee']
    users_collection = db['users']
    print("MongoDB Connected Successfully!")
except Exception as e:
    print(f"MongoDB Connection Error: {e}")

# --- টেলিগ্রাম বোট লজিক ---
@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = str(message.from_user.id)
        first_name = message.from_user.first_name
        
        # ইউজার ডাটাবেসে না থাকলে তৈরি করা
        if not users_collection.find_one({"user_id": user_id}):
            users_collection.insert_one({
                "user_id": user_id, 
                "username": first_name, 
                "balance": 0
            })

        markup = telebot.types.InlineKeyboardMarkup()
        # আপনার রেন্ডার ইউআরএল
        web_app_url = "https://reward-bee-bot.onrender.com" 
        button = telebot.types.InlineKeyboardButton(
            text="💰 কাজ শুরু করুন (লগইন ছাড়া)", 
            web_app=telebot.types.WebAppInfo(url=web_app_url)
        )
        markup.add(button)
        bot.send_message(message.chat.id, f"স্বাগতম {first_name}!\nনিচের বাটনে ক্লিক করে সরাসরি অ্যাপটি ওপেন করুন।", reply_markup=markup)
    except Exception as e:
        print(f"Start command error: {e}")

# --- ফ্লাস্ক রুট (ড্যাশবোর্ড) ---
@app.route('/')
def index():
    return render_template('index.html')

# API: জাভাস্ক্রিপ্ট দিয়ে ইউজারের তথ্য আনা
@app.route('/api/get_user/<user_id>')
def get_user(user_id):
    user = users_collection.find_one({"user_id": str(user_id)})
    if user:
        return jsonify({
            "status": "success", 
            "name": user['username'], 
            "balance": user['balance'],
            "user_id": user['user_id']
        })
    return jsonify({"status": "error", "message": "User not found"}), 404

# --- বোট পোলিং ফাংশন (Conflict এড়ানোর জন্য) ---
def run_bot():
    while True:
        try:
            bot.remove_webhook() # পুরনো কানেকশন ক্লিন করা
            print("Bot is polling...")
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5) # এরর হলে ৫ সেকেন্ড অপেক্ষা করে আবার চেষ্টা করবে

if __name__ == "__main__":
    # বোটকে আলাদা থ্রেডে চালানো
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Render এর পোর্টে Flask চালানো
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
