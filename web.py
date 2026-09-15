from flask import Flask, jsonify
import threading
from database import Database

app = Flask(__name__)
db = Database()

@app.route('/')
def home():
    total_users = db.get_total_users()
    total_wanks = db.get_total_wanks()
    return f"""
    <html>
    <head>
        <title>Членометр</title>
        <style>
            body {{ 
                background: linear-gradient(135deg, #0f0f13 0%, #1a237e 100%);
                color: white; 
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .container {{ text-align: center; }}
            h1 {{ font-size: 3em; margin-bottom: 0.5em; }}
            .stats {{ font-size: 1.5em; color: #64b5f6; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Членометр работает!</h1>
            <div class="stats">
                <p>👥 Пользователей: {total_users}</p>
                <p> Всего дрочек: {total_wanks}</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/api/stats')
def api_stats():
    return jsonify({
        'total_users': db.get_total_users(),
        'total_wanks': db.get_total_wanks(),
        'top_users': [
            {'username': u['username'], 'size': u['dick_size'], 'wanks': u['wank_count']}
            for u in db.get_global_top(5)
        ]
    })

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web, daemon=True)
    t.start()

if __name__ == "__main__":
    keep_alive()
    import bot
    bot.client.run(bot.config.BOT_TOKEN)