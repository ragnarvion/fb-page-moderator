import os
import re
from flask import Flask, request, make_response
import requests
from urllib.parse import urlparse

app = Flask(__name__)

# 🔑 ENVIRONMENT VARIABLES (I-setup ito sa Render Dashboard, huwag i-hardcode!)
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "PALITAN_NG_DEFAULT_KUNG_TESTING")
FB_VERIFY_TOKEN = os.environ.get("FB_VERIFY_TOKEN", "minion_secret_token_123")

GRAPH_API_URL = "https://facebook.com"
URL_PATTERN = re.compile(r'(https?://[^\s]+)')

# 🛑 PONZI & CRYPTO SCAM RED FLAGS (+35 puntos bawat isa)
PONZI_TERMINOLOGY = [
    "daily return", "weekly return", "monthly roi", "passive income", 
    "earn daily", "high yield", "return on investment", "capital based", 
    "deposit package", "trading bot profit", "double your money", "investment plan",
    "guaranteed profit", "guaranteed income", "passive return", "fixed roi",
    "crypto investment", "forex investment", "auto trading profit", "no risk trading",
    "deposit gcash", "pay via maya", "gcash payment", "maya deposit"
]

# 🟢 LEGIT BUSINESS INDICATORS (-25 puntos bawat isa)
LEGIT_INDICATORS = [
    "sec registration", "sec permit", "regulatory license", "terms and conditions",
    "office address", "customer support", "high risk warning", "capital at risk"
]

TRUSTED_EXCHANGES = ["binance.com", "kucoin.com", "coinbase.com", "bybit.com", "okx.com", "coingecko.com"]
BANNED_DOMAINS = ["coppii.com", "hqi29.com", "dsj056.com"]

# 📊 THE SCAM DETECTOR ALGORITHM
def analyze_link(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        path = parsed_url.path.lower()
        fragment = parsed_url.fragment.lower()

        if any(banned in domain for banned in BANNED_DOMAINS):
            return True, "Kumpirmadong Scam/Ponzi Platform base sa Blocklist."

        if ("/h5" in path or "/ios" in path or "home" in fragment or "trade" in fragment):
            if not any(trusted in domain for trusted in TRUSTED_EXCHANGES):
                return True, "Kahina-hinalang Web-App Architecture (/h5/ios bypass)."

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        web_response = requests.get(url, headers=headers, timeout=5)
        web_content = web_response.text.lower()
        
        scam_score = 0
        for kw in PONZI_TERMINOLOGY:
            if kw in web_content: scam_score += 35
        for kw in LEGIT_INDICATORS:
            if kw in web_content: scam_score -= 25

        if scam_score >= 40:
            return True, f"Ponzi/Unregulated Crypto System (Score: {scam_score} pts)."
    except Exception as e:
        print(f"⚠️ Error sa pag-analyze ng link: {e}")
        
    return False, ""

# 🛠️ FACEBOOK GRAPH API FUNCTIONS (Inayos ang mga URL Endpoints)
def send_fb_message(recipient_id, message_text):
    """Sumagot sa Messenger Chat gamit ang Send API"""
    url = f"{GRAPH_API_URL}/me/messages?access_token={FB_PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    res = requests.post(url, json=payload)
    print(f"Messenger Reply Status: {res.status_code} - {res.text}")

def delete_fb_object(object_id):
    """Burahin ang post o comment sa Page Wall"""
    url = f"{GRAPH_API_URL}/{object_id}?access_token={FB_PAGE_ACCESS_TOKEN}"
    res = requests.delete(url)
    if res.status_code == 200:
        print(f"🗑️ Matagumpay na binura ang scam object: {object_id}")
    else:
        print(f"❌ Failed idelete ang object: {res.text}")

def reply_to_fb_comment(comment_id, message_text):
    """Mag-iwan ng babala sa ilalim ng comment bago ito burahin"""
    url = f"{GRAPH_API_URL}/{comment_id}/comments?access_token={FB_PAGE_ACCESS_TOKEN}"
    payload = {"message": message_text}
    res = requests.post(url, json=payload)
    print(f"Comment Reply Status: {res.status_code}")

# 🌐 CLOUD HANDSHAKE VERIFICATION
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == FB_VERIFY_TOKEN:
        print("✅ WEBHOOK VERIFIED BY META CLOUD!")
        return make_response(str(challenge), 200)
    return "Forbidden", 403

# 📩 INTERCEPTOR: Tagasalo ng Webhook Events
@app.route('/webhook', methods=['POST'])
def receive_events():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            
            # 1. BANTAY SA MESSENGER (CHATS)
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    # Iwasan ang infinite loop kapag ang bot mismo ang nagpadala ng mensahe
                    if sender_id == entry.get("id"):
                        continue
                        
                    msg_text = messaging_event["message"].get("text", "")
                    urls = URL_PATTERN.findall(msg_text)
                    for url in urls:
                        is_scam, reason = analyze_link(url)
                        if is_scam:
                            send_fb_message(sender_id, f"⚠️ BABALA: Ang link na isend mo ({url}) ay may indikasyon ng SCAM/PONZI.\nDahilan: {reason}")

            # 2. BANTAY SA PAGE WALL (POSTS & COMMENTS)
            for change in entry.get("changes", []):
                if change.get("field") == "feed":
                    value = change.get("value", {})
                    item_type = value.get("item")  # 'comment' o 'post'
                    verb = value.get("verb")  # 'add' o 'edited'
                    
                    if verb == "add" and value.get("message"):
                        msg_text = value.get("message", "")
                        object_id = value.get("comment_id") if item_type == "comment" else value.get("post_id")
                        
                        urls = URL_PATTERN.findall(msg_text)
                        for url in urls:
                            is_scam, reason = analyze_link(url)
                            if is_scam:
                                print(f"🚨 Nakakita ng scam sa page wall ({item_type})!")
                                if item_type == "comment":
                                    reply_to_fb_comment(object_id, "🛑 Tinanggal ng Auto-Moderator: Bawal mag-post ng Ponzi/Scam investment links dito.")
                                delete_fb_object(object_id)
                                
    return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    # Ang Render ay nangangailangan ng PORT environment variable para gumana
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
