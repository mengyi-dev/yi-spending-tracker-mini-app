from flask import Flask, request, jsonify
from telebot import TeleBot
import os
import json

# Initialize Flask and bot
app = Flask(__name__)
bot = TeleBot(os.environ.get('BOT_TOKEN'))
bot.set_webhook(url=f"{os.environ.get('VERCEL_URL', '')}/webhook")

@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def catch_all(path):
    return jsonify({
        'status': 'running',
        'webhook_url': f"{os.environ.get('VERCEL_URL', '')}/webhook",
        'bot_info': bot.get_me().__dict__ if bot.token else 'Bot token not set'
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = json.loads(json_string)
            bot.process_new_updates([update])
            return 'OK', 200
        return 'Error: Invalid content type', 400
    except Exception as e:
        return f'Error: {str(e)}', 500

@bot.message_handler(commands=['start'])
def start(message):
    webapp_url = f"https://t.me/{bot.get_me().username}/app"
    bot.reply_to(
        message,
        "សូមស្វាគមន៍មកកាន់កម្មវិធីតាមដានចំណាយ! 🎉\n\n"
        "ចុចលើប៊ូតុងខាងក្រោមដើម្បីចាប់ផ្តើម:",
        reply_markup={
            "inline_keyboard": [[{
                "text": "បើកកម្មវិធី 📱",
                "web_app": {"url": webapp_url}
            }]]
        }
    )

@bot.message_handler(content_types=['web_app_data'])
def web_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        if data.get('action') == 'generate_report':
            report = data.get('report', 'គ្មានទិន្នន័យ')
            bot.reply_to(message, report)
    except Exception as e:
        bot.reply_to(message, f"មានបញ្ហា: {str(e)}")

# For Vercel
app = app
