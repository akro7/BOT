"""
keyboards.py — كل الكيبوردات Inline
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💻 تنفيذ كود",    callback_data="menu_exec"),
         InlineKeyboardButton("🤖 أدوات AI",     callback_data="menu_ai")],
        [InlineKeyboardButton("💬 محادثة ذكية",  callback_data="chat"),
         InlineKeyboardButton("🎓 تعلّم",         callback_data="menu_learn")],
        [InlineKeyboardButton("🌐 استضافة أكواد", callback_data="host"),
         InlineKeyboardButton("🔧 أدوات مساعدة", callback_data="menu_tools")],
        [InlineKeyboardButton("📊 المتصدرين",     callback_data="leaderboard"),
         InlineKeyboardButton("📂 مشاريعي",       callback_data="show")],
        [InlineKeyboardButton("📈 إحصائياتي",     callback_data="stats"),
         InlineKeyboardButton("📖 مساعدة",        callback_data="how")],
        [InlineKeyboardButton("🗑️ مسح الكل",      callback_data="clear")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back")]])


def exec_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🐍 Python",     callback_data="lang_py"),
         InlineKeyboardButton("☕ Java",        callback_data="lang_java")],
        [InlineKeyboardButton("🟨 JavaScript", callback_data="lang_js"),
         InlineKeyboardButton("🔵 C++",        callback_data="lang_cpp")],
        [InlineKeyboardButton("⚡ Bash",        callback_data="lang_bash")],
        [InlineKeyboardButton("🔙 رجوع",       callback_data="back")],
    ])


def ai_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ كود من فكرة",   callback_data="generate"),
         InlineKeyboardButton("🔍 مراجعة كود",   callback_data="ai_review")],
        [InlineKeyboardButton("📝 شرح كود",      callback_data="ai_explain"),
         InlineKeyboardButton("🔄 تحويل لغات",   callback_data="ai_convert")],
        [InlineKeyboardButton("📄 توثيق تلقائي", callback_data="ai_docs")],
        [InlineKeyboardButton("🔙 رجوع",         callback_data="back")],
    ])


def learn_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 تحدي اليوم",    callback_data="challenge"),
         InlineKeyboardButton("📝 اختبر نفسك",   callback_data="learn_quiz")],
        [InlineKeyboardButton("❓ شرح مفهوم",     callback_data="learn_concept")],
        [InlineKeyboardButton("🔙 رجوع",          callback_data="back")],
    ])


def tools_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔌 قارئ API",       callback_data="tool_api"),
         InlineKeyboardButton("🔄 JSON↔Python",    callback_data="tool_json")],
        [InlineKeyboardButton("🔍 كشف لغة الكود", callback_data="tool_detect"),
         InlineKeyboardButton("🔗 مشاركة كود",    callback_data="tool_share")],
        [InlineKeyboardButton("🗜️ مشروع ZIP",      callback_data="tool_zip"),
         InlineKeyboardButton("📦 تثبيت مكتبة",   callback_data="tool_install")],
        [InlineKeyboardButton("🔙 رجوع",           callback_data="back")],
    ])
