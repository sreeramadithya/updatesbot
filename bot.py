from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import sqlite3
from datetime import datetime

# Initialize Database
conn = sqlite3.connect("progress.db", check_same_thread=False)
cursor = conn.cursor()

# Create the progress table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    subject TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    status TEXT NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# Subjects and chapters
subjects = {
    "maths": 12,
    "cs": 16,
    "physics": 11,
    "chemistry": 15,
    "english": 6
}

# /start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Welcome to the Progress Tracker Bot!\n"
        "Available commands:\n"
        "/update <subject> <chapter> <status> - Update progress\n"
        "/view <username> - View progress\n"
        "/delete - Delete all your progress\n"
        "/help - Show this message"
    )

# /update command
async def update_progress(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /update <subject> <chapter> <status>")
        return

    username = update.message.from_user.username or update.message.from_user.first_name
    subject = context.args[0].lower()
    try:
        chapter = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Chapter must be a number.")
        return
    status = " ".join(context.args[2:]).lower()

    if subject not in subjects:
        await update.message.reply_text(f"Invalid subject. Available subjects: {', '.join(subjects.keys())}")
        return

    if chapter < 1 or chapter > subjects[subject]:
        await update.message.reply_text(f"{subject.capitalize()} has only {subjects[subject]} chapters.")
        return

    if status not in ["not started", "in progress", "completed"]:
        await update.message.reply_text("Status must be 'not started', 'in progress', or 'completed'.")
        return

    now = datetime.now()
    cursor.execute("""
    INSERT INTO progress (username, subject, chapter, status, last_updated)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(username, subject, chapter)
    DO UPDATE SET status=?, last_updated=?
    """, (username, subject, chapter, status, now, status, now))
    conn.commit()

    await update.message.reply_text(f"Progress updated for {subject.capitalize()} Chapter {chapter}: {status}")

# /view command
async def view_progress(update: Update, context: CallbackContext) -> None:
    username = context.args[0].lower() if context.args else update.message.from_user.username

    cursor.execute("""
    SELECT subject, chapter, status, last_updated
    FROM progress
    WHERE username=?
    ORDER BY subject, chapter
    """, (username,))
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text(f"No progress found for {username}.")
        return

    message = f"Progress for {username}:\n"
    for subject, chapter, status, last_updated in rows:
        message += f"• {subject.capitalize()} Chapter {chapter}: {status} (Last updated: {last_updated})\n"

    await update.message.reply_text(message)

# /delete command
async def delete_progress(update: Update, context: CallbackContext) -> None:
    username = update.message.from_user.username or update.message.from_user.first_name

    cursor.execute("DELETE FROM progress WHERE username=?", (username,))
    conn.commit()

    await update.message.reply_text("All your progress has been deleted.")

# /help command
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Available commands:\n"
        "/update <subject> <chapter> <status> - Update progress\n"
        "/view <username> - View progress\n"
        "/delete - Delete all your progress\n"
        "/help - Show this message"
    )

# Main function
def main() -> None:
    application = Application.builder().token("7113366096:AAHy4-JsDg9IJCbDb5_sf3V1YsbRJ-_lU6I").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("update", update_progress))
    application.add_handler(CommandHandler("view", view_progress))
    application.add_handler(CommandHandler("delete", delete_progress))
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling()

if __name__ == "__main__":
    main()
