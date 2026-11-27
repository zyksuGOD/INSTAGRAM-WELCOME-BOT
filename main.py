import os
import re
import time
import random
import threading
from datetime import datetime, timedelta
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, RateLimitError

# === CONFIG ===
BOT_USERNAME = os.environ.get("IG_BOT_USERNAME", "qwetuihf1")
ADMIN_USERNAMES = [a.strip() for a in os.environ.get("IG_ADMINS", "eren_ye4gerrr,unrexadox").split(",") if a.strip()]
GROUP_THREAD_IDS = [t.strip() for t in os.environ.get("IG_THREAD_IDS", "").split(",") if t.strip()]

IGNORE_WELCOME_USERNAMES = ["qwetuihf1", BOT_USERNAME] 

WELCOME_COOLDOWN_SEC = 12 * 3600  # 12 ghante
MESSAGE_CHECK_INTERVAL = 5 
ADMIN_POLL_INTERVAL = 15

# === GLOBALS ===
welcome_sent = {}
processed_message_ids = set()
gc_link_pattern = re.compile(
    r'(https?://)?(www\.)?(instagram\.com|instagr\.am|ig\.me)/(chat|direct|group|j)',
    re.IGNORECASE
)
cl = Client()

# === SESSION LOADER ===
def load_sessionid_from_netscape(path="cookies.txt"):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line: continue
            if line.startswith("#HttpOnly_"):
                line = line.replace("#HttpOnly_", "", 1)
            elif line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7 and parts[5] == "sessionid":
                return parts[6]
    return None

def get_sessionid():
    sid = os.environ.get("IG_SESSIONID")
    if sid and sid.strip(): return sid.strip()
    return load_sessionid_from_netscape("cookies.txt")

# === LOGIN ===
def login():
    sid = get_sessionid()
    if not sid:
        raise RuntimeError("No sessionid found")
    cl.login_by_sessionid(sid)
    print(f"[BOT] Logged in as {cl.username}")

# === HELPERS ===
def get_user_info(user_id):
    try: return cl.user_info(user_id)
    except Exception: return None

def send_msg(thread_id, text):
    time.sleep(random.randint(8, 12)) 
    try:
        cl.direct_send(text, thread_ids=[thread_id])
        return True
    except RateLimitError:
        print("[RATE LIMIT] sleeping 60s")
        time.sleep(60)
        return False
    except Exception as e:
        print(f"[SEND ERROR] {e}")
        return False

# === HANDLERS ===
def handle_welcome(thread_id, user_id, username):
    now = time.time()
    
    if user_id == cl.user_id: return
    if username in IGNORE_WELCOME_USERNAMES: return
    
    if now - welcome_sent.get(username, 0) < WELCOME_COOLDOWN_SEC:
        return
        
    mention = f"@{username}" if username else f"@{user_id}"
    text = f"🌸 WELCOME {mention} 🌸\n\nAao aao, hum toh tumhara hi wait kar rahe the! Batao kya haal chaal? 💖🫶"
    
    welcome_sent[username] = now 
    
    if send_msg(thread_id, text):
        print(f"[WELCOME] {username}")

def handle_ignore(thread_id, user_id):
    u = get_user_info(user_id)
    username = u.username if u else "baccha"
    emojis = ["🥹💋", "🥹💖", "🫂💋", "🥺💕", "💖🥹", "🥰💋", "🥺🫶"]
    chosen_emoji = random.choice(emojis)
    text = f"@{username} AWW BACCHA ISSOKIEE MEIN HU NA APKE LIYE {chosen_emoji}"
    if send_msg(thread_id, text): 
        print(f"[IGNORE] replied to {username}")

def handle_gc_link(thread_id, user_id):
    u = get_user_info(user_id)
    username = u.username if u else "user"
    emojis = ["😍💦👅", "😍😋💦", "🤤💦👅", "😍💦🔥", "🥵💦👅", "😍🔥💦"]
    chosen_emoji = random.choice(emojis)
    text = f"@{username} AWW TERE B44P KI BIWI KI PICS SHARE KAR RHA HAI KYA GC PE {chosen_emoji}"
    if send_msg(thread_id, text): 
        print(f"[GCLINK] replied to {username}")

def handle_hello_bot(thread_id, user_id):
    u = get_user_info(user_id)
    username = u.username if u else "user"
    text = f"@{username} hey wssp"
    if send_msg(thread_id, text):
        print(f"[HELLO BOT] replied to {username}")

def handle_1111(thread_id):
    hearts = ["💖", "❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍", "💗", "💓", "💞", "💕"]
    chosen_heart = random.choice(hearts)
    text = f"11:11 {chosen_heart}"
    if send_msg(thread_id, text):
        print("[11:11] Message sent")

