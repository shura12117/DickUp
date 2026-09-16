"""
Членометр - Игровой бот для Lolka
СТАТИСТИКА И КУЛДАУНЫ ПРИВЯЗАНЫ СТРОГО К user_id (ГЛОБАЛЬНО ДЛЯ ВСЕХ СЕРВЕРОВ)
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.http import Route
import yarl
import aiohttp
import config
import logging
import os
import sys
import random
import asyncio
from datetime import datetime, timedelta
from database import Database

# ===== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ =====
db = Database()

# ===== ПРОВЕРКА КОНФИГУРАЦИИ =====
print("=" * 70)
print("🔍 ПРОВЕРКА КОНФИГУРАЦИИ:")
print(f"  BOT_TOKEN: {'✅ Найден' if config.BOT_TOKEN else '❌ НЕ НАЙДЕН'} (длина: {len(config.BOT_TOKEN) if config.BOT_TOKEN else 0})")
print(f"  APPLICATION_ID: {config.APPLICATION_ID}")
print("=" * 70)

if not config.BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден в config.py!")
    sys.exit(1)

print("✅ Все проверки пройдены! Запуск...")
print("=" * 70)

# ===== ПЕРЕНАПРАВЛЕНИЕ НА LOLKA API =====
Route.BASE = "https://lolka.app/api/bot/v10"
discord.gateway.DiscordWebSocket.DEFAULT_GATEWAY = yarl.URL("wss://lolka.app/ws/bot")

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(
    level=logging.INFO if config.DEBUG else logging.WARNING,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===== ИНТЕНТЫ =====
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

# ===== КЛИЕНТ =====
client = commands.Bot(
    command_prefix=commands.when_mentioned_or(config.COMMAND_PREFIX),
    intents=intents,
    help_command=None
)

session = None

# ===== КУЛДАУНЫ (в СЕКУНДАХ!) =====
COOLDOWN_WANK = 15 * 60  # 15 минут = 900 секунд
COOLDOWN_UP = 30 * 60    # 30 минут = 1800 секунд

# ===== СПИСОК СТАТУСОВ =====
STATUSES = [
    "Играет в Доту | Сайт: dickuplolka.gt.tc",
    "Играет в Раст | Сайт: dickuplolka.gt.tc",
    "Играет в КС | Сайт: dickuplolka.gt.tc",
    "Играет в Майнкрафт | Сайт: dickuplolka.gt.tc",
    "Играет в GTA V | Сайт: dickuplolka.gt.tc",
]

# ===== ЗАДАЧА СМЕНЫ СТАТУСА =====
@tasks.loop(minutes=2)
async def change_status():
    status = random.choice(STATUSES)
    await client.change_presence(activity=discord.Game(name=status))
    logger.info(f"🎮 Статус изменён: {status}")

@change_status.before_loop
async def before_change_status():
    await client.wait_until_ready()


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

async def process_wank(interaction: discord.Interaction):
    user = interaction.user
    user_id = str(user.id)
    
    try:
        logger.info(f"🔍 process_wank вызван для user_id={user_id}, name={user.name}, guild={interaction.guild.name if interaction.guild else 'DM'}")
        
        user_data = await db.get_user(user_id, user.name)
        
        if user_data:
            last_wank_str = user_data.get('last_wank')
            logger.info(f"📝 last_wank из БД: '{last_wank_str}'")
            
            if last_wank_str and str(last_wank_str).strip():
                try:
                    last_wank = datetime.fromisoformat(str(last_wank_str))
                    now = datetime.now()
                    time_diff = (now - last_wank).total_seconds()
                    remaining_seconds = COOLDOWN_WANK - time_diff
                    
                    logger.info(f"⏱️ Прошло: {time_diff:.0f} сек, кулдаун: {COOLDOWN_WANK} сек, осталось: {remaining_seconds:.0f} сек")
                    
                    if remaining_seconds > 0:
                        minutes = int(remaining_seconds // 60)
                        seconds = int(remaining_seconds % 60)
                        logger.info(f"⏸️ Кулдаун активен, выполнение отменено.")
                        return await interaction.followup.send(
                            f"⏱️ Кулдаун! Подожди ещё **{minutes} мин {seconds} сек**.", 
                            ephemeral=True
                        )
                except Exception as e:
                    logger.error(f"⚠️ Ошибка парсинга времени: {e}. Продолжаем без кулдауна.")
        
        logger.info(f"➕ Выполняем add_wank для {user_id}")
        count = await db.add_wank(user_id, user.name)
        logger.info(f"✅ add_wank вернул count={count}")
        
        await db.update_username(user_id, user.name)
        
        if interaction.guild:
            user_data = await db.get_user(user_id, user.name)
            await db.update_server_stats(
                str(interaction.guild.id),
                user_id,
                user_data.get('dick_size', 0) if user_data else 0,
                count
            )
        
        await interaction.followup.send(
            f"**{user.name}**, подро🍆ил 😈\n"
            f"Дро🍆ек всего (глобально) - **{count}**"
        )
        
    except Exception as e:
        logger.error(f"❌ Error in /дроч: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)


async def process_up(interaction: discord.Interaction):
    user = interaction.user
    user_id = str(user.id)
    
    try:
        logger.info(f"🔍 process_up вызван для user_id={user_id}, name={user.name}")
        user_data = await db.get_user(user_id, user.name)
        
        if user_data:
            last_up_str = user_data.get('last_up')
            logger.info(f"📝 last_up из БД: '{last_up_str}'")
            
            if last_up_str and str(last_up_str).strip():
                try:
                    last_up = datetime.fromisoformat(str(last_up_str))
                    now = datetime.now()
                    time_diff = (now - last_up).total_seconds()
                    remaining_seconds = COOLDOWN_UP - time_diff
                    
                    if remaining_seconds > 0:
                        minutes = int(remaining_seconds // 60)
                        seconds = int(remaining_seconds % 60)
                        logger.info(f"⏸️ Кулдаун /ап активен, осталось: {remaining_seconds:.0f} сек")
                        return await interaction.followup.send(
                            f"⏱️ Кулдаун! Подожди ещё **{minutes} мин {seconds} сек**.", 
                            ephemeral=True
                        )
                except Exception as e:
                    logger.error(f"⚠️ Ошибка парсинга времени: {e}. Продолжаем без кулдауна.")
        
        growth = random.randint(1, 10)
        logger.info(f"➕ Выполняем add_size для {user_id}, growth={growth}")
        new_size = await db.add_size(user_id, growth, user.name)
        logger.info(f"✅ add_size вернул new_size={new_size}")
        
        await db.update_username(user_id, user.name)
        
        if interaction.guild:
            await db.update_server_stats(
                str(interaction.guild.id),
                user_id,
                new_size,
                user_data.get('wank_count', 0) if user_data else 0
            )
        
        await interaction.followup.send(
            f"**{user.name}**, вы успешно вырастили свою арматуру на **{growth} см**! 📏\n"
            f"Ваша арматура (глобально): **{new_size:.1f} см**"
        )
    except Exception as e:
        logger.error(f"❌ Error in /ап: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)


# ==================== СОБЫТИЯ ====================

@client.event
async def on_ready():
    global session
    session = aiohttp.ClientSession()
    
    await client.change_presence(
        activity=discord.Game(name="Играет в Доту | Сайт: dickuplolka.gt.tc")
    )
    
    if not change_status.is_running():
        change_status.start()
    
    logger.info("=" * 70)
    logger.info(f"✅ Бот подключён: {client.user}")
    logger.info(f"📊 Серверов: {len(client.guilds)}")
    
    total_users = await db.get_total_users()
    logger.info(f"👥 Пользователей в БД: {total_users}")
    
    logger.info(f"⏱️ Кулдаун /дроч: {COOLDOWN_WANK // 60} мин ({COOLDOWN_WANK} сек)")
    logger.info(f"⏱️ Кулдаун /ап: {COOLDOWN_UP // 60} мин ({COOLDOWN_UP} сек)")
    logger.info("💾 Статистика и кулдауны привязаны к ID пользователя")
    logger.info("🔄 Авто-смена статуса каждые 2 минуты запущена")
    logger.info("=" * 70)
    
    try:
        logger.info("🔄 Синхронизация команд...")
        synced = await client.tree.sync()
        logger.info(f"✅ Синхронизировано команд: {len(synced)}")
        for cmd in synced:
            logger.info(f"   - /{cmd.name}")
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации: {e}")


# ==================== КОМАНДЫ ====================

@client.tree.command(name="дроч", description="Увеличить счётчик дрочек")
async def wank_command(interaction: discord.Interaction):
    await interaction.response.defer()
    await process_wank(interaction)


@client.tree.command(name="дрочить", description="Увеличить счётчик дрочек")
async def wank2_command(interaction: discord.Interaction):
    await interaction.response.defer()
    await process_wank(interaction)


@client.tree.command(name="подрочить", description="Увеличить счётчик дрочек")
async def wank3_command(interaction: discord.Interaction):
    await interaction.response.defer()
    await process_wank(interaction)


@client.tree.command(name="ап", description="Вырастить арматуру на 1-10 см")
async def up_command(interaction: discord.Interaction):
    await interaction.response.defer()
    await process_up(interaction)


@client.tree.command(name="топ", description="Топ 10 пользователей сервера")
async def top_command(interaction: discord.Interaction):
    await interaction.response.defer()
    
    server = interaction.guild
    if not server:
        return await interaction.followup.send("❌ Команда работает только на сервере", ephemeral=True)
    
    try:
        logger.info(f"📊 Запрос топа для сервера {server.name} ({server.id})")
        top = await db.get_server_top(str(server.id), 10)
        logger.info(f"📊 Получено результатов: {len(top) if top else 0}")
        
        if not top:
            return await interaction.followup.send("📊 Пока никто не активничал на этом сервере", ephemeral=True)
        
        embed = discord.Embed(
            title=f"🏆 Топ 10 сервера {server.name}",
            color=discord.Color.blue()
        )
        
        for i, user in enumerate(top, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            embed.add_field(
                name=f"{medal} {user['username']}",
                value=f"📏 Арматура: **{user['dick_size']:.1f} см**\n💦 Дрочек: **{user['wank_count']}**",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"❌ Error in /топ: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)


@client.tree.command(name="глобальный_топ", description="Глобальный топ 10")
async def global_top_command(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        logger.info("📊 Запрос глобального топа")
        top = await db.get_global_top(10)
        logger.info(f"📊 Получено результатов: {len(top) if top else 0}")
        
        if not top:
            return await interaction.followup.send("📊 База данных пуста", ephemeral=True)
        
        embed = discord.Embed(
            title="🌍 Глобальный топ 10",
            description="Статистика общая для всех серверов",
            color=discord.Color.purple()
        )
        
        for i, user in enumerate(top, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            embed.add_field(
                name=f"{medal} {user['username']}",
                value=f"📏 Арматура: **{user['dick_size']:.1f} см**\n💦 Дрочек: **{user['wank_count']}**",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"❌ Error in /глобальный_топ: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)


@client.tree.command(name="стата", description="Твоя статистика")
async def stats_command(interaction: discord.Interaction):
    await interaction.response.defer()
    
    user = interaction.user
    
    try:
        user_data = await db.get_user(str(user.id), user.name)
        
        if not user_data:
            return await interaction.followup.send("❌ Ты ещё не в системе", ephemeral=True)
        
        total_users = await db.get_total_users()
        
        embed = discord.Embed(
            title=f"📊 Статистика {user.name}",
            description="*(Статистика сохраняется глобально по ID)*",
            color=discord.Color.blue()
        )
        embed.add_field(name="📏 Арматура", value=f"**{user_data['dick_size']:.1f} см**", inline=True)
        embed.add_field(name="💦 Дрочек", value=f"**{user_data['wank_count']}**", inline=True)
        embed.add_field(name="👥 Всего игроков", value=f"**{total_users}**", inline=True)
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"❌ Error in /стата: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)


@client.tree.command(name="help", description="Справка")
async def help_command(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        embed = discord.Embed(
            title="📖 Членометр - Справка",
            description=(
                "**Команды:**\n\n"
                f"**/дроч** (или /дрочить, /подрочить) - +1 к счёту (кулдаун **{COOLDOWN_WANK // 60} мин**)\n"
                f"**/ап** - вырастить арматуру на 1-10 см (кулдаун **{COOLDOWN_UP // 60} мин**)\n"
                "**/топ** - топ 10 пользователей этого сервера\n"
                "**/глобальный_топ** - глобальный топ 10 по всем серверам\n"
                "**/стата** - твоя личная статистика\n"
                "**/help** - эта справка\n\n"
                "💡 *Твоя статистика и кулдауны привязаны к твоему ID и одинаковы на всех серверах!*"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Членометр | Сайт: dickuplolka.gt.tc")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"❌ Error in /help: {e}", exc_info=True)
        await interaction.followup.send("❌ Произошла ошибка.", ephemeral=True)


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    try:
        logger.info("🚀 Запуск бота...")
        client.run(config.BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("❌ Неверный токен! Проверьте BOT_TOKEN в config.py")
    except discord.PrivilegedIntentsRequired:
        logger.error("❌ Ошибка привилегированных интентов!")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if session:
            session.close()
