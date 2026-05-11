from flask import Flask, request, jsonify
import asyncio
import aiohttp
import base64
import binascii
import json
import requests
import telebot
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.json_format import MessageToJson
import like_pb2
import like_count_pb2
import uid_generator_pb2
from google.protobuf.message import DecodeError
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter('ignore', InsecureRequestWarning)
app = Flask(__name__)

# ================= CONFIGURATION =================
# Yahan apna Telegram Bot Token daalo
BOT_TOKEN = "8724853412:AAHgRcU1xlEVUNG-SNKVHcmQvj7goDWRIXk" 
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# Crypto Keys (Same as your file)
KEY = b'Yg&tc%DEuh6%Zc^8'
IV = b'6oyZDr22E3ychjM%'
# =================================================

def load_tokens(server_name):
    try:
        files = {"IND": "token_ind.json", "BR": "token_br.json", "US": "token_br.json"}
        target = files.get(server_name, "token_bd.json")
        with open(target, "r") as f:
            return json.load(f)
    except: return None

def encrypt_message(plaintext):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return binascii.hexlify(cipher.encrypt(pad(plaintext, AES.block_size))).decode('utf-8')

# --- BOT COMMAND HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👑 *Throne Giant Bot Ready* \n\nCommand: `/like <uid> <server>`\nExample: `/like 12345678 BD`", parse_mode="Markdown")

@bot.message_handler(commands=['like'])
def handle_like(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ UID missing! Example: `/like 12345678 BD`")
            return
        
        uid = args[1]
        server = args[2].upper() if len(args) > 2 else "BD"
        
        # Bot Status Update
        status_msg = bot.reply_to(message, f"🚀 *Throne Giant Processing {uid}...*\nPattern: 1000 Likes Batch\nWait 30-40 seconds.", parse_mode="Markdown")

        # Select Server URL
        url_map = {
            "IND": "https://client.ind.freefiremobile.com/LikeProfile",
            "BR": "https://client.us.freefiremobile.com/LikeProfile",
            "US": "https://client.us.freefiremobile.com/LikeProfile"
        }
        target_url = url_map.get(server, "https://clientbp.ggpolarbear.com/LikeProfile")

        # 1000 Likes Logic Run
        asyncio.run(send_1000_likes_batch(uid, server, target_url))

        bot.edit_message_text(f"✅ *Success!* \nUID: {uid} \nServer: {server} \nStatus: 1000 Likes Sent Successfully!", 
                             chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
                             
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# --- 1000 LIKES PRO BATCH LOGIC ---
async def send_request(session, encrypted_uid, token, url):
    headers = {
        'User-Agent': "Dalvik/2.1.0",
        'Authorization': f"Bearer {token}",
        'Content-Type': "application/x-www-form-urlencoded"
    }
    try:
        async with session.post(url, data=bytes.fromhex(encrypted_uid), headers=headers, timeout=5) as r:
            return r.status
    except: return None

async def send_1000_likes_batch(uid, server_name, url):
    # Protobuf & Encryption
    message = like_pb2.like()
    message.uid, message.region = int(uid), server_name
    encrypted_uid = encrypt_message(message.SerializeToString())
    
    tokens = load_tokens(server_name)
    if not tokens: return
    
    # Batching Pattern: [200, 300, 300, 200] = 1000 Likes
    batches = [200, 300, 300, 200]
    idx = 0
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        for i, count in enumerate(batches):
            tasks = []
            for _ in range(count):
                if idx < len(tokens):
                    token = tokens[idx % len(tokens)]["token"]
                    tasks.append(send_request(session, encrypted_uid, token, url))
                    idx += 1
            
            await asyncio.gather(*tasks)
            # Short break between batches to avoid server-side blocking
            if i < len(batches) - 1:
                await asyncio.sleep(2.5)

# --- VERCEL WEBHOOK ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Forbidden', 403

@app.route('/')
def home():
    return "Throne Giant Bot is Active"

if __name__ == '__main__':
    app.run()
