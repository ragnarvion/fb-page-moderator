from flask import Flask, request, make_response
import requests
import re
import whois
from urllib.parse import urlparse

app = Flask(__name__)

# 🔑 FACEBOOK CREDENTIALS (Ang iyong Page Access Token at Verify Token mula sa Meta Dashboard)
FB_PAGE_ACCESS_TOKEN = "EAAdZAW7FpsyUBRkzDqrqbPLW0T2DbDlqIGaK6RPxeH1GCWiBY67up2IXYNdv6xRSsCgrbUeJGBZAl3D741L0WCQhupohfx4U2NFcUuJdeQFdZBs9UlVJK7tDCGXGZAmQprZCKOTfbpDMpMpGPkKXUbI5bZBlv0MjLTRZCzzdeq6nt06fqFZC3zBpaM9sEuJXOv61DiZAQX75euldZBLXe6hSGcKo5ZC"
FB_VERIFY_TOKEN = "minion_secret_token_123" 
APIVOID_API_KEY = "NFjihiWuEZBYDSe7o1PNx8LVsdRZ1VtViGZSiet85bw75.o1a2DwykJbR.z9bQwA"

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
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path.lower()
    fragment = parsed_url.fragment.lower()

    if any(banned in domain for banned in BANNED_DOMAINS):
        return True, "Kumpirmadong Scam/Ponzi Platform base sa Blocklist."

    if ("/h5" in path or "/ios" in path or "home" in fragment or "trade" in fragment):
        if not any(trusted in domain for trusted in TRUSTED_EXCHANGES):
            return True, "Kahina-hinalang Web-App Architecture (/h5/ios bypass)."

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        web_response = requests.get(url, headers=headers, timeout=5)
        web_content = web_response.text.lower()
        
        scam_score = 0
        for kw in PONZI_TERMINOLOGY:
            if kw in web_content: scam_score += 35
        for kw in LEGIT_INDICATORS:
            if kw in web_content: scam_score -= 25

        if scam_score >= 40:
            return True, f"Ponzi/Unregulated Crypto System (Score: {scam_score} pts)."
    except:
        pass
    return False, ""

# 🛠️ FACEBOOK GRAPH API FUNCTIONS
def send_fb_message(recipient_id, message_text):
    """Sumagot sa Messenger Chat"""
    url = f"https://facebook.com{FB_PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    requests.post(url, json=payload)

def delete_fb_object(object_id):
    """Burahin ang post o comment sa Page Wall"""
    url = f"https://facebook.com{object_id}?access_token={FB_PAGE_ACCESS_TOKEN}"
    response = requests.delete(url)
    if response.status_code == 200:
        print(f"🗑️ Matagumpay na binura ang scam object: {object_id}")

def reply_to_fb_comment(comment_id, message_text):
    """Mag-iwan ng babala sa ilalim ng comment"""
    url = f"https://facebook.com{comment_id}/comments?access_token={FB_PAGE_ACCESS_TOKEN}"
    payload = {"message": message_text}
    requests.post(url, json=payload)

# 🌐 CLOUD HANDSHAKE VERIFICATION (Para kay Meta Cloud)
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == FB_VERIFY_TOKEN:
        print("✅ WEBHOOK VERIFIED BY META CLOUD!")
        response = make_response(str(challenge))
        response.headers['ngrok-skip-browser-warning'] = 'true'
        return response, 200
    return "Forbidden", 403

# 📩 INTERCEPTOR: Tagasalo ng Chats, Posts, at Comments ng Page
@app.route('/webhook', methods=['POST'])
def receive_events():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data["entry"]:
            
            # 1. BANTAY SA MESSENGER (CHATS)
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
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
                                # Mag-iwan ng babala bago burahin ang comment
                                if item_type == "comment":
                                    reply_to_fb_comment(object_id, "🛑 Tinanggal ng Auto-Moderator: Bawal mag-post ng Ponzi/Scam investment links dito.")
                                delete_fb_object(object_id)
                                
    return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    app.run(port=5000)
