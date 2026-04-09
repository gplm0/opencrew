# 🤖 Crew AI Agents 

A sophisticated personal AI assistant with engineering expertise (Waza Skills) powered by Qwen LLM.

## ✨ Features

- 🧠 **Intelligent Reasoning** - Powered by Qwen LLM (cloud or local)
- 🛠️ **8 Engineering Skills** - think, write, design, hunt, learn, read, check, health
- 💬 **Multiple Interfaces** - Web UI, CLI, REST API, WebSocket
- 💾 **Conversation Memory** - Persistent history with SQLite
- 🔐 **Authentication** - JWT-based security
- 🐳 **Docker Ready** - Easy deployment with containers
- ⚡ **Real-time** - WebSocket support for live communication

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              INTERFACES                          │
│  Web UI  │  CLI  │  REST API  │  WebSocket      │
└────────────────┬────────────────────────────────┘
                 │
         ┌───────▼────────┐
         │  FastAPI Server │
         │   (Your Code)   │
         └───────┬────────┘
                 │
      ┌──────────┼──────────┐
      │          │          │
   ┌──▼──┐   ┌──▼──┐   ┌──▼──┐
   │Waza │   │ Qwen│   │Tools│
   │Skills   │ LLM │   │     │
   └──────┘   │     │   │     │
      │   └──────┘   │
      │       │      │
    ┌─▼──┬──▼────┬──▼──┐
    │SQLite│DashScope│Ollama
    └──────┘         └─────┘
```

## 📦 Project Structure

```
jarvis/
├── src/
│   ├── brain/
│   │   ├── llm.py              # Qwen LLM interface
│   │   ├── waza_skills.py      # Waza skills integration
│   │   └── memory.py           # Conversation history
│   │
│   ├── api/
│   │   ├── server.py           # FastAPI backend
│   │   └── auth.py             # JWT authentication
│   │
│   ├── tools/
│   │   └── handlers.py         # Code, file, web search tools
│   │
│   ├── waza-skills/            # Skill instruction files
│   │   ├── think.md
│   │   ├── write.md
│   │   ├── design.md
│   │   ├── hunt.md
│   │   ├── learn.md
│   │   ├── read.md
│   │   ├── check.md
│   │   └── health.md
│   │
│   └── cli.py                  # CLI interface
│
├── config/
│   └── settings.py             # Application configuration
│
├── static/
│   └── index.html              # Web UI
│
├── requirements.txt
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Qwen API key (or Ollama for local)

### 1. Install Dependencies

```bash
# Using your existing .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
copy .env.example .env

# Edit .env and add your Qwen API key
# QWEN_API_KEY=sk-your-actual-key-here
```

**Get API Key:**
- Cloud: https://dashscope.aliyun.com
- Local: Install Ollama from https://ollama.ai

### 3. Run Jarvis

#### Option A: Web Server (Recommended)

```bash
.venv/Scripts/python.exe -m src.cli serve
```

Then open: http://localhost:3000

#### Option B: CLI Chat

```bash
.venv/Scripts/python.exe -m src.cli chat
```

#### Option C: Use a Skill Directly

```bash
.venv/Scripts/python.exe -m src.cli use-skill think "Should we use microservices or monolith?"
```

### 4. Test the API

```bash
# Health check
curl http://localhost:3000/health

# Query Jarvis
curl -X POST http://localhost:3000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"Explain how to design a scalable API\"}"

# Use a skill
curl -X POST http://localhost:3000/skill/think ^
  -H "Content-Type: application/json" ^
  -d "{\"input\": \"Is monolithic or microservices better for our startup?\"}"

# List skills
curl http://localhost:3000/skills
```

## 🛠️ Waza Skills

| Skill | Description | Use Case |
|-------|-------------|----------|
| `/think` | Deep analysis & problem-solving | Architecture decisions, troubleshooting |
| `/write` | Technical writing & docs | Documentation, emails, explanations |
| `/design` | System architecture & UI/UX | System design, wireframes, planning |
| `/hunt` | Research & info gathering | Market research, competitive analysis |
| `/learn` | Learning & knowledge synthesis | Tutorials, concept explanations |
| `/read` | Content analysis & extraction | Summarize articles, extract insights |
| `/check` | Code review & QA | Code quality, security, best practices |
| `/health` | Diagnostics & optimization | System health, performance tuning |

