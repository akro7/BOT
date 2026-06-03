"""
handlers/messages.py — معالج الرسائل النصية والملفات
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile

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

# ─── امتدادات مدعومة ──────────────────────────────────────────
CODE_EXTS  = {"py", "js", "java", "cpp", "sh", "c", "ts", "go", "rs", "php", "rb", "kt", "swift"}
TEXT_EXTS  = {"txt", "md", "log", "csv", "ini", "cfg", "env"}
DATA_EXTS  = {"json", "xml", "yaml", "yml", "toml"}
IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp", "bmp"}
EXEC_MAP   = {"py": "py", "js": "js", "java": "java", "cpp": "cpp",
               "sh": "bash", "c": "cpp", "ts": "js"}


# ═══════════════════════════════════════════════════════════════
# رسائل نصية
# ═══════════════════════════════════════════════════════════════
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_banned(user.id):
        return
    register_user(user)

    uid  = user.id
    text = update.message.text or ""
    mode = ctx.user_data.get("mode", "")

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

    # ── 🗜️ مشروع ZIP ─────────────────────────────────────────
    elif mode == "tool_zip":
        msg = await update.message.reply_text("🗜️ جاري بناء المشروع وتجهيز الـ ZIP...")
        inc_ai(uid)
        zip_buf, project_name, summary = await _build_zip_project(text)
        if zip_buf is None:
            await msg.edit_text(f"❌ فشل في توليد المشروع:\n{summary}", reply_markup=back_keyboard())
            ctx.user_data.clear()
            return
        await msg.edit_text(
            f"✅ *تم بناء المشروع بنجاح!*\n\n📁 اسم المشروع: `{project_name}`\n\n{summary}",
            parse_mode="Markdown"
        )
        await update.message.reply_document(
            document=zip_buf,
            filename=f"{project_name}.zip",
            caption=f"🗜️ *{project_name}.zip* — جاهز للتحميل!",
            parse_mode="Markdown"
        )
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())
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


# ═══════════════════════════════════════════════════════════════
# معالج الملفات — موسّع
# ═══════════════════════════════════════════════════════════════
async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_banned(user.id):
        return
    register_user(user)

    doc: Document = update.message.document
    if not doc:
        return

    fname = doc.file_name or "file"
    ext   = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    uid   = user.id

    # ── ملفات الكود → تنفيذ ──────────────────────────────────
    if ext in CODE_EXTS:
        lang = EXEC_MAP.get(ext, "py")
        msg  = await update.message.reply_text(
            f"📥 جاري تنزيل وتنفيذ `{fname}`...", parse_mode="Markdown"
        )
        try:
            code = await _download_text(doc)
            inc_exec(uid)
            save_project(uid, code[:3000], lang)
            output = await run_code(lang, code)
            try:
                await msg.edit_text(
                    f"📤 *نتيجة تنفيذ `{fname}`:*\n```\n{output}\n```",
                    parse_mode="Markdown"
                )
            except Exception:
                await msg.edit_text(f"📤 نتيجة:\n{output}")
            if uid != OWNER_ID:
                await forward_to_owner(ctx.bot, user, f"[أرسل ملف: {fname}]\n{code[:200]}")
        except Exception as e:
            await msg.edit_text(f"❌ خطأ في معالجة الملف: {e}")

    # ── ملفات نصية → قراءة + تحليل ───────────────────────────
    elif ext in TEXT_EXTS:
        msg = await update.message.reply_text(f"📄 جاري قراءة `{fname}`...", parse_mode="Markdown")
        try:
            content = await _download_text(doc)
            preview = content[:500]
            inc_ai(uid)
            analysis = ai_generate(
                f"حلّل هذا الملف النصي بالعربية وقدّم:\n"
                f"1. ملخص المحتوى\n2. الأفكار الرئيسية\n3. أي ملاحظات مهمة\n\n"
                f"محتوى الملف:\n{content[:3000]}"
            )
            await msg.edit_text(
                f"📄 *تحليل `{fname}`:*\n\n{analysis[:3500]}",
                parse_mode="Markdown"
            )
        except Exception as e:
            await msg.edit_text(f"❌ خطأ: {e}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())

    # ── ملفات البيانات → تحليل هيكلي ─────────────────────────
    elif ext in DATA_EXTS:
        msg = await update.message.reply_text(f"🔄 جاري تحليل `{fname}`...", parse_mode="Markdown")
        try:
            content = await _download_text(doc)
            if ext == "json":
                try:
                    parsed   = json.loads(content)
                    if isinstance(parsed, list):
                        structure = f"مصفوفة بـ {len(parsed)} عنصر"
                    elif isinstance(parsed, dict):
                        structure = f"كائن بـ {len(parsed)} مفتاح: {', '.join(list(parsed.keys())[:10])}"
                    else:
                        structure = str(type(parsed).__name__)
                    preview_str = json.dumps(parsed, ensure_ascii=False, indent=2)[:800]
                except Exception:
                    structure   = "JSON غير صالح"
                    preview_str = content[:800]
                info = f"📊 الهيكل: {structure}\n\n```json\n{preview_str}\n```"
            else:
                info = f"```\n{content[:1000]}\n```"

            inc_ai(uid)
            summary = ai_generate(
                f"حلّل هذا الملف ({ext.upper()}) بالعربية:\n"
                f"1. ما وظيفته؟\n2. ما البيانات المخزّنة؟\n3. أي ملاحظات؟\n\nالمحتوى:\n{content[:2000]}"
            )
            try:
                await msg.edit_text(
                    f"🔄 *تحليل `{fname}`:*\n\n{info}\n\n📋 *الملخص:*\n{summary[:1500]}",
                    parse_mode="Markdown"
                )
            except Exception:
                await msg.edit_text(f"تحليل:\n{summary[:3000]}")
        except Exception as e:
            await msg.edit_text(f"❌ خطأ: {e}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())

    # ── ملفات ZIP → قائمة المحتوى + تحليل ───────────────────
    elif ext == "zip":
        msg = await update.message.reply_text(f"🗜️ جاري فحص `{fname}`...", parse_mode="Markdown")
        try:
            raw = await _download_bytes(doc)
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                names    = zf.namelist()
                total    = len(names)
                listing  = "\n".join(f"• `{n}`" for n in names[:30])
                if total > 30:
                    listing += f"\n_... و{total - 30} ملف آخر_"

                # قراءة الملفات النصية الصغيرة للتحليل
                text_samples = []
                for n in names[:10]:
                    if any(n.endswith(e) for e in [".py",".js",".ts",".java",".md",".txt",".json",".sh"]):
                        try:
                            data = zf.read(n)
                            if len(data) < 5000:
                                text_samples.append(f"--- {n} ---\n{data.decode('utf-8', errors='replace')[:500]}")
                        except Exception:
                            pass

            inc_ai(uid)
            context = "\n\n".join(text_samples[:3]) if text_samples else "لا توجد ملفات نصية مقروءة"
            analysis = ai_generate(
                f"حلّل هذا الـ ZIP ({total} ملف) بالعربية:\n"
                f"1. ما نوع المشروع؟\n2. ما اللغات المستخدمة؟\n3. ما الهيكل العام؟\n\n"
                f"قائمة الملفات:\n{chr(10).join(names[:30])}\n\nعينة من المحتوى:\n{context[:1500]}"
            )
            await msg.edit_text(
                f"🗜️ *فحص `{fname}`:*\n\n📦 *{total} ملف:*\n{listing}\n\n📋 *التحليل:*\n{analysis[:1500]}",
                parse_mode="Markdown"
            )
        except Exception as e:
            await msg.edit_text(f"❌ خطأ في فحص الـ ZIP: {e}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())

    # ── ملفات PDF → استخراج نص + تحليل ──────────────────────
    elif ext == "pdf":
        msg = await update.message.reply_text(f"📕 جاري قراءة `{fname}`...", parse_mode="Markdown")
        try:
            raw     = await _download_bytes(doc)
            pdf_text = _extract_pdf_text(raw)
            if not pdf_text.strip():
                pdf_text = "لم يتم العثور على نص قابل للقراءة (قد يكون PDF صور)."
            inc_ai(uid)
            summary = ai_generate(
                f"حلّل هذا PDF بالعربية:\n"
                f"1. ملخص المحتوى\n2. الموضوعات الرئيسية\n3. أهم المعلومات\n\n"
                f"النص:\n{pdf_text[:3000]}"
            )
            await msg.edit_text(
                f"📕 *تحليل `{fname}`:*\n\n{summary[:3500]}",
                parse_mode="Markdown"
            )
        except Exception as e:
            await msg.edit_text(f"❌ خطأ في قراءة PDF: {e}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())

    # ── صور → معلومات + وصف ──────────────────────────────────
    elif ext in IMAGE_EXTS:
        msg = await update.message.reply_text(f"🖼️ جاري تحليل الصورة `{fname}`...", parse_mode="Markdown")
        try:
            raw  = await _download_bytes(doc)
            info = _image_info(raw, fname)
            inc_ai(uid)
            desc = ai_generate(
                f"المستخدم أرسل صورة باسم `{fname}` بالمعلومات التالية:\n{info}\n\n"
                f"صف ما قد تحتوي عليه هذه الصورة بناءً على اسمها ومعلوماتها، "
                f"واقترح ما يمكن فعله بها برمجياً (مثل: ضغط، تحويل صيغة، تحليل pixels، إلخ)"
            )
            await msg.edit_text(
                f"🖼️ *معلومات الصورة:*\n{info}\n\n💡 *اقتراحات:*\n{desc[:2000]}",
                parse_mode="Markdown"
            )
        except Exception as e:
            await msg.edit_text(f"❌ خطأ: {e}")
        await update.message.reply_text("🔁 اختر:", reply_markup=main_keyboard())

    # ── صيغة غير مدعومة ──────────────────────────────────────
    else:
        supported = (
            "📎 *الصيغ المدعومة:*\n\n"
            "💻 *كود:* `.py` `.js` `.java` `.cpp` `.ts` `.go` `.rs` `.php` `.rb` `.kt` `.sh`\n"
            "📄 *نص:* `.txt` `.md` `.log` `.csv`\n"
            "🔄 *بيانات:* `.json` `.xml` `.yaml` `.yml`\n"
            "🗜️ *أرشيف:* `.zip`\n"
            "📕 *مستندات:* `.pdf`\n"
            "🖼️ *صور:* `.jpg` `.png` `.gif` `.webp`"
        )
        await update.message.reply_text(supported, parse_mode="Markdown", reply_markup=back_keyboard())


# ═══════════════════════════════════════════════════════════════
# helpers
# ═══════════════════════════════════════════════════════════════
async def _download_text(doc: Document) -> str:
    file = await doc.get_file()
    buf  = io.BytesIO()
    await file.download_to_memory(buf)
    return buf.getvalue().decode("utf-8", errors="replace")


async def _download_bytes(doc: Document) -> bytes:
    file = await doc.get_file()
    buf  = io.BytesIO()
    await file.download_to_memory(buf)
    return buf.getvalue()


def _extract_pdf_text(raw: bytes) -> str:
    try:
        import fitz  # PyMuPDF
        doc  = fitz.open(stream=raw, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except ImportError:
        pass
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(raw))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception:
        pass
    return ""


def _image_info(raw: bytes, fname: str) -> str:
    lines = [f"• الاسم: `{fname}`", f"• الحجم: `{len(raw) / 1024:.1f} KB`"]
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(raw))
        lines.append(f"• الأبعاد: `{img.width}×{img.height}` بكسل")
        lines.append(f"• الوضع: `{img.mode}`")
        lines.append(f"• الصيغة: `{img.format}`")
    except Exception:
        pass
    return "\n".join(lines)


async def _build_zip_project(description: str):
    """
    يطلب من AI توليد مشروع كامل → يعيد (BytesIO zip, project_name, summary)
    """
    prompt = (
        "أنت مولّد مشاريع برمجية. المستخدم طلب:\n"
        f"{description}\n\n"
        "أجب بـ JSON فقط بهذا الشكل الدقيق (بدون أي نص خارج JSON):\n"
        "{\n"
        '  "project_name": "my_project",\n'
        '  "summary": "وصف قصير للمشروع",\n'
        '  "files": [\n'
        '    {"path": "main.py", "content": "..."},\n'
        '    {"path": "README.md", "content": "..."}\n'
        "  ]\n"
        "}\n\n"
        "القواعد:\n"
        "- project_name: حروف إنجليزية وشرطات فقط\n"
        "- اكتب كوداً حقيقياً كاملاً قابلاً للتشغيل\n"
        "- اشمل README.md دائماً\n"
        "- اشمل requirements.txt إن كان Python\n"
        "- لا تكتب أي شيء خارج الـ JSON\n"
        "- لا تستخدم markdown backticks"
    )

    raw_resp = ai_generate(prompt)

    # تنظيف الرد من أي markdown
    cleaned = re.sub(r"```[a-z]*\n?", "", raw_resp).replace("```", "").strip()

    # استخراج JSON أول كائن كامل
    start = cleaned.find("{")
    end   = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        return None, None, f"الرد لم يكن JSON صحيحاً:\n{raw_resp[:500]}"

    try:
        data = json.loads(cleaned[start:end])
    except json.JSONDecodeError as e:
        return None, None, f"خطأ في تحليل JSON: {e}\n{cleaned[start:start+300]}"

    project_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", data.get("project_name", "project"))
    summary      = data.get("summary", "مشروع مولّد بواسطة AI")
    files        = data.get("files", [])

    if not files:
        return None, None, "لم يتم توليد أي ملفات."

    # بناء ZIP في الذاكرة
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            path    = f.get("path", "file.txt")
            content = f.get("content", "")
            zf.writestr(f"{project_name}/{path}", content)
    zip_buf.seek(0)

    # ملخص الملفات المُنشأة
    file_list = "\n".join(f"  📄 `{f.get('path','?')}`" for f in files)
    full_summary = f"{summary}\n\n*الملفات:*\n{file_list}"

    return zip_buf, project_name, full_summary


def _share_code(code: str):
    try:
        r = requests.post("https://paste.rs", data=code.encode("utf-8"), timeout=10)
        return r.text.strip() if r.status_code == 201 else None
    except Exception:
        return None
