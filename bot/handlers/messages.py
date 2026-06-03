"""
handlers/messages.py — معالج الرسائل النصية والملفات
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Document
from telegram.ext import ContextTypes

from bot.ai import ai_generate
from bot.database import (
    register_user, is_banned, save_project, save_chat,
    get_chat_history, inc_exec, inc_ai
)
from bot.executor import run_code
from bot.keyboards import main_keyboard, back_keyboard
from bot.handlers.commands import forward_to_owner

OWNER_ID = int(os.getenv("OWNER_ID", "0"))


# ─── رسائل نصية ──────────────────────────────────────────────
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_banned(user.id):
        return
    register_user(user)

    uid  = user.id
    text = update.message.text or ""
    mode = ctx.user_data.get("mode", "")

    # ── رسالة مباشرة بدون وضع → محادثة ذكية ─────────────────
    if not mode:
        ctx.user_data["mode"] = "chat"
        mode = "chat"

    # ── تنفيذ كود ────────────────────────────────────────────
    if mode == "exec":
        lang = ctx.user_data.get("lang", "py")
        msg  = await update.message.reply_text("⚙️ جاري التنفيذ...")
        inc_exec(uid)
        save_project(uid, text[:3000], lang)
        output = await run_code(lang, text)
        try:
            await msg.edit_text(f"📤 *النتيجة:*\n```\n{output}\n```", parse_mode="Markdown")
        except Exception:
            await msg.edit_text(f"📤 النتيجة:\n{output}")
        if uid != OWNER_ID:
            await forward_to_owner(ctx.bot, user, f"[تنفيذ {lang}]\n{text[:200]}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())
        ctx.user_data.clear()

    # ── توليد كود ────────────────────────────────────────────
    elif mode == "generate":
        msg = await update.message.reply_text("✨ جاري توليد الكود...")
        inc_ai(uid)
        code = ai_generate(f"اكتب كوداً برمجياً كاملاً لهذه الفكرة بالعربية مع شرح مختصر:\n{text}")
        try:
            await msg.edit_text(f"✨ *الكود المُولَّد:*\n\n{code[:3800]}", parse_mode="Markdown")
        except Exception:
            await msg.edit_text(f"✨ الكود:\n{code[:3800]}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())
        ctx.user_data.clear()

    # ── مراجعة كود ───────────────────────────────────────────
    elif mode == "ai_review":
        msg = await update.message.reply_text("🔍 جاري مراجعة الكود...")
        inc_ai(uid)
        review = ai_generate(
            f"راجع هذا الكود وأعطني تقريراً شاملاً بالعربية عن:\n"
            f"1. الجودة العامة\n2. الأداء\n3. الأمان\n4. اقتراحات التحسين\n\nالكود:\n{text}"
        )
        try:
            await msg.edit_text(f"🔍 *تقرير المراجعة:*\n\n{review[:3800]}", parse_mode="Markdown")
        except Exception:
            await msg.edit_text(f"🔍 المراجعة:\n{review[:3800]}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())
        ctx.user_data.clear()

    # ── شرح كود ──────────────────────────────────────────────
    elif mode == "ai_explain":
        msg = await update.message.reply_text("📝 جاري شرح الكود...")
        inc_ai(uid)
        expl = ai_generate(f"اشرح هذا الكود بالعربية سطراً بسطر بأسلوب واضح:\n{text}")
        try:
            await msg.edit_text(f"📝 *الشرح:*\n\n{expl[:3800]}", parse_mode="Markdown")
        except Exception:
            await msg.edit_text(f"📝 الشرح:\n{expl[:3800]}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())
        ctx.user_data.clear()

    # ── تحويل لغات ───────────────────────────────────────────
    elif mode == "ai_convert":
        msg = await update.message.reply_text("🔄 جاري التحويل...")
        inc_ai(uid)
        result = ai_generate(
            f"حوّل الكود التالي إلى اللغة المطلوبة مع الحفاظ على نفس المنطق:\n{text}"
        )
        try:
            await msg.edit_text(f"🔄 *الكود المُحوَّل:*\n\n{result[:3800]}", parse_mode="Markdown")
        except Exception:
            await msg.edit_text(f"🔄 النتيجة:\n{result[:3800]}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())
        ctx.user_data.clear()

    # ── توثيق تلقائي ─────────────────────────────────────────
    elif mode == "ai_docs":
        msg = await update.message.reply_text("📄 جاري كتابة التوثيق...")
        inc_ai(uid)
        docs = ai_generate(
            f"اكتب توثيقاً كاملاً بالعربية لهذا الكود يشمل:\n"
            f"• Docstrings لكل دالة\n• README مختصر\n• شرح المعاملات والقيم المُعادة\n\n{text}"
        )
        try:
            await msg.edit_text(f"📄 *التوثيق:*\n\n{docs[:3800]}", parse_mode="Markdown")
        except Exception:
            await msg.edit_text(f"📄 التوثيق:\n{docs[:3800]}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())
        ctx.user_data.clear()

    # ── شرح مفهوم ────────────────────────────────────────────
    elif mode == "learn_concept":
        msg = await update.message.reply_text("⏳ جاري الشرح...")
        inc_ai(uid)
        expl = ai_generate(
            f"اشرح المفهوم التالي بالعربية بأسلوب بسيط مع مثال عملي:\n{text}"
        )
        try:
            await msg.edit_text(f"❓ *شرح:* {text}\n\n{expl[:3500]}", parse_mode="Markdown")
        except Exception:
            await msg.edit_text(f"شرح: {text}\n\n{expl[:3500]}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())
        ctx.user_data.clear()

    # ── إجابة الاختبار ────────────────────────────────────────
    elif mode == "quiz_answer":
        correct_line   = ctx.user_data.get("quiz_ans", "")
        answer         = text.strip()
        correct_letter = ""
        for part in correct_line.split():
            if part in ["أ","ب","ج","د","a","b","c","d"]:
                correct_letter = part
                break
        if correct_letter and (answer == correct_letter or answer.lower() == correct_letter.lower()):
            result = "✅ *إجابة صحيحة!* 🎉"
        else:
            result = f"❌ *إجابة خاطئة.*\n{correct_line}"
        await update.message.reply_text(
            result, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 سؤال جديد", callback_data="learn_quiz")],
                [InlineKeyboardButton("🔙 رجوع",       callback_data="back")],
            ])
        )
        ctx.user_data.clear()

    # ── قارئ API ─────────────────────────────────────────────
    elif mode == "tool_api":
        msg = await update.message.reply_text("🔌 جاري جلب البيانات...")
        try:
            url  = text.strip()
            resp = requests.get(url, timeout=10, headers={"User-Agent": "karasven-bot/2.0"})
            try:
                data = json.dumps(resp.json(), ensure_ascii=False, indent=2)[:1500]
            except Exception:
                data = resp.text[:1000]
            summary = ai_generate(f"لخّص بيانات هذا الـ API بالعربية في 3-5 نقاط مهمة:\n{data[:800]}")
            reply = (
                f"🔌 *استجابة API* — Status: `{resp.status_code}`\n\n"
                f"```json\n{data}\n```\n\n📋 *الملخص:*\n{summary[:500]}"
            )
            try:
                await msg.edit_text(reply[:4000], parse_mode="Markdown")
            except Exception:
                await msg.edit_text(f"Status: {resp.status_code}\n{data}")
        except Exception as e:
            await msg.edit_text(f"❌ خطأ في الجلب: {e}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())
        ctx.user_data.clear()

    # ── محوّل JSON ────────────────────────────────────────────
    elif mode == "tool_json":
        msg = await update.message.reply_text("🔄 جاري التحويل...")
        try:
            txt = text.strip()
            if txt.startswith("{") or txt.startswith("["):
                parsed = json.loads(txt)
                result = f"```python\n{repr(parsed)}\n```"
                label  = "🔄 *JSON → Python dict:*"
            else:
                converted = ai_generate(f"حوّل هذا Python dict/list إلى JSON صحيح:\n{txt}\nأجب بـ JSON فقط.")
                result = f"```json\n{converted[:1500]}\n```"
                label  = "🔄 *Python → JSON:*"
            try:
                await msg.edit_text(f"{label}\n{result}", parse_mode="Markdown")
            except Exception:
                await msg.edit_text(f"النتيجة:\n{result}")
        except Exception as e:
            await msg.edit_text(f"❌ خطأ في التحويل: {e}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())
        ctx.user_data.clear()

    # ── كشف لغة ──────────────────────────────────────────────
    elif mode == "tool_detect":
        msg = await update.message.reply_text("🔍 جاري تحليل الكود...")
        inc_ai(uid)
        result = ai_generate(
            f"حلّل هذا الكود وأخبرني:\n"
            f"1. اللغة البرمجية\n2. الإصدار المحتمل\n3. ماذا يفعل\n4. هل فيه مشاكل واضحة؟\n\n{text}"
        )
        try:
            await msg.edit_text(f"🔍 *تحليل الكود:*\n\n{result[:3000]}", parse_mode="Markdown")
        except Exception:
            await msg.edit_text(f"🔍 تحليل:\n{result[:3000]}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())
        ctx.user_data.clear()

    # ── تثبيت مكتبة ──────────────────────────────────────────
    elif mode == "tool_install":
        raw_pkgs  = text.strip().split()
        safe_pkgs = [p for p in raw_pkgs if re.match(r"^[a-zA-Z0-9_\-\.]+$", p)]
        if not safe_pkgs:
            await update.message.reply_text(
                "⚠️ اسم المكتبة غير صحيح. استخدم أحرف إنجليزية فقط مثل: `numpy`",
                parse_mode="Markdown", reply_markup=back_keyboard()
            )
            ctx.user_data.clear()
            return
        msg = await update.message.reply_text(
            f"📦 جاري تثبيت: {' '.join(safe_pkgs)}\n⏳ قد يستغرق بضع ثوانٍ..."
        )
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet"] + safe_pkgs,
                capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace"
            )
            if result.returncode == 0:
                success_list = "\n".join(f"✅ {p}" for p in safe_pkgs)
                await msg.edit_text(
                    f"📦 تمّ التثبيت بنجاح!\n\n{success_list}\n\nيمكنك الآن استخدامها في كودك 🚀",
                    reply_markup=back_keyboard()
                )
            else:
                err = (result.stderr or result.stdout).strip()[:600]
                await msg.edit_text(f"❌ فشل التثبيت:\n\n{err}", reply_markup=back_keyboard())
        except subprocess.TimeoutExpired:
            await msg.edit_text("⚠️ انتهت المهلة (120 ثانية).", reply_markup=back_keyboard())
        except Exception as e:
            await msg.edit_text(f"❌ خطأ: {e}", reply_markup=back_keyboard())
        ctx.user_data.clear()

    # ── مشاركة كود ───────────────────────────────────────────
    elif mode == "tool_share":
        msg = await update.message.reply_text("🔗 جاري إنشاء رابط المشاركة...")
        url = _share_code(text)
        if url:
            await msg.edit_text(
                f"🔗 *رابط الكود جاهز!*\n\n`{url}`",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 افتح الرابط", url=url)],
                    [InlineKeyboardButton("🔙 رجوع",        callback_data="back")],
                ])
            )
        else:
            await msg.edit_text("❌ فشل إنشاء الرابط. حاول مرة أخرى.", reply_markup=back_keyboard())
        ctx.user_data.clear()

    # ── استضافة — استقبال الكود ──────────────────────────────
    elif mode == "host_step1":
        tl = text.lower()
        if "<html" in tl or "<!doctype" in tl:
            filename, lang_name = "index.html", "HTML"
        elif "from flask" in tl or "import flask" in tl:
            filename, lang_name = "app.py", "Python Flask"
        else:
            filename, lang_name = "index.html", "HTML/Static"
        ctx.user_data["host_code"]     = text
        ctx.user_data["host_filename"] = filename
        ctx.user_data["mode"]          = "host_step2"
        await update.message.reply_text(
            f"🌐 *جاهز للنشر!*\n\n📄 النوع: `{lang_name}`\n📁 الملف: `{filename}`\n\nاضغط 🚀 للرفع:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 ارفع الآن!", callback_data="host_deploy"),
                 InlineKeyboardButton("❌ إلغاء",      callback_data="back")],
            ])
        )

    # ── محادثة ذكية ──────────────────────────────────────────
    elif mode == "chat":
        msg = await update.message.reply_text("💬 جاري المعالجة...")
        try:
            history = get_chat_history(uid)
            save_chat(uid, "user", text)
            inc_ai(uid)
            reply = ai_generate(text, history=history)
            save_chat(uid, "model", reply)
            try:
                await msg.edit_text(f"🤖 {reply[:3800]}", parse_mode="Markdown")
            except Exception:
                await msg.edit_text(f"🤖 {reply[:3800]}")
        except Exception as e:
            await msg.edit_text(f"❌ خطأ: {e}")


# ─── معالج الملفات ───────────────────────────────────────────
async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_banned(user.id):
        return
    register_user(user)

    doc: Document = update.message.document
    if not doc:
        return
    fname    = doc.file_name or ""
    ext      = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    lang_map = {"py": "py", "js": "js", "java": "java", "cpp": "cpp", "sh": "bash", "c": "cpp"}
    lang     = lang_map.get(ext)

    if not lang:
        await update.message.reply_text(
            "📎 أنواع الملفات المدعومة: `.py` `.js` `.java` `.cpp` `.sh`",
            parse_mode="Markdown"
        )
        return

    msg = await update.message.reply_text(f"📥 جاري تنزيل وتنفيذ `{fname}`...", parse_mode="Markdown")
    try:
        file = await doc.get_file()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            await file.download_to_drive(tmp.name)
            with open(tmp.name, "r", encoding="utf-8", errors="replace") as f:
                code = f.read()
            os.unlink(tmp.name)
        inc_exec(user.id)
        save_project(user.id, code[:3000], lang)
        output = await run_code(lang, code)
        try:
            await msg.edit_text(
                f"📤 *نتيجة تنفيذ `{fname}`:*\n```\n{output}\n```",
                parse_mode="Markdown"
            )
        except Exception:
            await msg.edit_text(f"📤 نتيجة:\n{output}")
        if user.id != OWNER_ID:
            await forward_to_owner(ctx.bot, user, f"[أرسل ملف: {fname}]\n{code[:200]}")
    except Exception as e:
        await msg.edit_text(f"❌ خطأ في معالجة الملف: {e}")


# ─── helper ──────────────────────────────────────────────────
def _share_code(code: str):
    try:
        r = requests.post("https://paste.rs", data=code.encode("utf-8"), timeout=10)
        return r.text.strip() if r.status_code == 201 else None
    except Exception:
        return None
