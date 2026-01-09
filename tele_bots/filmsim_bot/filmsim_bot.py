#!/usr/bin/env python3
import os, uuid, math, subprocess, threading, queue, time, sys
from pathlib import Path

import telebot
from telebot import types

# ---- preinit sys.path  DO NOT REMOVE! ----
# Get the user's home directory
home_dir = os.path.expanduser("~")
if home_dir not in sys.path:
    sys.path.insert(0, home_dir)

# --------- CONFIG ----------
try:
    from _secrets import filmsimbottoken
except ImportError:
    from _secrets import filmsimbottoken


TOKEN = filmsimbottoken
if not TOKEN:
    raise RuntimeError("filmsimbottoken missing")

LUT_DIR = os.environ.get("FILMSIM_LUT_DIR", "/home/holly/luts")
LUT_DIR = os.path.abspath(LUT_DIR)

BASE = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE, "work")           # <— tidy
SCRIPT = os.path.join(BASE, "apply_lut.sh")

os.makedirs(WORK_DIR, exist_ok=True)

if not os.path.isfile(SCRIPT):
    raise RuntimeError(f"apply_lut.sh not found at {SCRIPT}")

PAGE_SIZE = 12
INTENSITIES = [0.25, 0.50, 0.75, 1.00]
CATEGORY_ALL = "All"
CATEGORY_UNCATEGORIZED = "Uncategorized"

# Limit concurrency: 1 worker is safest on an RPi/server.
WORKERS = int(os.environ.get("FILMSIM_WORKERS", "1"))

# database
from filmsim_db import FilmSimDB
DB_PATH = os.path.join(BASE, "filmsim.db")
db = FilmSimDB(DB_PATH)

FREE_DAILY_LIMIT = 5 #limits for non-premium users
PREMIUM_PLANS = {
    "premium_30d": {
        "title": "FilmSim Premium (30 days)",
        "description": "Unlimited exports for 30 days.",
        "days": 30,
        "stars": 199,
    }
}

# Cleanup policy:
# If True, delete the input image after each processing (tidy, but user can't re-apply different LUT without re-uploading).
# If False, keep last input per user so they can try multiple LUTs quickly.
DELETE_INPUT_AFTER_PROCESS = os.environ.get("FILMSIM_DELETE_INPUT", "0") == "1"

bot = telebot.TeleBot(TOKEN)

# per-user state
STATE = {}
# per-user lock to prevent stacking jobs
USER_BUSY = set()

# job queue
Job = dict
JOB_Q: "queue.Queue[Job]" = queue.Queue(maxsize=200)


def user_dir(user_id: int) -> str:
    p = os.path.join(WORK_DIR, str(user_id))
    os.makedirs(p, exist_ok=True)
    return p


def list_luts():
    out = []
    for root, _, files in os.walk(LUT_DIR):
        for f in files:
            if f.lower().endswith(".cube"):
                rel = os.path.relpath(os.path.join(root, f), LUT_DIR).replace("\\", "/")
                out.append(rel)
    return sorted(out)


def list_categories():
    cats = set()
    for rel in list_luts():
        if "/" in rel:
            cats.add(rel.split("/", 1)[0])
        else:
            cats.add(CATEGORY_UNCATEGORIZED)
    out = [CATEGORY_ALL] + sorted(cats)
    return out


def list_luts_by_category(category: str):
    all_luts = list_luts()
    if category == CATEGORY_ALL:
        return all_luts
    if category == CATEGORY_UNCATEGORIZED:
        return [rel for rel in all_luts if "/" not in rel]
    prefix = category.rstrip("/") + "/"
    return [rel for rel in all_luts if rel.startswith(prefix)]


def safe_lut_abs(rel):
    rel = (rel or "").replace("\\", "/")
    abs_path = os.path.abspath(os.path.join(LUT_DIR, rel))
    if not abs_path.startswith(LUT_DIR + os.sep):
        raise ValueError("Invalid LUT path")
    if not os.path.isfile(abs_path):
        raise FileNotFoundError("LUT not found")
    return abs_path


