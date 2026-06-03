"""
handlers/callbacks.py — معالج أزرار الإنلاين
"""
import json
import os
import time
import base64
from datetime import date

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.ai import ai_generate
from bot.database import (
    register_user, is_banned, get_leaderboard, get_projects,
    get_stats, get_deployments, clear_chat_history,
    save_deployment, get_challenge, save_challenge
)
from bot.keyboards import (
    main_keyboard, back_keyboard, exec_keyboard,
    ai_keyboard, learn_keyboard, tools_keyboard
)

OWNER_ID     = int(os.getenv("OWNER_ID", "0"))
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
LANG_NAMES   = {
    "py": "Python 🐍", "java": "Java ☕", "js": "JavaScript 🟨",
    "cpp": "C++ 🔵",   "bash": "Bash ⚡"
}


# ─── helpers ─────────────────────────────────────────────────
def _guard(q, user):
    if is_banned(user.id):
        return True
    register_user(user)
    return False


# ─── القوائم ─────────────────────────────────────────────────
async def menu_exec(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if _guard(q, update.effective_user): return
    await q.edit_message_text("💻 *اختر لغة البرمجة:*", parse_mode="Markdown",
                               reply_markup=exec_keyboard())


async def menu_ai(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if _guard(q, update.effective_user): return
    await q.edit_message_text("🤖 *أدوات الذكاء الاصطناعي:*", parse_mode="Markdown",
                               reply_markup=ai_keyboard())


async def menu_learn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if _guard(q, update.effective_user): return
    await q.edit_message_text("🎓 *تعلّم البرمجة:*", parse_mode="Markdown",
                               reply_markup=learn_keyboard())


async def menu_tools(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if _guard(q, update.effective_user): return
    await q.edit_message_text("🔧 *الأدوات المساعدة:*", parse_mode="Markdown",
                               reply_markup=tools_keyboard())


async def back_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear()
    await q.edit_message_text("🤖 *karasven AI*\n\nاختر ما تريد 👇",
                               reply_markup=main_keyboard(), parse_mode="Markdown")


# ─── تنفيذ — اختيار لغة ─────────────────────────────────────
async def select_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if _guard(q, update.effective_user): return
    lang = q.data.split("_")[1]
    ctx.user_data.clear()
    ctx.user_data["mode"] = "exec"
    ctx.user_data["lang"] = lang
    await q.edit_message_text(
        f"📝 أرسل كود *{LANG_NAMES.get(lang, lang)}* وسأنفذه فوراً:\n\n"
        f"_(أو أرسل ملف `.{lang}` مباشرة)_",
        parse_mode="Markdown"
    )


# ─── أزرار AI ────────────────────────────────────────────────
async def generate_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "generate"
    await q.edit_message_text(
        "🤖 *كود من فكرة*\n\nأرسل فكرة مشروعك وأذكر اللغة إن أردت\n"
        "_(مثال: برنامج Python لإدارة مهام)_",
        parse_mode="Markdown"
    )


async def ai_review_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "ai_review"
    await q.edit_message_text(
        "🔍 *مراجعة كود*\n\nأرسل كودك وسأعطيك تقرير عن:\n"
        "الجودة • الأداء • الأمان • اقتراحات التحسين",
        parse_mode="Markdown"
    )


async def ai_explain_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "ai_explain"
    await q.edit_message_text(
        "📝 *شرح كود*\n\nأرسل أي كود وسأشرحه لك سطراً بسطر بالعربي:",
        parse_mode="Markdown"
    )


async def ai_convert_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "ai_convert"
    await q.edit_message_text(
        "🔄 *تحويل لغات*\n\nأرسل كودك مع ذكر اللغة المستهدفة\n"
        "_(مثال: حوّل هذا لـ JavaScript)_",
        parse_mode="Markdown"
    )


async def ai_docs_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "ai_docs"
    await q.edit_message_text(
        "📄 *توثيق تلقائي*\n\nأرسل كودك وسأكتب له:\n• Docstrings • README • شرح الدوال",
        parse_mode="Markdown"
    )


# ─── تعلّم ───────────────────────────────────────────────────
async def challenge_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    today = date.today().isoformat()
    row   = get_challenge(today)
    if row:
        challenge = row[0]
    else:
        await q.edit_message_text("⏳ جاري توليد تحدي اليوم...")
        challenge = ai_generate(
            "أنشئ تحدي برمجي يومي متوسط الصعوبة بالعربية.\n"
            "اكتب: العنوان، وصف المشكلة، مثال الدخل والخرج المتوقع، ثم تلميح.\n"
            "لا تكتب الحل."
        )
        save_challenge(today, challenge)
    await q.edit_message_text(
        f"🎯 *تحدي اليوم — {today}*\n\n{challenge[:2000]}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ عرض الحل", callback_data="challenge_sol")],
            [InlineKeyboardButton("🔙 رجوع",    callback_data="back")],
        ])
    )


