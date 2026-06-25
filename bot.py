import os
import logging
import re
import csv
from datetime import datetime, timedelta, time
from functools import wraps
from tzlocal import get_localzone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from dotenv import load_dotenv
import database

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_USER_ID_RAW = os.getenv("AUTHORIZED_USER_ID")

if not TOKEN or TOKEN == "your_bot_token_here":
    raise ValueError("TELEGRAM_BOT_TOKEN tidak boleh kosong. Harap atur di file .env")
if not AUTHORIZED_USER_ID_RAW or AUTHORIZED_USER_ID_RAW == "123456789":
    raise ValueError("AUTHORIZED_USER_ID tidak boleh kosong atau menggunakan default. Harap atur di file .env")

try:
    AUTHORIZED_USER_ID = int(AUTHORIZED_USER_ID_RAW)
except ValueError:
    raise ValueError("AUTHORIZED_USER_ID harus berupa angka integer valid")

# Set timezone local
LOCAL_TZ = get_localzone()

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Decorator to restrict access to authorized user only
def authorized_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user or user.id != AUTHORIZED_USER_ID:
            logger.warning(
                f"Akses tidak sah dicoba oleh user ID: {user.id if user else 'Unknown'} "
                f"username: {user.username if user else 'Unknown'}"
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

# Decorator to restrict callback query access
def authorized_callback_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user or user.id != AUTHORIZED_USER_ID:
            logger.warning(f"Akses callback query tidak sah dicoba oleh user ID: {user.id if user else 'Unknown'}")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


@authorized_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message and lists available commands."""
    welcome_text = (
        "👋 **Halo! Selamat datang di Bot Timesheet & Pengingat.**\n\n"
        "Bot ini berjalan sangat ringan untuk mencatat aktivitas harian Anda.\n\n"
        "📝 **Mulai Mencatat:**\n"
        "Gunakan perintah `/isi` dengan pemisah koma:\n"
        "`/isi [Project], [Durasi], [Deskripsi]`\n"
        "_Contoh: `/isi Project A, 3.5, Coding API login`_\n\n"
        "📊 **Laporan:**\n"
        "Gunakan `/laporan` untuk memilih periode secara interaktif, atau ketik manual:\n"
        "- `/laporan 25-06-2026`\n"
        "- `/laporan 01-06-2026 s/d 15-06-2026`\n\n"
        "⚙️ **Pengingat Harian (Senin - Jumat):**\n"
        "- `/status` : Cek status & jam pengingat saat ini.\n"
        "- `/set_pengingat [HH:MM]` : Mengubah jam pengingat (contoh: `/set_pengingat 17:30`).\n"
        "- `/pengingat_on` : Mengaktifkan pengingat.\n"
        "- `/pengingat_off` : Menonaktifkan pengingat.\n\n"
        "Ketik `/help` jika butuh bantuan lebih lanjut."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


@authorized_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays detailed help info."""
    help_text = (
        "ℹ️ **Panduan Penggunaan Bot Timesheet**\n\n"
        "🛠️ **Pencatatan Timesheet**\n"
        "Format penulisan:\n"
        "`/isi [Nama Project], [Durasi Jam], [Deskripsi Pekerjaan]`\n\n"
        "⚠️ *Penting:* Harus dipisahkan menggunakan tanda koma ( `,` ).\n\n"
        "*Contoh Input:* \n"
        "• `/isi Project Antigravity, 2.5, Setup project dan konfigurasi .env`\n"
        "• `/isi R&D Web, 4, Diskusi tim terkait arsitektur`\n"
        "• `/isi Support Ops, 1.5, Membantu testing deploy`\n\n"
        "📊 **Mendapatkan Laporan (Report)**\n"
        "1. Ketik `/laporan` untuk menampilkan pilihan periode instan (Hari Ini, Kemarin, Minggu Ini, Bulan Ini).\n"
        "2. Masukkan tanggal spesifik: `/laporan 25-06-2026`\n"
        "3. Masukkan rentang tanggal: `/laporan 01-06-2026 s/d 15-06-2026`\n\n"
        "Bot akan merespon dengan ringkasan teks dan mengirimkan file `.csv` yang dapat langsung diimpor ke Excel/Spreadsheet.\n\n"
        "⏰ **Pengaturan Pengingat Harian**\n"
        "Bot akan otomatis mengingatkan Anda pada hari kerja (Senin - Jumat).\n"
        "- `/status` : Melihat konfigurasi jam & status aktif pengingat.\n"
        "- `/set_pengingat 17:15` : Mengatur agar diingatkan pada pukul 17:15.\n"
        "- `/pengingat_on` : Mengaktifkan kembali pengingat.\n"
        "- `/pengingat_off` : Mematikan pengingat harian."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


@authorized_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays current settings for reminder."""
    try:
        settings = database.get_settings(AUTHORIZED_USER_ID)
        status_enabled = "🟢 Aktif" if settings["reminder_enabled"] == 1 else "🔴 Nonaktif"
        
        status_text = (
            f"⚙️ **Status Bot & Pengingat Anda:**\n\n"
            f"👤 **User ID Anda:** `{AUTHORIZED_USER_ID}` (Terverifikasi)\n"
            f"🔔 **Pengingat Harian:** {status_enabled}\n"
            f"⏰ **Waktu Pengingat:** Pukul `{settings['reminder_time']}` (Senin - Jumat)\n\n"
            f"Gunakan `/set_pengingat [HH:MM]` untuk mengubah jam pengingat."
        )
        await update.message.reply_text(status_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error fetching status: {e}")
        await update.message.reply_text("❌ Gagal mengambil informasi status dari database.")


@authorized_only
async def isi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Logs a timesheet entry."""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "⚠️ **Format salah!** Gunakan:\n`/isi [Project], [Durasi], [Deskripsi]`\n\n"
            "Contoh: `/isi Project A, 3.5, Coding API login`",
            parse_mode="Markdown"
        )
        return

    # Split by comma
    parts = [p.strip() for p in text.split(",")]
    if len(parts) < 3:
        await update.message.reply_text(
            "⚠️ **Format kurang lengkap!** Pastikan Anda menggunakan pemisah koma ( `,` ) "
            "untuk memisahkan ketiga bagian.\n\n"
            "Format: `/isi [Project], [Durasi], [Deskripsi]`\n"
            "Contoh: `/isi Project A, 3, Rapat harian`",
            parse_mode="Markdown"
        )
        return

    project = parts[0]
    duration_str = parts[1]
    # Rejoin the description using comma just in case description has comma
    description = ", ".join(parts[2:])

    # Clean empty values
    if not project or not duration_str or not description:
        await update.message.reply_text("⚠️ Project, Durasi, dan Deskripsi tidak boleh kosong.")
        return

    # Validate duration is float
    try:
        duration = float(duration_str)
        if duration <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ **Durasi harus berupa angka positif!**\n"
            "Contoh: `3` atau `2.5` (gunakan titik untuk pecahan).",
            parse_mode="Markdown"
        )
        return

    # Store entry with today's date
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    try:
        database.add_timesheet(project, duration, description, today_str)
        await update.message.reply_text(
            f"✅ **Timesheet Berhasil Dicatat!**\n\n"
            f"📁 **Project:** {project}\n"
            f"⏱️ **Durasi:** {duration} jam\n"
            f"📝 **Deskripsi:** {description}\n"
            f"📅 **Tanggal:** {datetime.now().strftime('%d-%m-%Y')}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error adding timesheet: {e}")
        await update.message.reply_text("❌ Gagal menyimpan timesheet ke database.")


