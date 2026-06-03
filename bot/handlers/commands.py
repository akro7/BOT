"""
handlers/commands.py — أوامر المالك والمستخدمين
"""
import asyncio
import os

from telegram import Update
from telegram.ext import ContextTypes

from bot.database import (
    register_user, is_banned, all_users, get_all_users_info,
    ban_user, unban_user, save_message_map, get_user_from_admin_msg
)
from bot.keyboards import main_keyboard

OWNER_ID   = int(os.getenv("OWNER_ID", "0"))
OWNER_USER = os.getenv("OWNER_USER", "")


# ─── /start ──────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_banned(user.id):
        await update.message.reply_text("🚫 أنت محظور من استخدام هذا البوت.")
        return
    register_user(user)
    await update.message.reply_text(
        f"👋 أهلاً *{user.first_name}*!\n\n"
        "🤖 *karasven AI* — مساعدك البرمجي الذكي\n\n"
        "اختر ما تريد 👇",
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )


# ─── /ban ────────────────────────────────────────────────────
async def cmd_ban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not ctx.args:
        await update.message.reply_text("استخدام: /ban [ID] [السبب اختياري]")
        return
    try:
        target_id = int(ctx.args[0])
        reason    = " ".join(ctx.args[1:]) if len(ctx.args) > 1 else ""
        ban_user(target_id, reason)
        await update.message.reply_text(f"✅ تم حظر `{target_id}`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ ID غير صحيح")


# ─── /unban ──────────────────────────────────────────────────
async def cmd_unban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not ctx.args:
        await update.message.reply_text("استخدام: /unban [ID]")
        return
    try:
        target_id = int(ctx.args[0])
        unban_user(target_id)
        await update.message.reply_text(f"✅ تم رفع الحظر عن `{target_id}`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ ID غير صحيح")


# ─── /users ──────────────────────────────────────────────────
async def cmd_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    rows = get_all_users_info()
    if not rows:
        await update.message.reply_text("لا يوجد مستخدمون بعد.")
        return
    text = f"👥 *المستخدمون ({len(rows)}):*\n\n"
    for r in rows:
        uname = f"@{r[2]}" if r[2] else "لا يوزر"
        text += f"• `{r[0]}` — {r[1]} ({uname}) — {r[3]}\n"
    await update.message.reply_text(text[:4000], parse_mode="Markdown")


# ─── /broadcast ──────────────────────────────────────────────
async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not ctx.args:
        await update.message.reply_text("استخدام: /broadcast [الرسالة]")
        return
    msg   = " ".join(ctx.args)
    users = all_users()
    sent  = 0
    for uid in users:
        try:
            await ctx.bot.send_message(uid, f"📢 *إعلان:*\n\n{msg}", parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await update.message.reply_text(f"✅ تم الإرسال لـ {sent}/{len(users)} مستخدم")


# ─── إشعارات المالك ──────────────────────────────────────────
async def notify_owner(bot, text: str) -> int | None:
    try:
        sent = await bot.send_message(chat_id=OWNER_ID, text=text, parse_mode="Markdown")
        return sent.message_id
    except Exception as e:
        print(f"[notify_owner] {e}")
        return None


async def forward_to_owner(bot, user, text: str):
    if user.id == OWNER_ID:
        return
    name     = user.full_name or "بدون اسم"
    username = f"@{user.username}" if user.username else "لا يوزر"
    msg_text = (
        f"📩 *رسالة جديدة*\n"
        f"👤 {name}  |  {username}\n"
        f"🆔 `{user.id}`\n\n"
        f"💬 {text[:800]}"
    )
    mid = await notify_owner(bot, msg_text)
    if mid:
        save_message_map(mid, user.id)