async def challenge_sol_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    today = date.today().isoformat()
    row   = get_challenge(today)
    if not row:
        await q.edit_message_text("❌ لا يوجد تحدي اليوم بعد.", reply_markup=back_keyboard())
        return
    await q.edit_message_text("⏳ جاري توليد الحل...")
    sol = ai_generate(f"أعطني حل Python كامل لهذا التحدي:\n{row[0]}")
    try:
        await q.edit_message_text(f"✅ *الحل:*\n{sol[:3000]}", parse_mode="Markdown",
                                   reply_markup=back_keyboard())
    except Exception:
        await q.edit_message_text(f"✅ الحل:\n{sol[:3000]}", reply_markup=back_keyboard())


async def learn_concept_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "learn_concept"
    await q.edit_message_text(
        "❓ *شرح مفهوم*\n\nأرسل اسم المفهوم الذي تريد فهمه\n"
        "_(مثال: ما هو الـ OOP؟ أو ما هي الـ recursion?)_",
        parse_mode="Markdown"
    )


async def learn_quiz_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "quiz_start"
    await q.edit_message_text(
        "📝 *اختبر معرفتك*\n\nاختر مستوى السؤال:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 مبتدئ",  callback_data="quiz_easy")],
            [InlineKeyboardButton("🟡 متوسط",  callback_data="quiz_medium")],
            [InlineKeyboardButton("🔴 متقدم",  callback_data="quiz_hard")],
            [InlineKeyboardButton("🔙 رجوع",   callback_data="back")],
        ])
    )