# === MESSAGE POLLER ===
def poll_messages(start_time):
    global processed_message_ids
    print("[BOT] Message tracker started. Ignoring older messages.")

    while True:
        for thread_id in GROUP_THREAD_IDS:
            try:
                thread = cl.direct_thread(thread_id, amount=10)
            except LoginRequired:
                try: login()
                except Exception: pass
                continue
            except Exception:
                continue

            if not thread or not thread.messages: continue
            messages = list(reversed(thread.messages))

            for msg in messages:
                if msg.id in processed_message_ids:
                    continue
                
                processed_message_ids.add(msg.id)

                if msg.timestamp and msg.timestamp.timestamp() < start_time:
                    continue

                if msg.user_id == cl.user_id:
                    continue
                
                item_type = getattr(msg, "item_type", "") or ""
                if item_type == "action_log":
                    continue

                raw_text = getattr(msg, "text", "") or ""
                sender_id = msg.user_id
                
                try:
                    sender_info = get_user_info(sender_id)
                    username = sender_info.username if sender_info else None
                    
                    if raw_text:
                        if "hello bot" in raw_text.lower():
                            handle_hello_bot(thread_id, sender_id)
                        elif "ignore" in raw_text.lower():
                            handle_ignore(thread_id, sender_id)
                        elif gc_link_pattern.search(raw_text):
                            handle_gc_link(thread_id, sender_id)
                        else:
                            handle_welcome(thread_id, sender_id, username)
                    else:
                        # Agar text nahi hai (Sticker/Photo/Reel) toh welcome karega
                        handle_welcome(thread_id, sender_id, username)
                except Exception as e:
                    print(f"[HANDLER ERROR] {e}")
                
        if len(processed_message_ids) > 5000:
            processed_message_ids = set(list(processed_message_ids)[-2000:])
            
        time.sleep(MESSAGE_CHECK_INTERVAL)

# === ADMIN & DAILY ===
def poll_admin_dm():
    global processed_message_ids
    while True:
        try: 
            threads = cl.direct_threads(amount=5)
        except Exception: 
            time.sleep(ADMIN_POLL_INTERVAL)
            continue

        for thread in threads:
            if not thread.messages: continue
            last = thread.messages[0]
            
            if last.id in processed_message_ids:
                continue
            processed_message_ids.add(last.id)
            
            if last.user_id == cl.user_id: continue

            sender = get_user_info(last.user_id)
            if not sender or sender.username not in ADMIN_USERNAMES: continue

            raw_text = (last.text or "").strip()
            if raw_text.startswith("/send_gc "):
                content = raw_text[len("/send_gc "):].strip()
                if content:
                    for tid in GROUP_THREAD_IDS:
                        send_msg(tid, content)
                    send_msg(thread.id, "✅ Sent to GC")
                    print("[ADMIN] Sent to GC")
        time.sleep(ADMIN_POLL_INTERVAL)

def daily_scheduler():
    last_gm_date = None
    last_gn_date = None
    last_1111_am = None
    last_1111_pm = None
    
    while True:
        now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        today = now.date()
        
        if now.hour == 7 and now.minute == 0 and last_gm_date != today:
            for tid in GROUP_THREAD_IDS: 
                send_msg(tid, "GOOD MORNING EVERYONE ☀️💖")
            last_gm_date = today
            time.sleep(65) 
            
        if now.hour == 23 and now.minute == 59 and last_gn_date != today:
            for tid in GROUP_THREAD_IDS: 
                send_msg(tid, "GOOD NIGHT EVERYONE 🌙💤")
            last_gn_date = today
            time.sleep(65)
            
        if now.hour == 11 and now.minute == 11 and last_1111_am != today:
            for tid in GROUP_THREAD_IDS: 
                handle_1111(tid)
            last_1111_am = today
            time.sleep(65)
            
        if now.hour == 23 and now.minute == 11 and last_1111_pm != today:
            for tid in GROUP_THREAD_IDS: 
                handle_1111(tid)
            last_1111_pm = today
            time.sleep(65)
            
        time.sleep(20)

def start_keep_alive():
    try:
        from keep_alive import run_server
        threading.Thread(target=run_server, daemon=True).start()
    except Exception as e: 
        print(f"[KEEPALIVE ERROR] {e}")

if __name__ == "__main__":
    login()
    start_keep_alive()
    
    BOT_START_TIME = time.time()
    
    for tid in GROUP_THREAD_IDS:
        send_msg(tid, "BOT IS ACTIVE NOW")
    
    threading.Thread(target=poll_messages, args=(BOT_START_TIME,), daemon=True).start()
    threading.Thread(target=poll_admin_dm, daemon=True).start()
    threading.Thread(target=daily_scheduler, daemon=True).start()
    print("[BOT] Running safely...")
    while True: time.sleep(60)