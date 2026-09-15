"""
Web сервер + API + запуск бота для Render (Членометр)
С ДОБАВЛЕННЫМИ CORS ЗАГОЛОВКАМИ
"""

from flask import Flask, jsonify, make_response
import threading
import time
import os
import sys
import traceback
from datetime import datetime

print("=" * 70)
print(" ЧЛЕНОМЕТР - ЗАПУСК ПРИ ИМПОРТЕ...")
print("=" * 70)

app = Flask(__name__)

# Глобальный статус бота
bot_status = {
    'running': False,
    'started_at': None,
    'message': 'Initializing...',
    'users': 0,
    'servers': 0
}

# ===== CORS ЗАГОЛОВКИ =====
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ===== API ENDPOINTS ДЛЯ САЙТА =====

@app.route('/')
def home():
    status_html = 'running' if bot_status['running'] else 'stopped'
    status_text = 'Онлайн ✅' if bot_status['running'] else 'Офлайн 🔴'
    
    return f"""
    <html>
    <head>
        <title>Членометр API</title>
        <style>
            body {{ 
                background: linear-gradient(135deg, #0f0f13 0%, #1a237e 100%);
                color: white; 
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }}
            .container {{ 
                text-align: center; 
                max-width: 600px;
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }}
            h1 {{ font-size: 2.5em; margin-bottom: 0.5em; }}
            .stats {{ font-size: 1.3em; color: #64b5f6; margin: 20px 0; }}
            .status {{ 
                margin-top: 20px; 
                padding: 15px; 
                border-radius: 8px; 
                font-weight: bold;
            }}
            .running {{ background: #43b581; }}
            .stopped {{ background: #f04747; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Членометр API</h1>
            <div class="stats">
                <p>🌐 Веб-сервер активен</p>
                <p>🤖 Статус бота: {status_text}</p>
                <p>👥 Пользователей: {bot_status['users']}</p>
                <p>📡 Серверов: {bot_status['servers']}</p>
            </div>
            <div class="status {status_html}">
                {bot_status['message']}
            </div>
            <p style="margin-top: 30px; color: #b9bbbe;">
                API Endpoints:<br>
                <a href="/api/stats" style="color: #64b5f6;">/api/stats</a> - Статистика<br>
                <a href="/api/top" style="color: #64b5f6;">/api/top</a> - Топ 10<br>
                <a href="/health" style="color: #64b5f6;">/health</a> - Health check
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/api/stats')
def api_stats():
    """API для сайта - отдаёт статистику"""
    print(f"📊 /api/stats запрос - users: {bot_status['users']}, servers: {bot_status['servers']}")
    return jsonify({
        'success': True,
        'users': bot_status['users'],
        'servers': bot_status['servers'],
        'bot_running': bot_status['running'],
        'message': bot_status['message'],
        'timestamp': time.time()
    })

@app.route('/api/top')
def api_top():
    """API для сайта - отдаёт топ 10"""
    try:
        print("📊 /api/top запрос")
        # Импортируем базу данных
        from database import Database
        db = Database()
        
        # Топ по размеру
        top_size = db.get_global_top(10)
        print(f"  Top size: {len(top_size)} записей")
        
        # Топ по активности
        top_wanks = db.get_global_top_by_wanks(10)
        print(f"  Top wanks: {len(top_wanks)} записей")
        
        return jsonify({
            'success': True,
            'top_size': top_size,
            'top_wanks': top_wanks
        })
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'top_size': [],
            'top_wanks': []
        })

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok' if bot_status['running'] else 'bot_not_running',
        'bot_running': bot_status['running'],
        'users': bot_status['users'],
        'servers': bot_status['servers'],
        'message': bot_status['message'],
        'timestamp': time.time()
    })

# ===== ЗАПУСК БОТА =====

def update_bot_stats():
    """Периодически обновляет статистику бота"""
    global bot_status
    
    while True:
        try:
            if bot_status['running']:
                # Импортируем базу
                from database import Database
                db = Database()
                
                # Обновляем статистику
                bot_status['users'] = db.get_total_users()
                # Сервера считаем из client.guilds (но это асинхронно, поэтому пока заглушка)
                bot_status['servers'] = 1  # TODO: получить из бота
                
                print(f" Статистика обновлена: users={bot_status['users']}, servers={bot_status['servers']}")
                
        except Exception as e:
            print(f"⚠️ Ошибка обновления статистики: {e}")
        
        time.sleep(60)  # Обновляем каждую минуту

def run_bot():
    """Запускает бота в отдельном потоке"""
    global bot_status
    
    try:
        print("=" * 70)
        print("🤖 ЗАПУСК DISCORD БОТА (ЧЛЕНОМЕТР)...")
        print("=" * 70)
        
        bot_status['started_at'] = time.time()
        bot_status['message'] = 'Importing bot module...'
        
        # Импортируем бота
        import bot as bot_module
        print("✅ Модуль bot.py успешно импортирован")
        
        # Проверяем токен
        token = bot_module.config.BOT_TOKEN
        if not token:
            raise Exception("BOT_TOKEN пуст в config.py!")
        
        print(f"🔑 Токен найден (длина: {len(token)})")
        print("🔗 Подключение к Lolka Gateway...")
        
        bot_status['message'] = 'Connecting to Lolka...'
        bot_status['running'] = True
        
        # Запускаем бота
        bot_module.client.run(token)
        
    except Exception as e:
        bot_status['running'] = False
        bot_status['message'] = f'Error: {str(e)}'
        print("=" * 70)
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА БОТА: {e}")
        print("=" * 70)
        traceback.print_exc()
        
        # Перезапуск через 60 секунд
        print("⏳ Перезапуск бота через 60 секунд...")
        time.sleep(60)
        threading.Thread(target=run_bot, daemon=True).start()

def run_web():
    """Запускает Flask веб-сервер"""
    print("🌐 Запуск веб-сервера на http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)

# ===== ЗАПУСК ПРИ ИМПОРТЕ МОДУЛЯ =====
print("📦 Инициализация системы...")

# 1. Запускаем веб-сервер в фоне
web_thread = threading.Thread(target=run_web, daemon=True)
web_thread.start()

# 2. Запускаем обновление статистики
stats_thread = threading.Thread(target=update_bot_stats, daemon=True)
stats_thread.start()

# 3. Ждём 2 секунды
time.sleep(2)

# 4. Запускаем бота в фоне
print("🚀 Запуск бота в фоновом потоке...")
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

print("✅ Система запущена и работает в фоне!")
print("=" * 70)

# 5. Оставляем главный поток живым
def keep_alive():
    while True:
        time.sleep(3600)

keep_alive()