async def generate_and_send_report(
    chat_id: int, start_date_str: str, end_date_str: str, label: str, context: ContextTypes.DEFAULT_TYPE
):
    """Fetches timesheets for specified range, summarizes, and sends CSV."""
    entries = database.get_timesheets(start_date_str, end_date_str)
    
    if not entries:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📭 Tidak ada data timesheet untuk periode **{label}** ({start_date_str} s/d {end_date_str or start_date_str}).",
            parse_mode="Markdown"
        )
        return

    total_hours = 0.0
    project_totals = {}
    
    for entry in entries:
        duration = entry["duration"]
        project = entry["project"]
        total_hours += duration
        project_totals[project] = project_totals.get(project, 0.0) + duration

    # Helper to convert YYYY-MM-DD -> DD-MM-YYYY
    def format_date_display(d_str):
        try:
            return datetime.strptime(d_str, "%Y-%m-%d").strftime("%d-%m-%Y")
        except Exception:
            return d_str

    start_display = format_date_display(start_date_str)
    end_display = format_date_display(end_date_str) if end_date_str else start_display
    
    # Create Summary Text
    summary_text = (
        f"📊 **Laporan Timesheet: {label}**\n"
        f"📅 **Periode:** {start_display}" + (f" s/d {end_display}" if start_date_str != end_date_str else "") + "\n"
        f"⏱️ **Total Durasi:** {total_hours} jam\n\n"
    )
    
    summary_text += "**Rangkuman per Project:**\n"
    for proj, hours in project_totals.items():
        summary_text += f"- *{proj}*: {hours} jam\n"
    
    summary_text += "\n**Detail Catatan:**\n"
    for i, entry in enumerate(entries, 1):
        date_disp = format_date_display(entry["date"])
        summary_text += f"{i}. {date_disp} | *{entry['project']}* | {entry['duration']} jam\n   └ {entry['description']}\n"

    # Truncate summary if too long for Telegram (4096 char limit)
    if len(summary_text) > 4000:
        summary_text = summary_text[:3900] + "\n\n*(Laporan terlalu panjang, detail selengkapnya ada di file CSV di bawah...)*"
        
    await context.bot.send_message(
        chat_id=chat_id,
        text=summary_text,
        parse_mode="Markdown"
    )

    # Generate CSV file
    filename = f"timesheet_report_{start_date_str.replace('-', '')}"
    if end_date_str and end_date_str != start_date_str:
        filename += f"_{end_date_str.replace('-', '')}"
    filename += ".csv"
    
    file_path = os.path.join(os.getcwd(), filename)
    
    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Tanggal", "Project", "Durasi (Jam)", "Deskripsi", "Waktu Input"])
            for entry in entries:
                writer.writerow([
                    entry["date"],
                    entry["project"],
                    entry["duration"],
                    entry["description"],
                    entry["created_at"]
                ])
                
        # Send Document
        with open(file_path, "rb") as f:
            await context.bot.send_document(
                chat_id=chat_id,
                document=f,
                filename=filename,
                caption=f"📄 File CSV untuk laporan periode {label}."
            )
    except Exception as e:
        logger.error(f"Error creating/sending CSV file: {e}")
        await context.bot.send_message(chat_id=chat_id, text="❌ Terjadi kesalahan saat membuat/mengirim file CSV laporan.")
    finally:
        # Clean up file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Failed to delete temp CSV: {e}")


