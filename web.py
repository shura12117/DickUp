"""
Web сервер + API + запуск бота для Render (Членометр)
ИСПРАВЛЕНО: Правильное получение статистики
"""

from flask import Flask, jsonify
from flask_cors import CORS
import threading
import time
import os
import sys
import traceback
from datetime import datetime

print("=" * 70)
print("🚀 ЧЛЕНОМЕТР - ЗАПУСК ПРИ ИМПОРТЕ...")
print("=" * 70)

app = Flask(__name__)
CORS(app)

# Глобальный статус бота
bot_status = {
    'running': False,
    'started_at': None,
    'message': 'Initializing...',
    'users': 0,
    'servers': 0,
    'last_update': None
}

# ===== API ENDPOINTS =====

@app.route('/')
def home():
    try:
        status_html = 'running' if bot_status.get('running') else 'stopped'
        status_text = 'Онлайн ✅' if bot_status.get('running') else 'Подключение...'
        
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
                a {{ color: #64b5f6; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✅ Членометр API</h1>
                <div class="stats">
                    <p>🌐 Веб-сервер активен</p>
                    <p> Статус бота: {status_text}</p>
                    <p>👥 Пользователей: {bot_status.get('users', 0)}</p>
                    <p>📡 Серверов: {bot_status.get('servers', 1)}</p>
                    <p>🕒 Последнее обновление: {bot_status.get('last_update', 'Never')}</p>
                </div>
                <div class="status {status_html}">
                    {bot_status.get('message', 'Unknown')}
                </div>
                <p style="margin-top: 30px; color: #b9bbbe;">
                    API Endpoints:<br>
                    <a href="/api/stats">/api/stats</a> - Статистика<br>
                    <a href="/api/top">/api/top</a> - Топ 10<br>
                    <a href="/health">/health</a> - Health check
                </p>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>", 500

@app.route('/api/stats')
def api_stats():
    """API для сайта - отдаёт статистику"""
    try:
        print(f"[{datetime.now()}] 📊 /api/stats запрос")
        print(f"  Текущие данные: users={bot_status.get('users')}, servers={bot_status.get('servers')}")
        
        # Пытаемся получить актуальные данные из БД
        try:
            from database import Database
            db = Database()
            
            # Получаем актуальное количество пользователей
            total_users = db.get_total_users()
            bot_status['users'] = total_users
            
            print(f"   Из БД: total_users={total_users}")
            
        except Exception as db_error:
            print(f"  ⚠️ Ошибка чтения БД: {db_error}")
        
        return jsonify({
            'success': True,
            'users': int(bot_status.get('users', 0)),
            'servers': int(bot_status.get('servers', 1)),
            'bot_running': bool(bot_status.get('running', False)),
            'message': str(bot_status.get('message', '')),
            'last_update': str(bot_status.get('last_update', '')),
            'timestamp': time.time()
        })
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Ошибка в /api/stats: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'users': 0,
            'servers': 0
        }), 500

@app.route('/api/top')
def api_top():
    """API для сайта - отдаёт топ 10"""
    try:
        print(f"[{datetime.now()}] 📊 /api/top запрос")
        
        # Пытаемся получить данные из БД
        try:
            from database import Database
            db = Database()
            
            # Топ по размеру
            top_size = db.get_global_top(10)
            print(f"   Top size: {len(top_size) if top_size else 0} записей")
            
            # Топ по активности
            top_wanks = db.get_global_top_by_wanks(10)
            print(f"  📊 Top wanks: {len(top_wanks) if top_wanks else 0} записей")
            
            if top_size:
                print(f"   Первый в топе: {top_size[0]}")
            
        except Exception as db_error:
            print(f"  ⚠️ Ошибка БД: {db_error}")
            traceback.print_exc()
            top_size = []
            top_wanks = []
        
        return jsonify({
            'success': True,
            'top_size': top_size if top_size else [],
            'top_wanks': top_wanks if top_wanks else []
        })
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Ошибка в /api/top: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'top_size': [],
            'top_wanks': []
        }), 500

@app.route('/health')
def health():
    try:
        return jsonify({
            'status': 'ok' if bot_status.get('running') else 'bot_not_running',
            'bot_running': bool(bot_status.get('running', False)),
            'users': int(bot_status.get('users', 0)),
            'servers': int(bot_status.get('servers', 1)),
            'message': str(bot_status.get('message', '')),
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ===== ФОНОВЫЕ ЗАДАЧИ =====

def update_bot_stats():
    """Периодически обновляет статистику бота"""
    global bot_status
    
    print("🔄 Запущена фоновая задача обновления статистики...")
    
    while True:
        try:
            print(f"[{datetime.now()}] 🔄 Обновление статистики...")
            
            # Импортируем базу
            try:
                from database import Database
                db = Database()
                
                # Обновляем статистику
                total_users = db.get_total_users()
                bot_status['users'] = total_users
                bot_status['servers'] = 2  # Пока хардкод (бот на 2 серверах)
                bot_status['last_update'] = datetime.now().strftime('%H:%M:%S')
                
                print(f"  ✅ Статистика: users={total_users}, servers=2")
                
            except Exception as db_error:
                print(f"  ⚠️ Ошибка БД: {db_error}")
                traceback.print_exc()
                
        except Exception as e:
            print(f"️ Ошибка в update_bot_stats: {e}")
        
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
    try:
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    except Exception as e:
        print(f"❌ Ошибка запуска веб-сервера: {e}")
        traceback.print_exc()

# ===== ЗАПУСК ПРИ ИМПОРТЕ МОДУЛЯ =====
print(" Инициализация системы...")

try:
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
    
except Exception as e:
    print(f"❌ Ошибка инициализации: {e}")
    traceback.print_exc()

# 5. Оставляем главный поток живым
def keep_alive():
    while True:
        time.sleep(3600)

keep_alive()
