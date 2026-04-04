import os
import telebot
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
import threading

# --- কনফিগারেশন ---
API_TOKEN = '8762986628:AAFEBHZ2x7jTNWkC8Z-BaXvGWMaS-es4K2U'
MONGODB_URI = "mongodb+srv://Musfiqur_rahman:musfiqur@cluster0.qxu7ycp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

app = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN)
client = MongoClient(MONGODB_URI)
db = client['reward_bee']
users_collection = db['users']

# --- টেলিগ্রাম বোট ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name
    
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "username": first_name, "balance": 0})

    markup = telebot.types.InlineKeyboardMarkup()
    web_app_url = "https://reward-bee-bot.onrender.com" 
    button = telebot.types.InlineKeyboardButton(text="💰 কাজ শুরু করুন", web_app=telebot.types.WebAppInfo(url=web_app_url))
    markup.add(button)
    bot.send_message(message.chat.id, f"স্বাগতম {first_name}!", reply_markup=markup)

# --- ফ্লাস্ক রুট ---
@app.route('/')
def index():
    # এটি শুধু আপনার index.html ফাইলটি দেখাবে
    return render_template('index.html')

# API: ইউজার ডাটা পাঠানোর জন্য
@app.route('/api/get_user/<user_id>')
def get_user(user_id):
    try:
        user = users_collection.find_one({"user_id": str(user_id)})
        if user:
            return jsonify({
                "status": "success", 
                "name": user['username'], 
                "balance": user['balance'],
                "user_id": user['user_id']
            })
        return jsonify({"status": "error", "message": "User not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# বোট পোলিং রান করার ফাংশন
def run_bot():
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot error: {e}")

if __name__ == "__main__":
    # বোটের কোনো পুরনো পেন্ডিং রিকোয়েস্ট থাকলে তা মুছে ফেলা
    bot.remove_webhook()
    
    # বোটকে আলাদা থ্রেডে চালু করা
    # non_stop=True এবং interval=1 দিলে কানেকশন আরও স্টেবল থাকে
    threading.Thread(target=lambda: bot.infinity_polling(timeout=10, long_polling_timeout=5), daemon=True).start()
    
    # ফ্লাস্ক রান করা (Render-এর জন্য)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
