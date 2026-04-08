const express = require('express');
const mongoose = require('mongoose');
const axios = require('axios');
const path = require('path');
const app = express();

app.use(express.json());
app.use(express.static('public'));

// --- কনফিগারেশন (আপনার ডাটা এখানে দিন) ---
const MONGO_URI = "mongodb+srv://Musfiqur_rahman:musfiqur@cluster0.qxu7ycp.mongodb.net/?appName=Cluster0";
const BOT_TOKEN = "8762986628:AAFEBHZ2x7jTNWkC8Z-BaXvGWMaS-es4K2U"; 

// --- ডাটাবেজ মডেল ---
const ConfigSchema = new mongoose.Schema({
    links: [String],
    reward: { type: Number, default: 5 },
    minW: { type: Number, default: 500 },
    ads: { home: String, task: String, pay: String, prof: String }
});
const Config = mongoose.model('Config', ConfigSchema);

const UserSchema = new mongoose.Schema({
    id: { type: String, unique: true },
    balance: { type: Number, default: 0 },
    name: String
});
const User = mongoose.model('User', UserSchema);

// --- ডাটাবেজ কানেকশন ---
mongoose.connect(MONGO_URI)
    .then(() => {
        console.log("MongoDB Atlas Connected! 🚀");
        seedConfig();
    })
    .catch(err => console.log("DB Connection Error: ", err));

// --- API এন্ডপয়েন্টস ---

// ১. কনফিগ লোড করা
app.get('/api/config', async (req, res) => {
    const config = await Config.findOne();
    res.json(config || {});
});

// ২. ইউজার ডাটা চেক/তৈরি
app.get('/api/user/:id', async (req, res) => {
    try {
        let user = await User.findOne({ id: req.params.id });
        if (!user) {
            user = new User({ id: req.params.id, balance: 0 });
            await user.save();
        }
        res.json(user);
    } catch (e) { res.status(500).json(e); }
});

// ৩. ব্যালেন্স আপডেট ও বট মেসেজ
app.post('/api/update_balance', async (req, res) => {
    const { userId, amount } = req.body;
    try {
        const user = await User.findOneAndUpdate(
            { id: userId }, 
            { $inc: { balance: amount } }, 
            { new: true }
        );
        
        // টেলিগ্রাম মেসেজ পাঠানো
        await axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
            chat_id: userId,
            text: `✅ <b>টাস্ক সম্পন্ন!</b>\nআপনি পেয়েছেন: ৳${amount}\nবর্তমান ব্যালেন্স: ৳${user.balance}`,
            parse_mode: 'HTML'
        });

        res.json({ success: true, balance: user.balance });
    } catch (e) { res.status(500).json({ success: false }); }
});

// ৪. অ্যাডমিন প্যানেল আপডেট
app.post('/api/admin/update_config', async (req, res) => {
    try {
        await Config.findOneAndUpdate({}, req.body, { upsert: true });
        res.json({ success: true });
    } catch (e) { res.status(500).json({ success: false }); }
});

// ডিফল্ট কনফিগ তৈরি (যদি না থাকে)
async function seedConfig() {
    const count = await Config.countDocuments();
    if (count === 0) {
        await Config.create({
            links: ["https://google.com"],
            reward: 5,
            minW: 500,
            ads: { home: "", task: "", pay: "", prof: "" }
        });
    }
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
        });
    }
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server is running on port ${PORT}`));