## 📡 API Endpoints

### Core

- `POST /query` - Chat with Jarvis
- `POST /skill/{name}` - Use a specific skill
- `GET /skills` - List available skills
- `GET /health` - Health check

### Authentication

- `POST /auth/register` - Create user account
- `POST /auth/login` - Login and get JWT token

### History

- `GET /history/{user_id}` - Get conversation history
- `GET /history/{user_id}/stats` - Usage statistics
- `POST /history/{user_id}/clear` - Clear history

### Tools

- `POST /tools/execute` - Execute code (Python, JS, Bash)
- `GET /tools/file/read` - Read file
- `POST /tools/file/write` - Write file
- `GET /tools/search` - Web search

### WebSocket

- `WS /ws/{user_id}` - Real-time chat connection

## 🐳 Docker Deployment

### Cloud Qwen API

```bash
docker-compose --profile cloud up -d
```

### Local Ollama

```bash
docker-compose --profile local up -d
```

## 🎯 Usage Examples

### Deep Analysis with /think

```bash
curl -X POST http://localhost:3000/skill/think ^
  -H "Content-Type: application/json" ^
  -d "{\"input\": \"How should we handle database migrations in production?\"}"
```

### Write Documentation with /write

```bash
curl -X POST http://localhost:3000/skill/write ^
  -H "Content-Type: application/json" ^
  -d "{\"input\": \"Document our REST API for developers\"}"
```

### Design System Architecture

```bash
curl -X POST http://localhost:3000/skill/design ^
  -H "Content-Type: application/json" ^
  -d "{\"input\": \"Design a real-time notification system for 1M users\"}"
```

### Code Review with /check

```bash
curl -X POST http://localhost:3000/skill/check ^
  -H "Content-Type: application/json" ^
  -d "{\"input\": \"Review this authentication code for security issues\"}"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QWEN_API_TYPE` | API provider (dashscope/ollama) | dashscope |
| `QWEN_API_KEY` | Your DashScope API key | - |
| `QWEN_MODEL` | Model to use | qwen-plus |
| `QWEN_BASE_URL` | DashScope endpoint | - |
| `OLLAMA_MODEL` | Local Ollama model | qwen:7b |
| `PORT` | Server port | 3000 |
| `DATABASE_URL` | SQLite database path | sqlite+aiosqlite:///./jarvis.db |
| `JWT_SECRET_KEY` | Secret for JWT tokens | change-me |

## 🧪 Development

### Run in Development Mode

```bash
.venv/Scripts/python.exe -m src.cli serve --port 3000
```

### View Conversation History

```bash
.venv/Scripts/python.exe -m src.cli history --user-id web-user
```

### Check Usage Stats

```bash
.venv/Scripts/python.exe -m src.cli stats --user-id web-user
```

## 📚 Next Steps

1. **Add Custom Tools** - Extend `src/tools/handlers.py` with your own tools
2. **Create New Skills** - Add markdown files to `src/waza-skills/`
3. **Integrate APIs** - Add web search, code execution, database access
4. **Build Mobile App** - Use the REST API with React Native or Flutter
5. **Advanced Features** - Add streaming responses, function calling, multi-agent systems

## 🔒 Security Notes

- **Change JWT secret** in production (`.env` file)
- **Enable authentication** for production endpoints
- **Sanitize inputs** for code execution tools
- **Rate limiting** recommended for public deployments

## 📖 References

- **Waza**: https://github.com/tw93/Waza
- **Qwen**: https://github.com/QwenLM/Qwen
- **Ollama**: https://ollama.ai
- **DashScope**: https://dashscope.aliyun.com
- **FastAPI**: https://fastapi.tiangolo.com

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Add your changes
4. Submit a pull request

## 📄 License

MIT License - feel free to use for personal or commercial projects.

---

**Built with ❤️ for personal productivity and engineering excellence**
