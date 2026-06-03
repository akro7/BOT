"""
main.py — نقطة تشغيل karasven AI Bot
"""
import asyncio
import os
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)

from bot.ai import ai_generate
from bot.database import all_users, save_challenge, get_challenge
from bot.handlers.commands import (
    start, cmd_ban, cmd_unban, cmd_users, cmd_broadcast
)
from bot.handlers.callbacks import (
    menu_exec, menu_ai, menu_learn, menu_tools, back_btn,
    select_lang,
    generate_btn, ai_review_btn, ai_explain_btn, ai_convert_btn, ai_docs_btn,
    challenge_btn, challenge_sol_btn, learn_concept_btn, learn_quiz_btn, quiz_level,
    tool_api_btn, tool_json_btn, tool_detect_btn, tool_share_btn, tool_install_btn,
    host_btn, host_deploy_btn, chat_btn,
    leaderboard_btn, show_btn, stats_btn, how_btn, clear_btn,
)
from bot.handlers.messages import handle_message, handle_document

TOKEN = os.getenv("BOT_TOKEN", "")


# ─── التحدي اليومي ───────────────────────────────────────────
async def send_daily_challenge(bot):
    today = date.today().isoformat()
    row   = get_challenge(today)
    if not row:
        challenge = ai_generate(
            "أنشئ تحدي برمجي يومي متوسط الصعوبة بالعربية. "
            "اكتب: العنوان، المشكلة، مثال دخل/خرج، وتلميح صغير."
        )
        save_challenge(today, challenge)
    else:
        challenge = row[0]

    for uid in all_users():
        try:
            await bot.send_message(
                uid,
                f"🌅 *تحدي اليوم — {today}*\n\n{challenge[:1500]}",
                parse_mode="Markdown"
            )
            await asyncio.sleep(0.05)
        except Exception:
            pass


# ─── main ─────────────────────────────────────────────────────
def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN غير مضبوط في المتغيرات البيئية!")

    app = Application.builder().token(TOKEN).build()

    # أوامر
    app.add_handler(CommandHandler("start",     start))
    app.add_handler(CommandHandler("ban",       cmd_ban))
    app.add_handler(CommandHandler("unban",     cmd_unban))
    app.add_handler(CommandHandler("users",     cmd_users))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))

    # القوائم
    app.add_handler(CallbackQueryHandler(menu_exec,  pattern=r"^menu_exec$"))
    app.add_handler(CallbackQueryHandler(menu_ai,    pattern=r"^menu_ai$"))
    app.add_handler(CallbackQueryHandler(menu_learn, pattern=r"^menu_learn$"))
    app.add_handler(CallbackQueryHandler(menu_tools, pattern=r"^menu_tools$"))
    app.add_handler(CallbackQueryHandler(back_btn,   pattern=r"^back$"))

    # تنفيذ
    app.add_handler(CallbackQueryHandler(select_lang, pattern=r"^lang_"))

    # AI
    app.add_handler(CallbackQueryHandler(generate_btn,   pattern=r"^generate$"))
    app.add_handler(CallbackQueryHandler(ai_review_btn,  pattern=r"^ai_review$"))
    app.add_handler(CallbackQueryHandler(ai_explain_btn, pattern=r"^ai_explain$"))
    app.add_handler(CallbackQueryHandler(ai_convert_btn, pattern=r"^ai_convert$"))
    app.add_handler(CallbackQueryHandler(ai_docs_btn,    pattern=r"^ai_docs$"))

    # تعلّم
    app.add_handler(CallbackQueryHandler(challenge_btn,     pattern=r"^challenge$"))
    app.add_handler(CallbackQueryHandler(challenge_sol_btn, pattern=r"^challenge_sol$"))
    app.add_handler(CallbackQueryHandler(learn_concept_btn, pattern=r"^learn_concept$"))
    app.add_handler(CallbackQueryHandler(learn_quiz_btn,    pattern=r"^learn_quiz$"))
    app.add_handler(CallbackQueryHandler(quiz_level,        pattern=r"^quiz_(easy|medium|hard)$"))

    # أدوات
    app.add_handler(CallbackQueryHandler(tool_api_btn,     pattern=r"^tool_api$"))
    app.add_handler(CallbackQueryHandler(tool_json_btn,    pattern=r"^tool_json$"))
    app.add_handler(CallbackQueryHandler(tool_detect_btn,  pattern=r"^tool_detect$"))
    app.add_handler(CallbackQueryHandler(tool_share_btn,   pattern=r"^tool_share$"))
    app.add_handler(CallbackQueryHandler(tool_install_btn, pattern=r"^tool_install$"))

    # باقي الأزرار
    app.add_handler(CallbackQueryHandler(host_btn,         pattern=r"^host$"))
    app.add_handler(CallbackQueryHandler(host_deploy_btn,  pattern=r"^host_deploy$"))
    app.add_handler(CallbackQueryHandler(chat_btn,         pattern=r"^chat$"))
    app.add_handler(CallbackQueryHandler(leaderboard_btn,  pattern=r"^leaderboard$"))
    app.add_handler(CallbackQueryHandler(show_btn,         pattern=r"^show$"))
    app.add_handler(CallbackQueryHandler(stats_btn,        pattern=r"^stats$"))
    app.add_handler(CallbackQueryHandler(how_btn,          pattern=r"^how$"))
    app.add_handler(CallbackQueryHandler(clear_btn,        pattern=r"^clear$"))

    # رسائل + ملفات
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # جدولة التحدي اليومي الساعة 9 صباحاً
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_challenge, "cron", hour=9, minute=0, args=[app.bot])

    async def on_startup(application):
        scheduler.start()
        print("✅ karasven AI — جاهز 🚀")
        print("   🤖 AI: Claude (Anthropic)")
        print("   💻 لغات: Python | Java | JS | C++ | Bash")

    app.post_init = on_startup
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