async def handle_manual_laporan(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Parses manual date entry and generates report."""
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Try match DD-MM-YYYY s/d DD-MM-YYYY
    range_match = re.match(r'^(\d{2}-\d{2}-\d{4})\s*(?:s/d|sd|sampai|-)\s*(\d{2}-\d{2}-\d{4})$', text, re.IGNORECASE)
    # Try match DD-MM-YYYY
    single_match = re.match(r'^(\d{2}-\d{2}-\d{4})$', text)
    
    def convert_date(d_str):
        try:
            return datetime.strptime(d_str, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            return None

    chat_id = update.effective_chat.id

    if range_match:
        start_raw, end_raw = range_match.groups()
        start_date = convert_date(start_raw)
        end_date = convert_date(end_raw)
        if not start_date or not end_date:
            await update.message.reply_text("⚠️ Format tanggal salah! Gunakan format DD-MM-YYYY (Contoh: 01-06-2026).")
            return
        await generate_and_send_report(
            chat_id=chat_id,
            start_date_str=start_date,
            end_date_str=end_date,
            label=f"{start_raw} s/d {end_raw}",
            context=context
        )
    elif single_match:
        date_raw = single_match.group(1)
        date_str = convert_date(date_raw)
        if not date_str:
            await update.message.reply_text("⚠️ Format tanggal salah! Gunakan format DD-MM-YYYY (Contoh: 25-06-2026).")
            return
        await generate_and_send_report(
            chat_id=chat_id,
            start_date_str=date_str,
            end_date_str=date_str,
            label=date_raw,
            context=context
        )
    else:
        await update.message.reply_text(
            "⚠️ **Format perintah laporan manual salah!**\n\n"
            "Format yang didukung:\n"
            "• Tanggal tunggal: `/laporan 25-06-2026`\n"
            "• Rentang tanggal: `/laporan 01-06-2026 s/d 15-06-2026`"
        )


@authorized_only
async def laporan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends inline keyboard for date preset, or routes manual request."""
    text = " ".join(context.args) if context.args else ""
    if text:
        await handle_manual_laporan(update, context, text)
        return
        
    keyboard = [
        [
            InlineKeyboardButton("Hari Ini", callback_data="rep_today"),
            InlineKeyboardButton("Kemarin", callback_data="rep_yesterday"),
        ],
        [
            InlineKeyboardButton("Minggu Ini", callback_data="rep_this_week"),
            InlineKeyboardButton("Bulan Ini", callback_data="rep_this_month"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📋 Silakan pilih periode laporan:", reply_markup=reply_markup)


@authorized_callback_only
async def report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles report options chosen via inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    chat_id = update.effective_chat.id
    today = datetime.now()
    
    if data == "rep_today":
        start_date_str = today.strftime("%Y-%m-%d")
        end_date_str = start_date_str
        label = "Hari Ini"
    elif data == "rep_yesterday":
        yesterday = today - timedelta(days=1)
        start_date_str = yesterday.strftime("%Y-%m-%d")
        end_date_str = start_date_str
        label = "Kemarin"
    elif data == "rep_this_week":
        # Monday of current week
        start_week = today - timedelta(days=today.weekday())
        start_date_str = start_week.strftime("%Y-%m-%d")
        end_date_str = today.strftime("%Y-%m-%d")
        label = "Minggu Ini"
    elif data == "rep_this_month":
        # 1st day of current month
        start_month = today.replace(day=1)
        start_date_str = start_month.strftime("%Y-%m-%d")
        end_date_str = today.strftime("%Y-%m-%d")
        label = "Bulan Ini"
    else:
        return
        
    await generate_and_send_report(
        chat_id=chat_id,
        start_date_str=start_date_str,
        end_date_str=end_date_str,
        label=label,
        context=context
    )


async def send_reminder_job(context: ContextTypes.DEFAULT_TYPE):
    """The task run by JobQueue to send reminder."""
    chat_id = context.job.chat_id
    reminder_text = (
        "⏰ **Pengingat Timesheet Harian**\n\n"
        "Halo! Jangan lupa untuk mencatat timesheet Anda hari ini.\n\n"
        "Gunakan format:\n"
        "`/isi [Project], [Durasi], [Deskripsi]`\n"
        "_Contoh: `/isi Project A, 3.5, Rapat harian`_"
    )
    try:
        await context.bot.send_message(chat_id=chat_id, text=reminder_text, parse_mode="Markdown")
        logger.info(f"Reminder sent successfully to user {chat_id}")
    except Exception as e:
        logger.error(f"Failed to send reminder to user {chat_id}: {e}")


def reschedule_reminder(application: Application):
    """Reschedules the daily reminder job from database configuration."""
    # Cancel current jobs first
    cancel_reminder_job(application)
    
    settings = database.get_settings(AUTHORIZED_USER_ID)
    if settings["reminder_enabled"] != 1:
        logger.info("Reminder is disabled in settings. Skipping reschedule.")
        return
        
    time_str = settings["reminder_time"]
    try:
        hour, minute = map(int, time_str.split(":"))
    except ValueError:
        logger.error(f"Invalid reminder time format in database: {time_str}. Defaulting to 17:00")
        hour, minute = 17, 0
        
    # Create timezone-aware time object using LOCAL_TZ
    job_time = time(hour=hour, minute=minute, tzinfo=LOCAL_TZ)
    
    application.job_queue.run_daily(
        send_reminder_job,
        time=job_time,
        days=(1, 2, 3, 4, 5),  # 1-5 represents Monday to Friday in JobQueue
        name="daily_reminder_job",
        chat_id=AUTHORIZED_USER_ID
    )
    logger.info(f"Scheduled daily reminder job at {time_str} LOCAL_TZ (Monday-Friday)")


def cancel_reminder_job(application: Application):
    """Cancels any active daily reminder jobs."""
    current_jobs = application.job_queue.get_jobs_by_name("daily_reminder_job")
    for job in current_jobs:
        job.schedule_removal()
    logger.info("Cancelled all daily_reminder_job instances.")


@authorized_only
async def set_pengingat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Changes daily reminder time."""
    text = "".join(context.args).strip() if context.args else ""
    if not text:
        await update.message.reply_text(
            "⚠️ **Format salah!** Gunakan:\n`/set_pengingat [HH:MM]`\n\n"
            "Contoh: `/set_pengingat 17:30`",
            parse_mode="Markdown"
        )
        return
        
    match = re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", text)
    if not match:
        await update.message.reply_text(
            "⚠️ **Format jam tidak valid!** Gunakan format 24-jam `HH:MM`.\n"
            "Contoh: `17:00` atau `09:15`."
        )
        return
        
    hours, minutes = match.groups()
    formatted_time = f"{int(hours):02d}:{int(minutes):02d}"
    
    try:
        database.update_settings(AUTHORIZED_USER_ID, reminder_time=formatted_time)
        reschedule_reminder(context.application)
        
        await update.message.reply_text(
            f"✅ **Waktu pengingat berhasil diubah!**\n"
            f"⏰ Bot akan mengingatkan Anda setiap Senin - Jumat pada pukul `{formatted_time}`.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error updating reminder time: {e}")
        await update.message.reply_text("❌ Gagal menyimpan pengaturan baru ke database.")


@authorized_only
async def pengingat_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enables reminder."""
    try:
        database.update_settings(AUTHORIZED_USER_ID, reminder_enabled=1)
        reschedule_reminder(context.application)
        
        await update.message.reply_text(
            "🔔 **Pengingat harian telah diaktifkan!**\n"
            "Anda akan diingatkan untuk mengisi timesheet setiap hari kerja (Senin - Jumat).",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error enabling reminder: {e}")
        await update.message.reply_text("❌ Gagal mengaktifkan pengingat.")


@authorized_only
async def pengingat_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disables reminder."""
    try:
        database.update_settings(AUTHORIZED_USER_ID, reminder_enabled=0)
        cancel_reminder_job(context.application)
        
        await update.message.reply_text(
            "🔕 **Pengingat harian dinonaktifkan.**\n"
            "Bot tidak akan mengirimkan pengingat sampai diaktifkan kembali.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error disabling reminder: {e}")
        await update.message.reply_text("❌ Gagal menonaktifkan pengingat.")


async def post_init(application: Application) -> None:
    """Sets bot commands menu in Telegram."""
    commands = [
        BotCommand("start", "Memulai bot dan verifikasi"),
        BotCommand("help", "Menampilkan panduan lengkap"),
        BotCommand("status", "Cek status pengingat & User ID"),
        BotCommand("isi", "Pencatatan timesheet (Project, Durasi, Deskripsi)"),
        BotCommand("laporan", "Meminta laporan timesheet"),
        BotCommand("set_pengingat", "Atur jam pengingat harian (HH:MM)"),
        BotCommand("pengingat_on", "Mengaktifkan pengingat harian"),
        BotCommand("pengingat_off", "Menonaktifkan pengingat harian"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands menu registered successfully.")


def main():
    # 1. Initialize SQLite Database tables
    database.init_db()
    
    # 2. Build Application
    application = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # 3. Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("isi", isi_command))
    application.add_handler(CommandHandler("laporan", laporan_command))
    application.add_handler(CommandHandler("set_pengingat", set_pengingat_command))
    application.add_handler(CommandHandler("pengingat_on", pengingat_on_command))
    application.add_handler(CommandHandler("pengingat_off", pengingat_off_command))
    
    application.add_handler(CallbackQueryHandler(report_callback, pattern="^rep_"))
    
    # 4. Schedule daily reminder from configuration
    reschedule_reminder(application)
    
    # 5. Start Polling
    logger.info("Starting bot polling...")
    application.run_polling()


if __name__ == "__main__":
    main()
