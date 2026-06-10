# 📰 AI-NewsPaper Bot

> A smart Telegram bot delivering instant and scheduled news. Built using Python, LangChain, Groq, LLaMA-3.3, and the Tavily API via an autonomous Agentic AI architecture.

---

## ✨ Features

* 🚀 **Instant News:** Send any topic to the bot, and it instantly searches the web, reads multiple sources, and synthesizes a concise, formatted news report.
* ⏰ **Daily Briefings:** Subscribe to a custom topic using `/setdaily <topic>`. The bot acts as your personal news desk, delivering a fresh morning paper automatically every day at 8:00 AM.
* 🧠 **Agentic AI Architecture:** Uses advanced LLM orchestration to determine search queries, fetch real-time data, and format it natively for Telegram.
* ⚡ **Blazing Fast:** Powered by Groq's lightning-fast inference engine running the Llama 3.3 70B model.

---

## 🛠️ Technology Stack

* **Language:** Python 3.12+
* **AI Framework:** LangChain 🦜🔗
* **LLM Engine:** Groq API (`llama-3.3-70b-versatile`)
* **Search Engine:** Tavily Search API
* **Interface:** `python-telegram-bot`
* **Package Manager:** `uv`
* **Deployment:** JustRunMy.App

---

## 🚀 Getting Started

### 1. Prerequisites
You will need API keys from the following services (all offer free tiers):
* [Telegram BotFather](https://core.telegram.org/bots) (Bot Token)
* [Groq Cloud](https://console.groq.com/) (API Key)
* [Tavily](https://tavily.com/) (Search API Key)
* [uv](https://github.com/astral-sh/uv) (Extremely fast Python package installer)

### 2. Installation
Clone the repository and navigate to the project directory:
```bash
git clone [https://github.com/up65akhil/PulseBot-AI.git](https://github.com/up65akhil/PulseBot-AI.git)
cd PulseBot-AI
uv pip install -r requirements.txt