async def quiz_level(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    level_map = {"quiz_easy": "مبتدئ", "quiz_medium": "متوسط", "quiz_hard": "متقدم"}
    level = level_map.get(q.data, "متوسط")
    await q.edit_message_text("⏳ جاري توليد السؤال...")
    question = ai_generate(
        f"أنشئ سؤال اختيار من متعدد في البرمجة بمستوى {level}.\n"
        "الصيغة:\n❓ السؤال\nأ) ...\nب) ...\nج) ...\nد) ...\nالجواب الصحيح: (حرف فقط)"
    )
    ctx.user_data["mode"]     = "quiz_answer"
    ctx.user_data["quiz"]     = question
    ans_line = [l for l in question.split("\n") if l.strip().startswith("الجواب")]
    ctx.user_data["quiz_ans"] = ans_line[0] if ans_line else "?"
    display = "\n".join(l for l in question.split("\n") if not l.strip().startswith("الجواب"))
    try:
        await q.edit_message_text(
            f"📝 *السؤال:*\n\n{display[:1500]}\n\n✏️ أرسل حرف إجابتك (أ / ب / ج / د):",
            parse_mode="Markdown"
        )
    except Exception:
        await q.edit_message_text(f"السؤال:\n{display[:1500]}\n\nأرسل حرف إجابتك:")


# ─── أدوات ───────────────────────────────────────────────────
async def tool_api_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "tool_api"
    await q.edit_message_text(
        "🔌 *قارئ API*\n\nأرسل رابط API وسأجلب البيانات وأشرحها:\n"
        "_(مثال: https://api.github.com/users/torvalds)_",
        parse_mode="Markdown"
    )


async def tool_json_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "tool_json"
    await q.edit_message_text(
        "🔄 *محوّل JSON ↔ Python*\n\n"
        "أرسل JSON وسأحوله لـ Python dict، أو أرسل Python dict وسأحوله لـ JSON:",
        parse_mode="Markdown"
    )


async def tool_detect_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "tool_detect"
    await q.edit_message_text(
        "🔍 *كشف لغة الكود*\n\nأرسل أي كود وسأخبرك بلغته وأعطيك معلومات عنه:",
        parse_mode="Markdown"
    )


async def tool_share_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "tool_share"
    await q.edit_message_text(
        "🔗 *مشاركة الكود*\n\nأرسل الكود وسأنشئ لك رابط مشاركة:",
        parse_mode="Markdown"
    )


async def tool_install_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "tool_install"
    await q.edit_message_text(
        "📦 *تثبيت مكتبة Python*\n\n"
        "اكتب اسم المكتبة أو أكثر مفصولة بمسافات:\n\n"
        "📌 *أمثلة:*\n`numpy`\n`pandas matplotlib`\n`requests beautifulsoup4`",
        parse_mode="Markdown"
    )


async def tool_zip_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "tool_zip"
    await q.edit_message_text(
        "🗜️ *مشروع ZIP*\n\n"
        "صف المشروع الذي تريده وسأبنيه لك وأرفعه ZIP جاهز للتحميل!\n\n"
        "📌 *أمثلة:*\n"
        "`بوت تيليجرام بسيط يرد على الرسائل بـ Python`\n"
        "`موقع HTML+CSS+JS لمعرض صور`\n"
        "`API Flask بيحسب العمليات الحسابية`\n"
        "`سكريبت Bash لعمل backup للملفات`",
        parse_mode="Markdown"
    )


# ─── باقي الأزرار ────────────────────────────────────────────
async def chat_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    clear_chat_history(update.effective_user.id)
    ctx.user_data.clear(); ctx.user_data["mode"] = "chat"
    await q.edit_message_text(
        "💬 *محادثة ذكية*\n\nاسألني أي شيء في البرمجة أو الأكواد 👇",
        parse_mode="Markdown"
    )


async def host_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear(); ctx.user_data["mode"] = "host_step1"
    await q.edit_message_text(
        "🌐 *استضافة أكواد مجانية*\n\n"
        "🔹 HTML/CSS/JS — مواقع ثابتة\n"
        "🔹 Python Flask — مواقع ديناميكية\n\n"
        "📤 أرسل كود موقعك الآن:",
        parse_mode="Markdown"
    )


async def host_deploy_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid   = update.effective_user.id
    code  = ctx.user_data.get("host_code", "")
    fname = ctx.user_data.get("host_filename", "index.html")
    if not code:
        await q.edit_message_text("❌ لم يتم إرسال كود.", reply_markup=back_keyboard())
        return
    await q.edit_message_text("⏳ جاري رفع موقعك...")
    url, err = await _deploy_to_vercel(code, fname, uid)
    if url:
        await q.edit_message_text(
            f"✅ *تم رفع الموقع!*\n\n🔗 `{url}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 افتح الموقع", url=url)],
                [InlineKeyboardButton("🔙 رجوع",        callback_data="back")],
            ])
        )
    else:
        await q.edit_message_text(f"❌ *فشل النشر*\n{err}", parse_mode="Markdown",
                                   reply_markup=back_keyboard())
    ctx.user_data.clear()


async def leaderboard_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    rows = get_leaderboard()
    if not rows:
        await q.edit_message_text("📊 لا توجد بيانات بعد.", reply_markup=back_keyboard())
        return
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    text   = "📊 *لوحة المتصدرين:*\n\n"
    for i, (name, ex, ai_c) in enumerate(rows):
        text += f"{medals[i]} *{name}*\n   ⚡ {ex} تنفيذ  |  🤖 {ai_c} AI  |  مجموع: {ex+ai_c}\n\n"
    await q.edit_message_text(text[:3500], parse_mode="Markdown", reply_markup=back_keyboard())


