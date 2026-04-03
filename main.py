import os
import telebot
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import threading

# --- কনফিগারেশন ---
API_TOKEN = '8762986628:AAFDHx75rzOBJGWFp8ACTGliil2T4rItlbw'
MONGODB_URI = "mongodb+srv://Musfiqur_rahman:musfiqur@cluster0.qxu7ycp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

app = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN)
client = MongoClient(MONGODB_URI)
db = client['reward_bee']
users_collection = db['users']

# --- টেলিগ্রাম বোট লজিক ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name
    
    # ইউজার ডাটাবেসে না থাকলে অটো-রেজিস্ট্রেশন
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({
            "user_id": user_id,
            "username": first_name,
            "balance": 0
        })

    # বাটন সেটআপ (সরাসরি আপনার index.html ওপেন হবে)
    markup = telebot.types.InlineKeyboardMarkup()
    web_app_url = "https://reward-bee-bot.onrender.com" 
    
    button = telebot.types.InlineKeyboardButton(
        text="💰 কাজ শুরু করুন", 
        web_app=telebot.types.WebAppInfo(url=web_app_url)
    )
    markup.add(button)

    bot.send_message(message.chat.id, f"স্বাগতম {first_name}!\nনিচের বাটনে ক্লিক করে সরাসরি অ্যাপটি ওপেন করুন। কোনো লগইন লাগবে না।", reply_markup=markup)

# --- ফ্লাস্ক রুট (সরাসরি ড্যাশবোর্ড) ---
@app.route('/')
def index():
    # এটি সরাসরি আপনার index.html লোড করবে
    return render_template('index.html')

# API: জাভাস্ক্রিপ্ট দিয়ে ব্যালেন্স এবং নাম দেখানোর জন্য
@app.route('/api/get_user/<user_id>')
def get_user(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        return jsonify({
            "status": "success",
            "name": user['username'],
            "balance": user['balance']
        })
    return jsonify({"status": "error", "message": "User not found"}), 404

# বোট রান করার জন্য থ্রেড
def run_bot():
    bot.remove_webhook()
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
