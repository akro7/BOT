"""
ai.py — opencode.ai Zen API (big-pickle)
"""
import os
import time
import requests

_ZEN_URL   = "https://opencode.ai/zen/v1/chat/completions"
_ZEN_MODEL = "big-pickle"

# ضع مفاتيحك في GitHub Secrets باسم OPENCODE_KEYS مفصولة بفاصلة
_raw_keys = os.getenv("OPENCODE_KEYS", "")
_ZEN_KEYS = [k.strip() for k in _raw_keys.split(",") if k.strip()] or ["no-key"]
_KEY_IDX  = 0

SYS_PROMPT = (
    "أنت karasven AI — مساعد برمجة ذكي متكامل باللغة العربية. "
    "اسمك karasven AI وتم تطويرك خصيصاً لمساعدة المبرمجين العرب. "
    "عند السؤال عن هويتك قل: أنا karasven AI، مساعدك البرمجي الذكي. "
    "أجب دائماً بالعربية ما لم يطلب المستخدم غير ذلك. "
    "كن دقيقاً وعملياً في إجاباتك البرمجية. "
    "الأكواد داخل ```language ... ```."
)


def ai_generate(prompt: str, history: list = None) -> str:
    global _KEY_IDX

    messages = [{"role": "system", "content": SYS_PROMPT}]
    if history:
        for role, msg in history[-6:]:
            api_role = "assistant" if role == "model" else "user"
            messages.append({"role": api_role, "content": msg})
    messages.append({"role": "user", "content": prompt})

    for _ in range(len(_ZEN_KEYS) * 2):
        key = _ZEN_KEYS[_KEY_IDX % len(_ZEN_KEYS)]
        try:
            resp = requests.post(
                _ZEN_URL,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": _ZEN_MODEL, "messages": messages, "max_tokens": 2048},
                timeout=40,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            elif resp.status_code in (429, 401, 403):
                _KEY_IDX = (_KEY_IDX + 1) % len(_ZEN_KEYS)
                time.sleep(1)
            else:
                return f"⚠️ خطأ من الخادم: {resp.status_code}"
        except requests.exceptions.Timeout:
            _KEY_IDX = (_KEY_IDX + 1) % len(_ZEN_KEYS)
            time.sleep(1)
        except Exception as e:
            return f"⚠️ خطأ: {e}"

    return "⚠️ تعذّر الاتصال — حاول بعد قليل."
