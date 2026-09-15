import os

# ===== КОНФИГУРАЦИЯ БОТА =====

# Токен бота (из скриншота)
BOT_TOKEN = "ODgwNzQ4MjY4MjQxOTIx.qB9whByZORbD_6JxX2iVTWXPx_iToApT6e5Fse3QTLo"

# Application ID (из скриншота)
APPLICATION_ID = "d9a84b47-9f99-4bcf-b16c-fcd25500a782"

# Для Render (если запускаешь там)
if os.environ.get('BOT_TOKEN'):
    BOT_TOKEN = os.environ.get('BOT_TOKEN')

if os.environ.get('APPLICATION_ID'):
    APPLICATION_ID = os.environ.get('APPLICATION_ID')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'
COMMAND_PREFIX = "/"