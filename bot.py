import logging
import os
import json
from datetime import datetime, time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# LangChain & AI Imports
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
search_tool = TavilySearch(max_results=5, search_depth="advanced", topic="news")

SYSTEM_PROMPT = """You are the Chief Editor of 'THE TELEGRAM DAILY'. 
Format your output strictly using HTML tags supported by Telegram: 
<b>📰 THE [TOPIC] GAZETTE</b>
\n<b>🚨 BREAKING: [Headline]</b>\n[Summary]
\n<b>🌐 TOP STORIES:</b>\n• <b>[Title]</b>: [Summary] (<a href='[URL]'>Source</a>)
\n---
<b>🖋️ EDITORIAL:</b> [Witty 2-sentence summary]
"""

agent = create_agent(model=llm, tools=[search_tool], system_prompt=SYSTEM_PROMPT)

DATA_FILE = "users.json"

def get_all_subscribers() -> dict:
    if not os.path.exists(DATA_FILE): 
        return {}
    with open(DATA_FILE, 'r') as f: 
        return json.load(f)

def update_user(user_id: int, topic: str = None, delivery_time: str = None):
    data = get_all_subscribers()
    uid = str(user_id)
    
    if uid not in data or isinstance(data[uid], str):
        legacy_topic = data[uid] if uid in data else "Technology"
        data[uid] = {"topic": legacy_topic, "time": "08:00"}
        
    if topic:
        data[uid]["topic"] = topic
    if delivery_time:
        data[uid]["time"] = delivery_time
        
    with open(DATA_FILE, 'w') as f: 
        json.dump(data, f, indent=4)

def schedule_user_job(job_queue, chat_id: int, time_str: str):
    """Removes old schedules for the user and creates a new one."""
    current_jobs = job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
        
    try:
        hour, minute = map(int, time_str.split(':'))
        target_time = time(hour=hour, minute=minute)
        job_queue.run_daily(send_daily_news, target_time, chat_id=chat_id, name=str(chat_id))
        logging.info(f"Scheduled news for {chat_id} at {time_str}")
    except ValueError:
        logging.error(f"Invalid time format for {chat_id}: {time_str}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "👋 <b>Welcome to your AI News Desk!</b>\n\n"
        "1️⃣ <b>Instant News:</b> Type any topic (e.g., 'Tesla') for live news right now.\n"
        "2️⃣ <b>Daily Topic:</b> Type <code>/setdaily [topic]</code>\n"
        "3️⃣ <b>Daily Time:</b> Type <code>/settime HH:MM</code> (24-hour format)\n\n"
        "<i>Example: /settime 08:30</i>"
    )
    await update.message.reply_text(welcome_msg, parse_mode="HTML")

async def set_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a topic! Example: <code>/setdaily AI</code>", parse_mode="HTML")
        return
        
    topic = " ".join(context.args)
    user_id = update.message.chat_id
    
    update_user(user_id, topic=topic)
    time_str = get_all_subscribers()[str(user_id)]["time"]
    schedule_user_job(context.job_queue, user_id, time_str)
    
    await update.message.reply_text(f"✅ <b>Topic Updated!</b>\nI will send you news on <b>{topic}</b> daily at {time_str}.", parse_mode="HTML")

async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a time in 24-hour format! Example: <code>/settime 09:00</code>", parse_mode="HTML")
        return
        
    time_str = context.args[0]
    user_id = update.message.chat_id
    
    try:
        hour, minute = map(int, time_str.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError()
    except ValueError:
        await update.message.reply_text("❌ Invalid format. Please use HH:MM (e.g., 14:30 or 08:00).", parse_mode="HTML")
        return

    update_user(user_id, delivery_time=time_str)
    schedule_user_job(context.job_queue, user_id, time_str)
    
    topic = get_all_subscribers()[str(user_id)]["topic"]
    await update.message.reply_text(f"⏰ <b>Time Updated!</b>\nI will now send your <b>{topic}</b> paper at <b>{time_str}</b>.", parse_mode="HTML")

async def handle_instant_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text
    today = datetime.now().strftime('%B %d, %Y')
    
    status_msg = await update.message.reply_text(f"🔍 <i>Writing your paper on <b>{topic}</b>...</i>", parse_mode="HTML")
    
    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Find the absolute latest news on {topic} for {today} and format it as the newspaper.")]
        })
        news_content = result["messages"][-1].content
        await status_msg.edit_text(text=news_content, parse_mode="HTML", disable_web_page_preview=False)
    except Exception as e:
        logging.error(f"Error fetching instant news: {e}")
        await status_msg.edit_text("❌ Sorry, I encountered an error. Please try again.")

async def send_daily_news(context: ContextTypes.DEFAULT_TYPE):
    """Triggered by the alarm schedule."""
    chat_id = context.job.chat_id
    user_data = get_all_subscribers().get(str(chat_id))
    
    if not user_data:
        return
        
    topic = user_data["topic"]
    today = datetime.now().strftime('%B %d, %Y')
    
    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Find the absolute latest news on {topic} for {today} and format it as the newspaper.")]
        })
        news_content = result["messages"][-1].content
        await context.bot.send_message(chat_id=chat_id, text=news_content, parse_mode="HTML", disable_web_page_preview=False)
    except Exception as e:
        logging.error(f"Failed to send daily news to {chat_id}: {e}")

# --- MAIN EXECUTION ---

if __name__ == '__main__':
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token or token == "your-telegram-token-from-botfather":
        print("❌ ERROR: Please add your TELEGRAM_BOT_TOKEN to .env!")
        exit(1)

    app = ApplicationBuilder().token(token).build()
    
    subscribers = get_all_subscribers()
    for chat_id_str, data in subscribers.items():
        if isinstance(data, str):
            print(f"🛠️ Upgrading database format for user {chat_id_str}...")
            update_user(int(chat_id_str), topic=data) 
            data = {"topic": data, "time": "08:00"}
            
        time_str = data.get("time", "08:00")
        schedule_user_job(app.job_queue, int(chat_id_str), time_str)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setdaily", set_daily))
    app.add_handler(CommandHandler("settime", set_time))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_instant_news))

    print("✅ System Online! Telegram Bot is running...")
    app.run_polling()
    