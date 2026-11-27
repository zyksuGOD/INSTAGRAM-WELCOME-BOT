import os
import re
import time
import random
import threading
from datetime import datetime, timedelta
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, RateLimitError

# === CONFIG ===
BOT_USERNAME = os.environ.get("IG_BOT_USERNAME", "gc_bot_acc")
ADMIN_USERNAMES = [a.strip() for a in os.environ.get("IG_ADMINS", "eren_ye4gerrr,unrexadox").split(",") if a.strip()]
GROUP_THREAD_IDS = [t.strip() for t in os.environ.get("IG_THREAD_IDS", "").split(",") if t.strip()]

WELCOME_COOLDOWN_SEC = 6 * 3600
MESSAGE_CHECK_INTERVAL = 10 
ADMIN_POLL_INTERVAL = 15

# === GLOBALS ===
welcome_sent = {}
processed_message_ids = set()
gc_link_pattern = re.compile(
    r'(https?://)?(www\.)?(instagram\.com|instagr\.am)/(chat|direct|group|j)',
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

def human_delay():
    time.sleep(random.randint(6, 12))

def send_msg(thread_id, text, reply_to=None):
    try:
        if reply_to is not None:
            cl.direct_send(text, thread_ids=[thread_id], reply_to_message=reply_to)
        else:
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
    if now - welcome_sent.get(user_id, 0) < WELCOME_COOLDOWN_SEC:
        return
    human_delay()
    mention = f"@{username}" if username else f"@{user_id}"
    text = f"WELCOME TO OUR GC {mention} HOW ARE YOU 💖🥰"
    if send_msg(thread_id, text):
        welcome_sent[user_id] = now
        print(f"[WELCOME] {username}")

def handle_ignore(thread_id, user_id, msg_obj):
    human_delay()
    u = get_user_info(user_id)
    username = u.username if u else "baccha"
    
    # Random emoji variations taaki spam na lage
    emojis = ["🥹💋", "🥹💖", "🫂💋", "🥺💕", "💖🥹"]
    chosen_emoji = random.choice(emojis)
    
    text = f"@{username} AWW BACCHA ISSOKIEE MEIN HU NA APKE LIYE {chosen_emoji}"
    if send_msg(thread_id, text, reply_to=msg_obj): 
        print(f"[IGNORE] replied to {username}")

def handle_gc_link(thread_id, user_id, msg_obj):
    human_delay()
    u = get_user_info(user_id)
    username = u.username if u else "user"
    
    # Random emoji variations
    emojis = ["😍💦👅", "😍😋💦", "🤤💦👅", "😍💦🔥", "🥵💦👅"]
    chosen_emoji = random.choice(emojis)
    
    text = f"@{username} AWW TERE B44P KI BIWI KI PICS SHARE KAR RHA HAI KYA GC PE {chosen_emoji}"
    if send_msg(thread_id, text, reply_to=msg_obj): 
        print(f"[GCLINK] replied to {username}")

# === MESSAGE POLLER ===
def poll_messages():
    global processed_message_ids
    is_first_run = True

    while True:
        for thread_id in GROUP_THREAD_IDS:
            try:
                thread = cl.direct_thread(thread_id, amount=15)
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
                
                if is_first_run:
                    processed_message_ids.add(msg.id)
                    continue
                
                if msg.user_id == cl.user_id:
                    processed_message_ids.add(msg.id)
                    continue

                try:
                    item_type = getattr(msg, "item_type", "") or ""
                    raw_text = getattr(msg, "text", "") or ""
                    sender_id = msg.user_id

                    # 1. IGNORE CHECK
                    if raw_text and "ignore" in raw_text.lower():
                        handle_ignore(thread_id, sender_id, msg)
                        processed_message_ids.add(msg.id)
                    
                    # 2. GC LINK CHECK
                    elif raw_text and gc_link_pattern.search(raw_text):
                        handle_gc_link(thread_id, sender_id, msg)
                        processed_message_ids.add(msg.id)
                    
                    # 3. WELCOME CHECK (NEW MEMBER JOINED)
                    elif item_type == "action_log" and "joined" in raw_text.lower():
                        joined_uid = None
                        joined_uname = None
                        
                        m = re.search(r"@([A-Za-z0-9._]+)", raw_text)
                        if m:
                            joined_uname = m.group(1)
                            try: joined_uid = cl.user_id_from_username(joined_uname)
                            except: pass
                        
                        if not joined_uid:
                            mid_uid = getattr(msg, "user_id", None)
                            if mid_uid and mid_uid != cl.user_id:
                                joined_uid = mid_uid
                                u = get_user_info(mid_uid)
                                joined_uname = u.username if u else None
                        
                        if joined_uid:
                            handle_welcome(thread_id, joined_uid, joined_uname)
                        
                        processed_message_ids.add(msg.id)
                        
                except Exception as e:
                    print(f"[HANDLER ERROR] {e}")
                    processed_message_ids.add(msg.id)
                
        is_first_run = False
        if len(processed_message_ids) > 10000:
            processed_message_ids = set(list(processed_message_ids)[-5000:])
            
        time.sleep(MESSAGE_CHECK_INTERVAL)

# === ADMIN & DAILY ===
def poll_admin_dm():
    global processed_message_ids
    while True:
        try: 
            threads = cl.direct_threads(amount=1)
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
                    time.sleep(5)
        time.sleep(ADMIN_POLL_INTERVAL)

def daily_scheduler():
    last_gm_date = None
    last_gn_date = None
    while True:
        now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        today = now.date()
        
        if now.hour == 7 and now.minute == 0 and last_gm_date != today:
            for tid in GROUP_THREAD_IDS: 
                send_msg(tid, "GOOD MORNING EVERYONE ☀️💖")
            last_gm_date = today
            print("[DAILY] Good morning sent")
            time.sleep(65) 
            
        if now.hour == 0 and now.minute == 0 and last_gn_date != today:
            for tid in GROUP_THREAD_IDS: 
                send_msg(tid, "GOOD NIGHT EVERYONE 🌙💤")
            last_gn_date = today
            print("[DAILY] Good night sent")
            time.sleep(65)
            
        time.sleep(20)

def start_keep_alive():
    try:
        from keep_alive import run_server
        threading.Thread(target=run_server, daemon=True).start()
    except: pass

if __name__ == "__main__":
    login()
    start_keep_alive()
    threading.Thread(target=poll_messages, daemon=True).start()
    threading.Thread(target=poll_admin_dm, daemon=True).start()
    threading.Thread(target=daily_scheduler, daemon=True).start()
    print("[BOT] Running safely...")
    while True: time.sleep(60)