import os
import telebot
from flask import Flask, render_template, jsonify
from pymongo import MongoClient
import threading

# --- সেটিংস ---
API_TOKEN = '8762986628:AAFDHx75rzOBJGWFp8ACTGliil2T4rItlbw'
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
    try:
        return render_template('index.html')
    except Exception as e:
        return str(e) # এরর সরাসরি স্ক্রিনে দেখাবে

@app.route('/api/get_user/<user_id>')
def get_user(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        return jsonify({"status": "success", "name": user['username'], "balance": user['balance']})
    return jsonify({"status": "error"}), 404

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
