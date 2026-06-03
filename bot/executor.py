"""
executor.py — تنفيذ الأكواد البرمجية
"""
import os
import subprocess
import tempfile
import shutil
import sys

GPP_CMD  = os.getenv("GPP_CMD",  "g++")
JAVA_BIN = os.getenv("JAVA_BIN", "")   # مثال: /usr/lib/jvm/java-17/bin


async def run_code(lang: str, code: str) -> str:
    try:
        if lang == "py":
            return await _run_python(code)
        elif lang == "js":
            return await _run_js(code)
        elif lang == "java":
            return await _run_java(code)
        elif lang == "cpp":
            return await _run_cpp(code)
        elif lang == "bash":
            return await _run_bash(code)
        else:
            return "⚠️ لغة غير مدعومة"
    except subprocess.TimeoutExpired:
        return "⚠️ تجاوز الوقت المسموح (15 ثانية)"
    except FileNotFoundError as e:
        return f"⚠️ أداة غير متوفرة في البيئة: {e}"
    except Exception as e:
        return f"❌ خطأ: {e}"


# ─── Python ──────────────────────────────────────────────────
async def _run_python(code: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", encoding="utf-8", delete=False) as f:
        f.write(code)
        fname = f.name
    r = subprocess.run(
        [sys.executable, fname],
        capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace"
    )
    os.unlink(fname)
    return (r.stdout or r.stderr or "✅ تنفيذ ناجح بدون خرج")[:2000]


# ─── JavaScript ──────────────────────────────────────────────
async def _run_js(code: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", encoding="utf-8", delete=False) as f:
        f.write(code)
        fname = f.name
    r = subprocess.run(
        ["node", fname],
        capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace"
    )
    os.unlink(fname)
    return (r.stdout or r.stderr or "✅ تنفيذ ناجح بدون خرج")[:2000]


# ─── Java ────────────────────────────────────────────────────
async def _run_java(code: str) -> str:
    tmpdir     = tempfile.mkdtemp()
    class_name = "Main"
    for line in code.split("\n"):
        if "public class " in line:
            class_name = line.split("public class ")[1].split()[0].split("{")[0].strip()
            break
    fpath = os.path.join(tmpdir, f"{class_name}.java")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(code)

    javac = os.path.join(JAVA_BIN, "javac") if JAVA_BIN else "javac"
    java  = os.path.join(JAVA_BIN, "java")  if JAVA_BIN else "java"

    comp = subprocess.run([javac, fpath], capture_output=True, text=True, timeout=30, encoding="utf-8")
    if comp.returncode != 0:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return f"❌ خطأ في الترجمة:\n{comp.stderr[:800]}"

    run = subprocess.run(
        [java, "-cp", tmpdir, class_name],
        capture_output=True, text=True, timeout=15, encoding="utf-8"
    )
    shutil.rmtree(tmpdir, ignore_errors=True)
    return (run.stdout or run.stderr or "✅ تنفيذ ناجح بدون خرج")[:2000]


# ─── C++ ─────────────────────────────────────────────────────
async def _run_cpp(code: str) -> str:
    tmpdir  = tempfile.mkdtemp()
    src     = os.path.join(tmpdir, "main.cpp")
    out_bin = os.path.join(tmpdir, "main")
    with open(src, "w", encoding="utf-8") as f:
        f.write(code)
    comp = subprocess.run(
        [GPP_CMD, src, "-o", out_bin],
        capture_output=True, text=True, timeout=30, encoding="utf-8"
    )
    if comp.returncode != 0:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return f"❌ خطأ في الترجمة:\n{comp.stderr[:800]}"
    run = subprocess.run(
        [out_bin], capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace"
    )
    shutil.rmtree(tmpdir, ignore_errors=True)
    return (run.stdout or run.stderr or "✅ تنفيذ ناجح بدون خرج")[:2000]


# ─── Bash ────────────────────────────────────────────────────
async def _run_bash(code: str) -> str:
    r = subprocess.run(
        ["bash", "-c", code],
        capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace"
    )
    return (r.stdout or r.stderr or "✅ تنفيذ ناجح بدون خرج")[:2000]
