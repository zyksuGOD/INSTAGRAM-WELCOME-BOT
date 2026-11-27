# Instagram Group Chat Bot

Features:
- Welcome message on user text (8-12s delay)
- 12-hour cooldown per user for welcome
- "ignore" keyword auto-reply with mention
- GC link auto-reply with mention
- 11:11 AM & PM daily message (random heart)
- Good Morning (7:00 AM) & Good Night (11:59 PM)
- Admin DM command: `/send_gc <text>`

## Deploy on Render
1. Push to GitHub
2. Create New Web Service -> Select Repo
3. Region: Singapore
4. Add Env Vars (IG_BOT_USERNAME, IG_ADMINS, IG_THREAD_IDS, IG_SESSIONID, PYTHON_VERSION)
5. Deploy
6. Set UptimeRobot HTTP monitor (5 mins)