"""
Web сервер + запуск бота для Render (Членометр)
ВАЖНО: Этот файл НЕ вызывает асинхронные функции БД напрямую!
"""

from flask import Flask, jsonify
import threading
import time
import os
import sys
import traceback

print("=" * 70)
print("🚀 ЧЛЕНОМЕТР - ЗАПУСК ПРИ ИМПОРТЕ...")
print("=" * 70)

app = Flask(__name__)

# Глобальный статус бота
bot_status = {
    'running': False,
    'started_at': None,
    'message': 'Initializing...'
}

@app.route('/')
def home():
    status_html = 'running' if bot_status['running'] else 'stopped'
    status_text = 'Онлайн ✅' if bot_status['running'] else 'Офлайн 🔴'
    
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
            <h1>✅ Членометр</h1>
            <div class="stats">
                <p>🌐 Веб-сервер активен</p>
                <p>🤖 Статус бота: {status_text}</p>
            </div>
            <div class="status {status_html}">
                {bot_status['message']}
            </div>
            <p style="margin-top: 30px; color: #b9bbbe;">
                Сайт: dickuplolka.gt.tc
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok' if bot_status['running'] else 'bot_not_running',
        'bot_running': bot_status['running'],
        'message': bot_status['message']
    })

@app.route('/api/status')
def api_status():
    return jsonify(bot_status)

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
        
        # Запускаем бота (это блокирующий вызов, поэтому он в потоке)
        bot_module.client.run(token)
        
    except Exception as e:
        bot_status['running'] = False
        bot_status['message'] = f'Error: {str(e)}'
        print("=" * 70)
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА БОТА: {e}")
        print("=" * 70)
        traceback.print_exc()
        
        # Пробуем перезапустить через 60 секунд
        print("⏳ Перезапуск бота через 60 секунд...")
        time.sleep(60)
        threading.Thread(target=run_bot, daemon=True).start()

def run_web():
    """Запускает Flask веб-сервер"""
    print("🌐 Запуск веб-сервера на http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)

# ===== ЗАПУСК ПРИ ИМПОРТЕ МОДУЛЯ (для Gunicorn) =====
print("📦 Инициализация системы...")

# 1. Запускаем веб-сервер в фоне
web_thread = threading.Thread(target=run_web, daemon=True)
web_thread.start()

# 2. Ждём 2 секунды чтобы веб-сервер успел стартовать
time.sleep(2)

# 3. Запускаем бота в фоне
print("🚀 Запуск бота в фоновом потоке...")
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

print("✅ Система запущена и работает в фоне!")
print("=" * 70)

# 4. Оставляем главный поток живым (Gunicorn требует этого)
def keep_alive():
    while True:
        time.sleep(3600)

# НЕ используем if __name__ == "__main__", так как Gunicorn импортирует этот файл!
keep_alive()
