import os
import re
from flask import Flask, request, make_response
import requests
from urllib.parse import urlparse

app = Flask(__name__)

# 🔑 VERIFY TOKEN (Tugma sa nilagay mo sa Facebook Webhook Setup)
FB_VERIFY_TOKEN = os.environ.get("FB_VERIFY_TOKEN", "05f9187b5e112b6523f11675bd76a811")
GRAPH_API_URL = "https://facebook.com"
URL_PATTERN = re.compile(r'(https?://[^\s]+)')

# 🛑 [ANTI-SCAM CONFIG] PONZI & CRYPTO RED FLAGS (+35 puntos)
PONZI_TERMINOLOGY = [
    "daily return", "weekly return", "monthly roi", "passive income", 
    "earn daily", "high yield", "return on investment", "capital based", 
    "deposit package", "trading bot profit", "double your money", "investment plan",
    "guaranteed profit", "guaranteed income", "passive return", "fixed roi",
    "crypto investment", "forex investment", "auto trading profit", "no risk trading",
    "deposit gcash", "pay via maya", "gcash payment", "maya deposit"
]
LEGIT_INDICATORS = [
    "sec registration", "sec permit", "regulatory license", "terms and conditions",
    "office address", "customer support", "high risk warning", "capital at risk"
]
TRUSTED_EXCHANGES = ["binance.com", "kucoin.com", "coinbase.com", "bybit.com", "okx.com", "coingecko.com"]
BANNED_DOMAINS = ["coppii.com", "hqi29.com", "dsj056.com", "hqi30.com", "wikipedia.org"]

# 🏢 [BUSINESS CONFIG] FAQ ANSWERS FOR CLUB OF ENTREPRENEURS
BUSINESS_TEMPLATES = {
    "GREETING": (
        "Magandang araw! Salamat sa pag-message sa Club of Entrepreneurs. 🚀\n\n"
        "Ako ang iyong Automated Assistant. Paano namin kayo matutulungan sa inyong tech project o system ngayon?\n\n"
        "I-type ang keyword ng inyong katanungan:\n"
        "👉 'PRESYO' - Magkano magpagawa ng website/system?\n"
        "👉 'PORTFOLIO' - Tingnan ang mga nagawa naming projects\n"
        "👉 'TIMELINE' - Gaano katagal bago matapos ang system?\n"
        "👉 'TAO' - Kausapin ang totoong Developer"
    ),
    "PRESYO": (
        "📊 ESTIMATED PRICING:\n\n"
        "🌐 Landing Page / Business Website: Nagsisimula sa ₱5,000 - ₱10,000\n"
        "🛒 E-Commerce / Online Store: ₱15,000 - ₱30,000\n"
        "💻 Customized Management System (Inventory, POS): Depende sa requirements (₱25,000+).\n\n"
        "Gusto mo ba ng libreng quotation? I-send lang ang mga detalye ng iyong kailangan dito!"
    ),
    "PORTFOLIO": "📂 AMING PROJECTS:\nTingnan ang aming mga demo at past works dito: https://yourportfolio.com",
    "TIMELINE": "⏳ TIMELINE:\n• Basic Websites: 5-7 araw.\n• Complex Systems: 3-6 na linggo.",
    "TAO": "Noted po! Inabisuhan ko na ang aming Lead Developer. Mag-antay lamang ng ilang sandali. 👨‍💻"
}

# 🛠️ MULTI-PAGE CONFIGURATION (EKSALTONG TUGMA SA SCREENSHOT MO)
CREATOR_PORTAL_PAGE_ID = "117234051433308"  # <-- Para kay Scambuster (Anti-Scam)
BUSINESS_PAGE_ID = "157057240819513"        # <-- Para kay Club of Entrepreneurs (Business)

PAGE_TOKENS = {
    CREATOR_PORTAL_PAGE_ID: os.environ.get("TOKEN_CREATOR_PORTAL"),
    BUSINESS_PAGE_ID: os.environ.get("TOKEN_BUSINESS_PAGE")
}

# 📊 THE SCAM DETECTOR ALGORITHM (Para kay Scambuster)
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
    except Exception as e:
        print(f"⚠️ Link Check Error: {e}")
    return False, ""

# 🛠️ FACEBOOK GRAPH API FUNCTIONS
def send_fb_message(recipient_id, message_text, token):
    if not token: return
    url = f"{GRAPH_API_URL}/me/messages?access_token={token}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    requests.post(url, json=payload)