async def show_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query; await q.answer()
    uid = update.effective_user.id
    projects = get_projects(uid)
    if not projects:
        await q.edit_message_text(
            "📂 لا توجد مشاريع بعد.\n\nابدأ بتنفيذ أو توليد كود!",
            reply_markup=back_keyboard()
        )
        return
    text = "📂 *آخر مشاريعك:*\n\n"
    for p in projects[:6]:
        preview = str(p[1])[:60].replace("\n", " ").replace("*","").replace("`","")
        text += f"🔹 `{p[3]}` — *{p[2]}*\n   {preview}...\n\n"
    await q.edit_message_text(text[:3800], parse_mode="Markdown", reply_markup=back_keyboard())


async def stats_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query; await q.answer()
    uid = update.effective_user.id
    ex, ai_c = get_stats(uid)
    projs    = len(get_projects(uid))
    deploys  = get_deployments(uid)
    text = (
        f"📈 *إحصائياتك:*\n\n"
        f"⚡ أكواد نفّذتها: `{ex}`\n"
        f"🤖 طلبات AI: `{ai_c}`\n"
        f"📁 مشاريع محفوظة: `{projs}`\n"
        f"🌐 مواقع رُفعت: `{len(deploys)}`"
    )
    if deploys:
        text += "\n\n🌐 *آخر نشراتك:*\n"
        for d in deploys[:3]:
            text += f"• [{d[1][:30]}]({d[0]})\n"
    await q.edit_message_text(text, parse_mode="Markdown",
                               reply_markup=back_keyboard(), disable_web_page_preview=True)


async def how_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "📖 *دليل karasven AI*\n\n"
        "💻 *تنفيذ كود* — Python, Java, JS, C++, Bash\n"
        "🤖 *أدوات AI* — توليد، مراجعة، شرح، تحويل، توثيق\n"
        "💬 *محادثة ذكية* — أسئلة وأجوبة برمجية\n"
        "🎓 *تعلّم* — تحدي يومي، اختبار، شرح مفاهيم\n"
        "🌐 *استضافة* — ارفع موقعك HTML/Flask مجاناً\n"
        "🔧 *أدوات* — قارئ API، محوّل JSON، كشف لغة، مشاركة كود\n"
        "📊 *المتصدرين* — لوحة أفضل المستخدمين\n\n"
        "🔑 *الذكاء*: مدعوم بـ Claude AI من Anthropic",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )


async def clear_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query; await q.answer()
    uid = update.effective_user.id
    clear_chat_history(uid)
    ctx.user_data.clear()
    await q.edit_message_text(
        "🗑️ تم مسح محادثتك وبيانات الجلسة.\n\nاختر ما تريد 👇",
        reply_markup=main_keyboard()
    )


# ─── Vercel deploy ───────────────────────────────────────────
async def _deploy_to_vercel(code: str, filename: str, uid: int):
    if not VERCEL_TOKEN:
        return None, "❌ VERCEL_TOKEN غير مضبوط"
    project_name = f"ksv-{uid}-{int(time.time())}"
    if filename.endswith(".html"):
        files = [{"file": "index.html", "data": base64.b64encode(code.encode()).decode()}]
    elif filename.endswith(".py"):
        files = [
            {"file": "api/index.py", "data": base64.b64encode(code.encode()).decode()},
            {"file": "vercel.json",  "data": base64.b64encode(json.dumps({
                "builds": [{"src": "api/index.py", "use": "@vercel/python"}],
                "routes": [{"src": "/(.*)", "dest": "api/index.py"}]
            }).encode()).decode()}
        ]
    else:
        files = [{"file": filename, "data": base64.b64encode(code.encode()).decode()}]
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            "https://api.vercel.com/v13/deployments", headers=headers,
            json={"name": project_name, "files": files,
                  "projectSettings": {"framework": None}, "target": "production"},
            timeout=40
        )
        data = resp.json()
        if resp.status_code in (200, 201):
            url = f"https://{data.get('url', project_name + '.vercel.app')}"
            save_deployment(uid, url, project_name)
            return url, None
        return None, f"❌ Vercel: {data.get('error', {}).get('message', str(data))[:200]}"
    except Exception as e:
        return None, f"❌ خطأ اتصال: {e}"
