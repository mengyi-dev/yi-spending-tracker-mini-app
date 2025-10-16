from flask import Flask, request, jsonify
from telebot import TeleBot
from telebot.types import Update
import os
import json
import hmac
import hashlib
from urllib.parse import parse_qs

# Initialize Flask
app = Flask(__name__)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
VERCEL_URL = os.environ.get('VERCEL_URL', '')

# Initialize bot without validation
bot = None
if BOT_TOKEN:
    bot = TeleBot(BOT_TOKEN, threaded=False)
    
    # Register handlers only if bot is initialized
    @bot.message_handler(commands=['start'])
    def start(message):
        try:
            markup = json.dumps({
                "inline_keyboard": [[{
                    "text": "បើកកម្មវិធី 📱",
                    "web_app": {"url": "https://yi-spending-tracker-mini-app.vercel.app/"}
                }]]
            })
            
            bot.send_message(
                message.chat.id,
                "សូមស្វាគមន៍មកកាន់កម្មវិធីតាមដានចំណាយ! 🎉\n\n"
                "ចុចលើប៊ូតុងខាងក្រោមដើម្បីចាប់ផ្តើម:",
                reply_markup=markup
            )
        except Exception as e:
            print(f"Start command error: {str(e)}")

def validate_init_data(init_data):
    """Validate Telegram Mini App init data"""
    try:
        parsed_data = parse_qs(init_data)
        hash_value = parsed_data.get('hash', [''])[0]
        
        if not hash_value:
            return None
        
        # Remove hash from data
        data_check_arr = []
        for key, value in sorted(parsed_data.items()):
            if key != 'hash':
                data_check_arr.append(f"{key}={value[0]}")
        
        data_check_string = '\n'.join(data_check_arr)
        
        # Create secret key
        secret_key = hmac.new(
            b'WebAppData',
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verify hash
        if calculated_hash == hash_value:
            # Extract user data
            user_data = parsed_data.get('user', ['{}'])[0]
            return json.loads(user_data)
        
        return None
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return None

@app.route('/api/send-report', methods=['POST'])
def send_report():
    try:
        if not bot:
            return jsonify({'success': False, 'error': 'Bot not initialized'}), 500
        
        data = request.get_json()
        init_data = data.get('initData')
        report = data.get('report')
        
        if not init_data or not report:
            return jsonify({'success': False, 'error': 'Missing data'}), 400
        
        # Validate init data
        user = validate_init_data(init_data)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid init data'}), 403
        
        # Send report to user
        chat_id = user.get('id')
        bot.send_message(chat_id, report)
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Send report error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/', methods=['GET'])
@app.route('/api/index', methods=['GET'])
def index():
    try:
        if not bot:
            return jsonify({'status': 'error', 'message': 'BOT_TOKEN not set'}), 500
        
        return jsonify({
            'status': 'running',
            'webhook_url': f"https://{VERCEL_URL}/api/webhook",
            'bot_username': bot.get_me().username
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/webhook', methods=['POST'])
def webhook():
    try:
        if not bot:
            return 'Bot not initialized', 500
            
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = Update.de_json(json.loads(json_string))
            bot.process_new_updates([update])
            return 'OK', 200
        return 'Error: Invalid content type', 400
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return 'OK', 200