def delete_fb_object(object_id, token):
    if not token: return
    url = f"{GRAPH_API_URL}/{object_id}?access_token={token}"
    requests.delete(url)

def reply_to_fb_comment(comment_id, message_text, token):
    if not token: return
    url = f"{GRAPH_API_URL}/{comment_id}/comments?access_token={token}"
    payload = {"message": message_text}
    requests.post(url, json=payload)

# 🌐 CLOUD HANDSHAKE VERIFICATION
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == FB_VERIFY_TOKEN:
        return make_response(str(challenge), 200)
    return "Forbidden", 403

# 📩 INTERCEPTOR: Tagasalo ng Webhook Events
@app.route('/webhook', methods=['POST'])
def receive_events():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            page_id = entry.get("id")
            page_token = PAGE_TOKENS.get(page_id)
            
            # 1. BANTAY SA MESSENGER (CHATS)
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    if sender_id == page_id: continue
                    msg_text = messaging_event["message"].get("text", "").strip()

                    # 🛡️ LOGIC PARA KAY SCAMBUSTER (ANTI-SCAM CHAT FILTER)
                    if page_id == CREATOR_PORTAL_PAGE_ID:
                        urls = URL_PATTERN.findall(msg_text)
                        for url in urls:
                            is_scam, reason = analyze_link(url)
                            if is_scam:
                                send_fb_message(sender_id, f"⚠️ BABALA NG SCAMBUSTER: Ang link mo ({url}) ay may indikasyon ng SCAM/PONZI.\nDahilan: {reason}", page_token)
                    
                    # 🏢 LOGIC PARA KAY CLUB OF ENTREPRENEURS (BUSINESS AUTO-RESPONDER)
                    elif page_id == BUSINESS_PAGE_ID:
                        cmd = msg_text.upper()
                        if any(w in cmd for w in ["HI", "HELLO", "INQUIRE", "HOW MUCH"]):
                            send_fb_message(sender_id, BUSINESS_TEMPLATES["GREETING"], page_token)
                        elif "PRESYO" in cmd or "PRICE" in cmd or "MAGKANO" in cmd:
                            send_fb_message(sender_id, BUSINESS_TEMPLATES["PRESYO"], page_token)
                        elif "PORTFOLIO" in cmd or "SAMPLE" in cmd:
                            send_fb_message(sender_id, BUSINESS_TEMPLATES["PORTFOLIO"], page_token)
                        elif "TIMELINE" in cmd or "TAGAL" in cmd:
                            send_fb_message(sender_id, BUSINESS_TEMPLATES["TIMELINE"], page_token)
                        elif "TAO" in cmd or "DEVELOPER" in cmd:
                            send_fb_message(sender_id, BUSINESS_TEMPLATES["TAO"], page_token)

            # 2. BANTAY SA PAGE WALL (FEED)
            for change in entry.get("changes", []):
                if change.get("field") == "feed":
                    value = change.get("value", {})
                    if value.get("verb") == "add" and value.get("message"):
                        msg_text = value.get("message", "")
                        item_type = value.get("item")
                        object_id = value.get("comment_id") if item_type == "comment" else value.get("post_id")
                        
                        # 🛡️ MODERATION: BURAHIN ANG SCAM KUNG SA SCAMBUSTER PAGE NAG-POST
                        if page_id == CREATOR_PORTAL_PAGE_ID:
                            urls = URL_PATTERN.findall(msg_text)
                            for url in urls:
                                is_scam, reason = analyze_link(url)
                                if is_scam:
                                    if item_type == "comment":
                                        reply_to_fb_comment(object_id, "🛑 Tinanggal ng Scambuster Auto-Moderator: Bawal ang Ponzi/Scam links dito.", page_token)
                                    delete_fb_object(object_id, page_token)
                        
                        # 🏢 INQUIRY AUTOMATION: AUTO-REPLY SA COMMENT KUNG SA CLUB OF ENTREPRENEURS
                        elif page_id == BUSINESS_PAGE_ID and item_type == "comment":
                            if any(k in msg_text.lower() for k in ["magkano", "how much", "pm", "avail"]):
                                reply_to_fb_comment(object_id, "Magandang araw! Nag-padala po kami ng estimated pricing sa inyong Messenger Inbox. Paki-check po ang aming message. Salamat! 🚀", page_token)

    return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
