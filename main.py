import os
import hashlib
import hmac
import time
from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "reward_bee_secure_secret_key" # আপনার ইচ্ছা মতো পরিবর্তন করতে পারেন

# --- কনফিগারেশন ---
API_TOKEN = '8762986628:AAFDHx75rzOBJGWFp8ACTGliil2T4rItlbw'
# কানেকশন স্ট্রিং আপডেট করা হয়েছে
MONGODB_URI = "mongodb+srv://Musfiqur_rahman:musfiqur@cluster0.qxu7ycp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGODB_URI)
db = client['reward_bee']
users_collection = db['users']
config_collection = db['config']

# --- UTILS ---
def verify_telegram_auth(auth_data):
    check_hash = auth_data.get('hash')
    auth_data_copy = auth_data.copy()
    del auth_data_copy['hash']
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(auth_data_copy.items())])
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    hash_res = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hash_res == check_hash

def get_admin_config():
    # অ্যাডমিন প্যানেল থেকে আসা কনফিগ ডাটাবেস থেকে আনা
    conf = config_collection.find_one({"type": "settings"})
    if not conf:
        # ডিফল্ট সেটিংস যদি ডাটাবেসে না থাকে
        return {
            "links": ["https://google.com"],
            "reward": 5, "minW": 500, "hourly": 10, "daily": 50,
            "ads": {"home": "", "task": "", "pay": "", "prof": ""}
        }
    return conf

# --- ROUTES ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('login.html')
    
    user_data = users_collection.find_one({"telegram_id": session['user_id']})
    config = get_admin_config()
    return render_template('index.html', user=user_data, config=config)

@app.route('/auth')
def auth():
    auth_data = request.args.to_dict()
    if verify_telegram_auth(auth_data):
        user_id = auth_data.get('id')
        user = users_collection.find_one({"telegram_id": user_id})
        
        if not user:
            users_collection.insert_one({
                "telegram_id": user_id,
                "name": auth_data.get('first_name'),
                "balance": 0,
                "total_earn": 0,
                "daily_count": 0,
                "hourly_count": 0,
                "last_task_time": 0,
                "referrals": []
            })
        
        session['user_id'] = user_id
        session.permanent = True # সেশন স্থায়ী করা
        return redirect('/')
    return "Authentication Failed", 403

# --- API ENDPOINTS ---

@app.route('/api/complete_task', methods=['POST'])
def complete_task():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    config = get_admin_config()
    user = users_collection.find_one({"telegram_id": session['user_id']})
    
    # সিম্পল চেক: দৈনিক লিমিট শেষ কি না
    if user['daily_count'] >= config['daily']:
        return jsonify({"success": False, "error": "Daily Limit Reached"}), 400

    # ব্যালেন্স ও কাউন্ট আপডেট
    new_balance = user['balance'] + config['reward']
    new_total = user['total_earn'] + config['reward']
    new_daily = user['daily_count'] + 1
    
    users_collection.update_one(
        {"telegram_id": session['user_id']},
        {"$set": {
            "balance": new_balance,
            "total_earn": new_total,
            "daily_count": new_daily,
            "last_task_time": int(time.time())
        }}
    )
    
    return jsonify({"success": True, "new_balance": new_balance, "new_daily": new_daily})

@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    user = users_collection.find_one({"telegram_id": session['user_id']})
    config = get_admin_config()
    
    if user['balance'] < int(data['amt']):
        return jsonify({"success": False, "error": "Insufficient Balance"})
    
    # এখানে পেমেন্ট রিকোয়েস্ট ডাটাবেসে সেভ করা বা বোট দিয়ে মেসেজ পাঠানোর লজিক হবে
    users_collection.update_one(
        {"telegram_id": session['user_id']},
        {"$inc": {"balance": -int(data['amt'])}}
    )
    return jsonify({"success": True})

# --- RENDER PORT CONFIGURATION ---
if __name__ == '__main__':
    # রেন্ডার থেকে পোর্ট নাম্বার নেওয়া, না থাকলে ডিফল্ট ৫০০৫
    port = int(os.environ.get("PORT", 5005))
    # ০.০.০.০ হোস্ট ব্যবহার করা জরুরি যাতে বাইরের নেটওয়ার্ক থেকে কানেক্ট হতে পারে
    app.run(host='0.0.0.0', port=port)
