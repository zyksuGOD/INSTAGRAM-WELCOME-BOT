# Instagram Group Chat Bot

Bot for Instagram GC:
- Per-user welcome (6h cooldown per user)
- "ignore" keyword auto-reply
- GC link auto-reply
- Daily Good Morning (7AM), Good Night (12AM)
- Admin DM: /send_gc <text>

## Deploy on Render

1. Push repo to GitHub (private)
2. New Web Service -> connect repo
3. Region: Singapore
4. Env vars:
   - IG_THREAD_IDS = 1158412246605899,2961421587561271
   - IG_ADMINS = eren_ye4gerrr,unrexadox
   - IG_BOT_USERNAME = iy7qt
   - IG_SESSIONID = <sessionid value from cookies>
5. Deploy
6. UptimeRobot: HTTP monitor every 5 min on Render URL

## Session
Netscape cookies.txt supported, but env var IG_SESSIONID takes priority.
If expired, regenerate cookies and update env var -> redeploy.