"""
Chișinău Public Transport Ticket Bot
=====================================
Generează o imagine identică cu SMS-ul de la 7000.

Requirements:
    pip install python-telegram-bot Pillow

Font:
    Pune SF-Pro-Text-Regular.otf și SF-Pro-Text-Bold.otf
    în același folder cu acest script.
"""

import logging
import random
import io
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler,
)

BOT_TOKEN = "8784157927:AAHkvueeHu6fr1JzVToFV-mNxevGbWxcc48"
TICKET_PRICE_MDL = 6
CHOOSE_TYPE, ENTER_NUMBER = range(2)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def get_font(size, bold=False):
    candidates = [
        "SF-Pro-Text-Bold.otf"    if bold else "SF-Pro-Text-Regular.otf",
        "SF-Pro-Display-Bold.otf" if bold else "SF-Pro-Display-Regular.otf",
        f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
        f"/usr/share/fonts/truetype/crosextra/Carlito-{'Bold' if bold else 'Regular'}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except:
            pass
    return ImageFont.load_default()


def make_ticket_image(transport_type: str, board_number: str) -> io.BytesIO:
    now         = datetime.now()
    valid_until = now + timedelta(hours=1)
    ticket_no   = str(random.randint(100_000_000, 999_999_999))
    date_str    = now.strftime("%d.%m.%Y")
    time_from   = now.strftime("%H:%M")
    time_to     = valid_until.strftime("%H:%M")
    time_now    = now.strftime("%H:%M")

    W, H = 750, 1624
    img = Image.new("RGB", (W, H), "#1C1C1E")
    d   = ImageDraw.Draw(img)

    # Backgrounds
    d.rectangle([0, 0,     W, 249],   fill="#1C1C1E")
    d.rectangle([0, 249,   W, H-120], fill="#000000")
    d.rectangle([0, H-120, W, H],     fill="#1C1C1E")

    # Fonts — SF Pro Text, scaled for 750px 2x retina
    f_status    = get_font(28)
    f_sender    = get_font(32, bold=True)
    f_ts        = get_font(24)
    f_bubble    = get_font(36, bold=True)   # green bubble number
    f_body      = get_font(32, bold=True)   # white text in bubbles
    f_ticket_no = get_font(32)              # blue ticket number — Regular not Bold

    # ── Status bar ────────────────────────────────────────────────────────────
    d.text((44, 44), time_now, font=f_status, fill="#FFFFFF")
    d.text((W-160, 44), "▶ 4G", font=f_status, fill="#FFFFFF")
    d.rectangle([W-80, 48, W-40, 68], outline="#FFFFFF", width=2)
    d.rectangle([W-78, 50, W-60, 66], fill="#FFFFFF")

    # ── Nav bar ───────────────────────────────────────────────────────────────
    d.ellipse([32, 72, 104, 144], fill="#3478F6")
    bbox = d.textbbox((0,0), "15", font=f_ts)
    tw = bbox[2]-bbox[0]
    d.text((32+(72-tw)//2, 86), "15", font=f_ts, fill="#FFFFFF")

    d.ellipse([W//2-52, 56, W//2+52, 160], fill="#636366")
    d.ellipse([W//2-18, 76, W//2+18, 116], fill="#AEAEB2")
    d.ellipse([W//2-34, 114, W//2+34, 168], fill="#AEAEB2")

    bbox = d.textbbox((0,0), "7000", font=f_sender)
    tw = bbox[2]-bbox[0]
    d.text((W//2-tw//2, 168), "7000", font=f_sender, fill="#FFFFFF")
    d.text((W//2+tw//2+6, 172), ">", font=f_ts, fill="#636366")
    d.line([0, 208, W, 208], fill="#38383A", width=1)

    # ── Timestamp ─────────────────────────────────────────────────────────────
    for i, txt in enumerate(["Text Message", f"Today {time_now}"]):
        bbox = d.textbbox((0,0), txt, font=f_ts)
        tw = bbox[2]-bbox[0]
        d.text((W//2-tw//2, 256+i*32), txt, font=f_ts, fill="#8E8E93")

    # ── Green bubble ──────────────────────────────────────────────────────────
    bbox = d.textbbox((0,0), board_number, font=f_bubble)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    pad_x = 38
    gb_w  = max(140, tw + pad_x*2)
    gb_h  = 72
    gb_r  = W - 28
    gb_l  = gb_r - gb_w
    gb_t  = 360
    gb_b  = gb_t + gb_h
    d.rounded_rectangle([gb_l, gb_t, gb_r, gb_b], radius=22, fill="#3AC85A")
    d.text((gb_l+(gb_w-tw)//2, gb_t+(gb_h-th)//2-2), board_number, font=f_bubble, fill="#FFFFFF")

    # ── Bubble 1 — procesare ─────────────────────────────────────────────────
    # Măsurăm textul ca să facem bubble exact cât trebuie
    line1 = "Solicitarea este in curs de"
    line2 = "procesare."
    b1_pad_x, b1_pad_y = 22, 20
    b1_line_h = 42
    b1_w = 514
    b1_h = b1_pad_y*2 + b1_line_h*2
    b1_l, b1_t = 26, 448
    b1_r = b1_l + b1_w
    b1_b = b1_t + b1_h
    d.rounded_rectangle([b1_l, b1_t, b1_r, b1_b], radius=22, fill="#262626")
    d.text((b1_l+b1_pad_x, b1_t+b1_pad_y),           line1, font=f_body, fill="#FFFFFF")
    d.text((b1_l+b1_pad_x, b1_t+b1_pad_y+b1_line_h), line2, font=f_body, fill="#FFFFFF")

    # ── Bubble 2 — bilet ─────────────────────────────────────────────────────
    ticket_lines = [
        ("Bilet electronic nr.",              f_body,      "#FFFFFF"),
        (ticket_no,                           f_ticket_no, "#3478F6"),
        (date_str,                            f_body,      "#FFFFFF"),
        (f"Valabil 1 ora (de la {time_from}", f_body,      "#FFFFFF"),
        (f"pina la {time_to})",               f_body,      "#FFFFFF"),
        (f"Pret {TICKET_PRICE_MDL} MDL",      f_body,      "#FFFFFF"),
        (f"Numar de bord {board_number}",     f_body,      "#FFFFFF"),
    ]
    b2_pad_x, b2_pad_y = 22, 20
    b2_line_h = 38
    b2_l = 26
    b2_t = b1_b + 12
    b2_w = 514
    b2_h = b2_pad_y*2 + len(ticket_lines)*b2_line_h
    b2_r = b2_l + b2_w
    b2_b = b2_t + b2_h
    d.rounded_rectangle([b2_l, b2_t, b2_r, b2_b], radius=22, fill="#262626")
    y = b2_t + b2_pad_y
    for text, fnt, color in ticket_lines:
        d.text((b2_l+b2_pad_x, y), text, font=fnt, fill=color)
        y += b2_line_h

    # ── Bottom bar ────────────────────────────────────────────────────────────
    bar_y = H - 94
    d.ellipse([18, bar_y, 68, bar_y+50], fill="#636366")
    d.text((26, bar_y+8), "+", font=f_sender, fill="#FFFFFF")
    d.rounded_rectangle([78, bar_y, W-20, bar_y+50], radius=25, fill="#1C1C1E", outline="#38383A", width=1)
    bbox = d.textbbox((0,0), "Text Message", font=f_ts)
    tw = bbox[2]-bbox[0]
    d.text((78+(W-98-tw)//2, bar_y+12), "Text Message", font=f_ts, fill="#636366")
    d.rounded_rectangle([W//2-66, H-14, W//2+66, H-4], radius=4, fill="#FFFFFF")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ── Telegram handlers ─────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[
        InlineKeyboardButton("🚎 Troleibuz", callback_data="trolleybus"),
        InlineKeyboardButton("🚌 Autobuz",   callback_data="bus"),
    ]]
    await update.message.reply_text(
        "👋 Bun venit!\nSelectează tipul transportului:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_TYPE


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["transport_type"] = query.data
    label = "Troleibuz" if query.data == "trolleybus" else "Autobuz"
    await query.edit_message_text(
        f"✅ Ai ales: *{label}*\n\nIntrodu *numărul de bord* (4 cifre, ex: 3038):",
        parse_mode="Markdown",
    )
    return ENTER_NUMBER


async def enter_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    board = update.message.text.strip()
    if not board.isdigit() or len(board) != 4:
        await update.message.reply_text("⚠️ Număr invalid. Introdu exact 4 cifre (ex: 3038).")
        return ENTER_NUMBER

    transport_type = context.user_data.get("transport_type", "trolleybus")
    await update.message.reply_text("⏳ Se generează biletul...")
    image_buf = make_ticket_image(transport_type, board)
    await update.message.reply_photo(photo=image_buf)

    keyboard = [[InlineKeyboardButton("🎫 Cumpără alt bilet", callback_data="restart")]]
    await update.message.reply_text("Dorești alt bilet?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


async def restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [[
        InlineKeyboardButton("🚎 Troleibuz", callback_data="trolleybus"),
        InlineKeyboardButton("🚌 Autobuz",   callback_data="bus"),
    ]]
    await query.edit_message_text("Selectează tipul transportului:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_TYPE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Anulat. Scrie /start pentru un bilet nou.")
    return ConversationHandler.END


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(restart_callback, pattern="^restart$"),
        ],
        states={
            CHOOSE_TYPE: [
                CallbackQueryHandler(choose_type, pattern="^(trolleybus|bus)$"),
                CallbackQueryHandler(restart_callback, pattern="^restart$"),
            ],
            ENTER_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_number)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    logger.info("Bot started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()