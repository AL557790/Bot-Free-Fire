
import os
import logging
import requests
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================================================
# FLASK KEEP-ALIVE SERVER (FOR RENDER FREE TIER)
# =========================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# =========================================================
# CONFIG
# =========================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8482418509:AAH4p698srFZi1JwoX2_oHtUTjiPP7C0ywg")

API_URL = "https://freefireapis.lat/info-player"

REGIONS = [
    "BR", "SAC", "US", "NA",
    "IND", "BD", "ID", "ME",
    "VN", "TH", "CIS", "RU",
    "PK", "SG", "EU", "TW"
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# =========================================================
# HELPERS
# =========================================================

def get_player(uid: str, region: str):
    try:
        response = requests.get(
            API_URL,
            params={
                "uid": uid,
                "region": region
            },
            timeout=20
        )

        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            return None, "API returned an unsuccessful response."

        return data.get("result"), None

    except requests.exceptions.Timeout:
        return None, "The Free Fire API took too long to respond."

    except requests.exceptions.RequestException as e:
        logger.error("API error: %s", e)
        return None, "Could not connect to the Free Fire API."

    except ValueError:
        return None, "The API returned invalid JSON."


def safe(value, default="Unknown"):
    if value is None or value == "":
        return default
    return str(value)


def format_player(result):
    basic = result.get("basicInfo", {})
    clan = result.get("clanBasicInfo", {})
    pet = result.get("petInfo", {})
    credit = result.get("creditScoreInfo", {})
    spark = result.get("userSparkInfo", {})

    nickname = safe(basic.get("nickname"))
    uid = safe(basic.get("accountId"))
    region = safe(basic.get("region"))
    level = safe(basic.get("level"))
    exp = safe(basic.get("exp"))

    rank = safe(basic.get("rank"))
    ranking_points = safe(basic.get("rankingPoints"))

    cs_rank = safe(basic.get("csRank"))
    cs_points = safe(basic.get("csRankingPoints"))

    max_rank = safe(basic.get("maxRank"))
    cs_max_rank = safe(basic.get("csMaxRank"))

    likes = safe(basic.get("liked"))
    prime = safe(basic.get("primeLevel"))
    badges = safe(basic.get("badgeCnt"))

    created = safe(basic.get("createAt"))
    last_login = safe(basic.get("lastLoginAt"))
    version = safe(basic.get("releaseVersion"))

    clan_name = safe(clan.get("clanName"))
    clan_level = safe(clan.get("clanLevel"))
    clan_members = safe(clan.get("memberNum"))
    clan_capacity = safe(clan.get("capacity"))

    pet_id = safe(pet.get("id"))

    credit_score = safe(credit.get("creditScore"))
    spark_level = safe(spark.get("level"))

    message = f"""🎮 FREE FIRE PLAYER

👤 Nickname: {nickname}
🆔 UID: {uid}
🌍 Region: {region}

━━━━━━━━━━━━━━━━━━

⭐️ Level: {level}
✨ EXP: {exp}
👑 Prime Level: {prime}
❤️ Likes: {likes}
🏅 Badges: {badges}

🏆 BR Rank: {rank}
📊 BR Points: {ranking_points}
🔥 Max BR Rank: {max_rank}

⚔️ CS Rank: {cs_rank}
📊 CS Points: {cs_points}
🔥 Max CS Rank: {cs_max_rank}

━━━━━━━━━━━━━━━━━━

🏰 CLAN

🏷 Name: {clan_name}
⭐️ Level: {clan_level}
👥 Members: {clan_members}/{clan_capacity}

━━━━━━━━━━━━━━━━━━

🐾 PET

🆔 ID: {pet_id}

━━━━━━━━━━━━━━━━━━

🛡 CREDIT SCORE

💯 Score: {credit_score}

⚡️ Spark Level: {spark_level}

━━━━━━━━━━━━━━━━━━

📱 Version: {version}
📅 Created: {created}
🕐 Last Login: {last_login}"""

    return message


def get_clothes(result):
    inventory = result.get("inventory", {})
    return inventory.get("clothes", [])


def get_weapon_skins(result):
    inventory = result.get("inventory", {})
    return inventory.get("weaponSkinShows", [])


# =========================================================
# START & HELP
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔎 Player Info", callback_data="help_info")],
        [InlineKeyboardButton("🌍 Regions", callback_data="regions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = """🎮 FREE FIRE API BOT

Welcome!

Use:
/info UID REGION

Example:
/info 228159683 BR

The bot will retrieve public player information and send player images when available."""

    await update.message.reply_text(text, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""📖 COMMANDS

/info UID REGION

Example:
/info 228159683 BR

━━━━━━━━━━━━━━━━━━

Available regions:
{', '.join(REGIONS)}"""

    await update.message.reply_text(text)


# =========================================================
# INFO COMMAND
# =========================================================

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Incorrect format.\n\nUse:\n/info UID REGION\n\nExample:\n/info 228159683 BR"
        )
        return

    uid = context.args[0].strip()
    region = context.args[1].strip().upper()

    if not uid.isdigit():
        await update.message.reply_text("❌ UID must contain numbers only.")
        return

    if region not in REGIONS:
        await update.message.reply_text(
            f"❌ Invalid region.\n\nSupported regions:\n{', '.join(REGIONS)}"
        )
        return

    status_message = await update.message.reply_text("🔎 Searching for player...\n\nPlease wait.")

    result, error = get_player(uid, region)

    if error:
        await status_message.edit_text(f"❌ Error\n\n{error}")
        return

    if not result:
        await status_message.edit_text("❌ Player information was not found.")
        return

    text = format_player(result)

    try:
        await status_message.delete()
    except Exception:
        pass

    clothes_url = result.get("clothesUrl", {}).get("png")

    if clothes_url:
        try:
            await update.message.reply_photo(photo=clothes_url, caption=text)
        except Exception as e:
            logger.error("Failed to send clothes image: %s", e)
            await update.message.reply_text(text)
    else:
        await update.message.reply_text(text)

    clothes = get_clothes(result)
    if clothes:
        clothes_text = "👕 CLOTHES\n\n"
        for item in clothes[:20]:
            title = safe(item.get("title"), "Unknown")
            rarity = safe(item.get("rarity"), "Unknown")
            item_type = safe(item.get("type"), "Unknown")
            clothes_text += f"• {title}\n  Type: {item_type}\n  Rarity: {rarity}\n\n"

        await update.message.reply_text(clothes_text)

    weapon_skins = get_weapon_skins(result)
    if weapon_skins:
        weapon_text = "🔫 WEAPON SKINS\n\n"
        for item in weapon_skins[:20]:
            title = safe(item.get("title"), "Unknown")
            rarity = safe(item.get("rarity"), "Unknown")
            weapon_text += f"• {title}\n  Rarity: {rarity}\n\n"

        await update.message.reply_text(weapon_text)


# =========================================================
# CALLBACK BUTTONS & ERRORS
# =========================================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "help_info":
        await query.message.reply_text("🔎 PLAYER INFO\n\nUse:\n/info UID REGION\n\nExample:\n/info 228159683 BR")
    elif query.data == "regions":
        await query.message.reply_text(f"🌍 SUPPORTED REGIONS\n\n{', '.join(REGIONS)}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Telegram error: %s", context.error)


# =========================================================
# MAIN
# =========================================================

def main():
    # تشغيل سيرفر Flask في الخلفية لتلبية متطلبات Render Web Service
    Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_error_handler(error_handler)

    print("================================")
    print(" FREE FIRE TELEGRAM BOT IS RUNNING")
    print("================================")

    application.run_polling()


if __name__ == "__main__":
    main()
