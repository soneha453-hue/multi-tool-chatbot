🤖 Multi-Tool Agentic Chatbot

An intelligent conversational AI chatbot built with LangGraph and Groq LLM, featuring memory-enabled conversations, multi-tool capabilities, and an interactive UI built with HTML/CSS/JS and FastAPI.

🔗 Live Demo: https://soneha453-hue.github.io/multi-tool-chatbot/

🔗 API: https://multi-tool-chatbot.onrender.com


✨ Features


🌤 Weather — Real-time weather data via OpenWeatherMap API
📈 Stock Prices — Live stock data via Finnhub API
🔍 Web Search — Internet search via Tavily API
🔢 Calculator — Mathematical expression evaluation
🧠 Memory — Persistent conversation history using SQLite checkpointer
💬 Multi-turn Conversations — Thread-based chat with full history
🗂 Sidebar — View, switch, and delete past conversations



🛠 Tech Stack

LayerTechnologyLLMGroq (qwen/qwen3-32b)Agent FrameworkLangGraph + LangChainBackendFastAPIMemorySQLite (LangGraph Checkpointer)FrontendHTML + CSS + JavaScriptSearchTavily APIWeatherOpenWeatherMap APIStocksFinnhub APIDeployment (Backend)RenderDeployment (Frontend)GitHub Pages


🚀 Getting Started (Local Setup)

1. Clone the repository

bashgit clone https://github.com/soneha453-hue/multi-tool-chatbot.git
cd multi-tool-chatbot

2. Install dependencies

bashpip install -r requirements.txt

3. Set up environment variables

Create a .env file in the root directory:

envGROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
FINNHUB_API_KEY=your_finnhub_api_key

4. Run the backend

bashuvicorn main:app --reload

5. Open the frontend

Open index.html in your browser — or just visit the Live Demo!


📁 Project Structure

multi-tool-chatbot/
├── main.py              # FastAPI backend
├── langgraph_bot.py     # LangGraph agent + tools
├── index.html           # Frontend UI
├── requirements.txt     # Python dependencies
└── .gitignore


📸 Architecture

User → HTML/JS Frontend
         ↓
    FastAPI Backend
         ↓
    LangGraph Agent
    ↙    ↓    ↘    ↘
Weather Stock Search Calculator
  API    API   API
         ↓
   SQLite Memory


🙋‍♀️ Author

Neha — MSc Mathematics & Computing, IIT (ISM) Dhanbad

GitHub: @soneha453-hue