def kb_luts(luts, page, show_back=False):
    total = len(luts)
    pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(0, min(page, pages - 1))

    kb = types.InlineKeyboardMarkup(row_width=1)
    start = page * PAGE_SIZE
    end = min(total, start + PAGE_SIZE)

    for rel in luts[start:end]:
        display = rel[:-5] if rel.lower().endswith(".cube") else rel #strip extension, looks nasty in menu
        label = display if len(display) <= 44 else ("…" + display[-43:])
        kb.add(types.InlineKeyboardButton(label, callback_data=f"lut|{page}|{rel}"))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅ Prev", callback_data=f"page|{page-1}"))
    nav.append(types.InlineKeyboardButton(f"Page {page+1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(types.InlineKeyboardButton("Next ➡", callback_data=f"page|{page+1}"))
    kb.row(*nav)
    if show_back:
        kb.row(types.InlineKeyboardButton("⬅ Categories", callback_data="cats|0"))
    return kb


def kb_categories(cats, page):
    total = len(cats)
    pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(0, min(page, pages - 1))

    kb = types.InlineKeyboardMarkup(row_width=1)
    start = page * PAGE_SIZE
    end = min(total, start + PAGE_SIZE)

    for cat in cats[start:end]:
        label = cat if len(cat) <= 44 else ("…" + cat[-43:])
        kb.add(types.InlineKeyboardButton(label, callback_data=f"cat|{page}|{cat}"))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅ Prev", callback_data=f"catpage|{page-1}"))
    nav.append(types.InlineKeyboardButton(f"Page {page+1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(types.InlineKeyboardButton("Next ➡", callback_data=f"catpage|{page+1}"))
    kb.row(*nav)
    return kb


def kb_intensity():
    kb = types.InlineKeyboardMarkup(row_width=4)
    btns = [types.InlineKeyboardButton(f"{v:.2f}", callback_data=f"int|{v:.2f}") for v in INTENSITIES]
    kb.add(*btns)
    return kb


def cleanup_user_outputs(uid: int):
    """Keep the folder tidy: remove stale outputs, temp files."""
    d = user_dir(uid)
    for name in ("out.jpg", "out.jpeg", "out.png", "tmp.jpg", "tmp.png"):
        p = os.path.join(d, name)
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


def worker_loop(n: int):
    while True:
        job = JOB_Q.get()
        if job is None:
            JOB_Q.task_done()
            return

        user_id = job["user_id"]
        chat_id = job["chat_id"]
        msg_id = job["status_msg_id"]
        in_path = job["in_path"]
        lut_rel = job["lut_rel"]
        intensity = job["intensity"]
        out_path = os.path.join(user_dir(user_id), "out.jpg")

        try:
            cleanup_user_outputs(user_id)

            lut_path = safe_lut_abs(lut_rel)

            subprocess.run(
                [SCRIPT, in_path, lut_path, out_path, str(intensity)],
                check=True,
                timeout=120,
            )

            lut_name = lut_rel[:-5] if lut_rel.lower().endswith(".cube") else lut_rel
            caption = f"{lut_name} recipie @ {float(intensity):.2f}"
            with open(out_path, "rb") as f:
                bot.send_photo(chat_id, f, caption=caption)
            
            # ---- COUNT A SUCCESSFUL EXPORT (ADD THIS) ----
            db.increment_usage(user_id)

            bot.edit_message_text("Done ✅", chat_id, msg_id)

        except subprocess.TimeoutExpired:
            bot.edit_message_text("Error: processing timed out.", chat_id, msg_id)
        except subprocess.CalledProcessError as e:
            bot.edit_message_text(f"Error: processing failed ({e.returncode}).", chat_id, msg_id)
        except Exception as e:
            bot.edit_message_text(f"Error: {e}", chat_id, msg_id)
        finally:
            # tidy: always remove output
            try:
                if os.path.exists(out_path):
                    os.remove(out_path)
            except Exception:
                pass

            # optional: remove input after processing
            if DELETE_INPUT_AFTER_PROCESS:
                try:
                    if os.path.exists(in_path):
                        os.remove(in_path)
                except Exception:
                    pass

            USER_BUSY.discard(user_id)
            JOB_Q.task_done()


# start workers
for i in range(WORKERS):
    t = threading.Thread(target=worker_loop, args=(i,), daemon=True)
    t.start()


@bot.message_handler(commands=["start", "help"])
def start(m):
    bot.reply_to(
        m,
        "Send me a photo, then choose a recipe.\n\n"
        "Commands:\n"
        "/recipes  (browse film look recipes)\n"
        "/clear (forget current photo)\n"
        "/usage (your current usage for today)\n"
    )


@bot.message_handler(commands=["clear"])
def clear(m):
    uid = m.from_user.id
    STATE.pop(uid, None)
    USER_BUSY.discard(uid)
    # tidy user folder but keep LUTs external
    d = user_dir(uid)
    for fn in ("in.jpg", "in.png", "in.jpeg"):
        try:
            p = os.path.join(d, fn)
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    bot.reply_to(m, "Cleared your current selection.")


@bot.message_handler(commands=["usage"])
def usage(m):
    uid = m.from_user.id
    used = db.get_usage_today(uid)
    if db.is_premium(uid):
        bot.reply_to(m, f"⭐ Premium: unlimited exports.\nToday: {used} exports.")
    else:
        bot.reply_to(m, f"Free exports today: {used}/{FREE_DAILY_LIMIT}\nUpgrade: /premium")


@bot.message_handler(commands=["premium"])
def premium(m):
    plan = PREMIUM_PLANS["premium_30d"]

    prices = [types.LabeledPrice(label=plan["title"], amount=int(plan["stars"]))]

    bot.send_invoice(
        m.chat.id,
        title=plan["title"],
        description=plan["description"],
        invoice_payload="premium_30d",
        provider_token="",          # <-- Stars: MUST be empty
        currency="XTR",             # <-- Stars currency
        prices=prices,
    )



@bot.pre_checkout_query_handler(func=lambda q: True)
def pre_checkout(q):
    if q.invoice_payload not in PREMIUM_PLANS:
        bot.answer_pre_checkout_query(q.id, ok=False, error_message="Unknown plan.")
        return
    bot.answer_pre_checkout_query(q.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def on_successful_payment(m):
    payload = m.successful_payment.invoice_payload
    plan = PREMIUM_PLANS.get(payload)
    if not plan:
        bot.send_message(m.chat.id, "Payment received, but the plan is unknown.")
        return
    new_until = db.grant_premium_days(m.from_user.id, plan["days"])
    bot.send_message(
        m.chat.id,
        f"Premium active until {new_until.strftime('%Y-%m-%d')} ✅",
    )

@bot.message_handler(commands=["recipes"])
def recipes(m):
    uid = m.from_user.id
    st = STATE.setdefault(uid, {})
    st["cats"] = list_categories()
    st["cat"] = CATEGORY_ALL
    st["cat_page"] = 0
    bot.send_message(m.chat.id, "Pick a category:", reply_markup=kb_categories(st["cats"], 0))


@bot.message_handler(content_types=["photo"])
def photo(m):
    uid = m.from_user.id

    # largest version
    p = m.photo[-1]
    info = bot.get_file(p.file_id)
    data = bot.download_file(info.file_path)

    # keep tidy: overwrite user input
    d = user_dir(uid)
    in_path = os.path.join(d, "in.jpg")
    with open(in_path, "wb") as f:
        f.write(data)

    l = list_luts()
    STATE[uid] = {
        "in_path": in_path,
        "cats": list_categories(),
        "cat": CATEGORY_ALL,
        "cat_page": 0,
        "luts": l,
        "page": 0,
        "lut_rel": None,
    }

    bot.send_message(m.chat.id, "Photo received. Pick a category:", reply_markup=kb_categories(STATE[uid]["cats"], 0))


@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.from_user.id
    data = c.data or ""

    if data == "noop":
        bot.answer_callback_query(c.id)
        return

    st = STATE.get(uid)
    if not st:
        bot.answer_callback_query(c.id, "Send a photo first.")
        return

    if data.startswith("page|"):
        page = int(data.split("|", 1)[1])
        st["page"] = page
        bot.edit_message_reply_markup(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=kb_luts(st.get("luts", []), page, show_back=True),
        )
        bot.answer_callback_query(c.id)
        return

    if data.startswith("catpage|"):
        page = int(data.split("|", 1)[1])
        st["cat_page"] = page
        bot.edit_message_reply_markup(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=kb_categories(st.get("cats", []), page),
        )
        bot.answer_callback_query(c.id)
        return

    if data.startswith("cats|"):
        st["cat_page"] = int(data.split("|", 1)[1])
        bot.edit_message_text(
            "Pick a category:",
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=kb_categories(st.get("cats", []), st["cat_page"]),
        )
        bot.answer_callback_query(c.id)
        return

    if data.startswith("cat|"):
        _, page_str, cat = data.split("|", 2)
        st["cat_page"] = int(page_str)
        st["cat"] = cat
        st["page"] = 0
        st["luts"] = list_luts_by_category(cat)
        bot.edit_message_text(
            "Pick a filter:",
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=kb_luts(st.get("luts", []), 0, show_back=True),
        )
        bot.answer_callback_query(c.id, "Selected")
        return

    if data.startswith("lut|"):
        _, page_str, rel = data.split("|", 2)
        st["page"] = int(page_str)
        st["lut_rel"] = rel
        bot.answer_callback_query(c.id, "Selected")
        rel_display = rel[:-5] if rel.lower().endswith(".cube") else rel
        bot.send_message(c.message.chat.id, f"Selected filter:\n{rel_display}\n\nPick intensity:", reply_markup=kb_intensity())
        return

    if data.startswith("int|"):
        # ---- DAILY LIMIT CHECK (ADD THIS) ----
        allowed, used, limit = db.can_process(uid, FREE_DAILY_LIMIT)
        if not allowed:
            bot.answer_callback_query(c.id, f"Daily limit reached ({used}/{limit}).")
            bot.send_message(
                c.message.chat.id,
                "You’ve hit today’s free limit (5).\n"
                "Upgrade to Premium for unlimited. (/premium)"
            )
            return
        # ---- END DAILY LIMIT CHECK ----

        # prevent a single user stacking jobs
        if uid in USER_BUSY:
            bot.answer_callback_query(c.id, "Still processing your last request…")
            return

        intensity = data.split("|", 1)[1]
        lut_rel = st.get("lut_rel")
        in_path = st.get("in_path")
        if not lut_rel:
            bot.answer_callback_query(c.id, "Pick a recipie first.")
            return
        if not in_path or not os.path.isfile(in_path):
            bot.answer_callback_query(c.id, "Send a photo again.")
            return

        USER_BUSY.add(uid)

        # enqueue job
        try:
            status = bot.send_message(c.message.chat.id, "Queued…")
            JOB_Q.put_nowait({
                "user_id": uid,
                "chat_id": c.message.chat.id,
                "status_msg_id": status.message_id,
                "in_path": in_path,
                "lut_rel": lut_rel,
                "intensity": intensity,
            })
            bot.answer_callback_query(c.id, "Queued")
        except queue.Full:
            USER_BUSY.discard(uid)
            bot.answer_callback_query(c.id, "Busy right now — try again in a minute.")
            bot.send_message(c.message.chat.id, "Server is busy. Try again shortly.")
        return

    bot.answer_callback_query(c.id, "Unknown action.")


if __name__ == "__main__":
    print("filmsim_bot running…")
    print("LUT_DIR:", LUT_DIR)
    print("WORKERS:", WORKERS, "DELETE_INPUT_AFTER_PROCESS:", DELETE_INPUT_AFTER_PROCESS)
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
