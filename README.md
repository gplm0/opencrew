# 🤖 OpenCrew - Multi-Agent AI Crew

A sophisticated multi-agent AI orchestration system that automatically decomposes complex tasks and executes them using specialist agents powered by Qwen LLM.

**Two Modes:**
- **Single-Agent Mode** - Direct chat with one AI assistant (Jarvis)
- **Multi-Agent Mode (OpenCrew)** - Supervisor orchestrates 8 specialist agents for complex tasks

## ✨ Features

- 🧠 **Multi-Agent Orchestration** - Supervisor decomposes tasks across specialist agents
- 🤖 **8 Specialist Agents** - think, write, design, hunt, learn, read, check, health
- 📋 **Task Planning** - Automatic task decomposition with dependency tracking
- 🔄 **Parallel Execution** - Independent subtasks run concurrently for speed
- 💬 **Multiple Interfaces** - Web UI, CLI, REST API, WebSocket
- 📊 **Vision Dashboard** - Real-time monitoring of agents and tasks
- 💾 **Session Memory** - Persistent history with SQLite
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
opencrew/
├── src/
│   ├── agents/                 # Multi-agent system (NEW)
│   │   ├── orchestrator.py     # Main entry point for crew mode
│   │   ├── supervisor.py       # Task decomposition & planning
│   │   ├── specialist_agent.py # Specialist agents (8 skills)
│   │   ├── base_agent.py       # Base agent class
│   │   ├── message_bus.py      # Inter-agent communication
│   │   ├── registry.py         # Agent registry & task board
│   │   └── crew_session.py     # Session tracking & history
│   │
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
│   ├── cli.py                  # Single-agent CLI
│   ├── crew_cli.py             # Multi-agent crew CLI
│   └── direct_cli.py           # Direct skill CLI
│
├── config/
│   └── settings.py             # Application configuration
│
├── data/                       # SQLite database storage
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

### 3. Run opencrew

#### Option A: CLI Chat

```bash
.venv/Scripts/python.exe -m src.cli chat
```

#### Option B: Use a Skill Directly

```bash
.venv/Scripts/python.exe -m src.cli use-skill think "Should we use microservices or monolith?"
```

#### Option C: Multi-Agent Crew (OpenCrew)

```bash
# Run a complex task with multiple AI agents working together
.venv/Scripts/python.exe -m src.crew_cli run "Design and document a REST API for our service" --stream

# View the crew dashboard
.venv/Scripts/python.exe -m src.crew_cli vision

# Check crew status
.venv/Scripts/python.exe -m src.crew_cli status
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

## 🤖 Multi-Agent System

OpenCrew uses a supervisor-based multi-agent architecture to automatically decompose and execute complex tasks.

### How It Works

1. **Supervisor Agent** - Analyzes your task and creates an execution plan
2. **Task Decomposition** - Breaks complex tasks into subtasks with dependencies
3. **Specialist Assignment** - Assigns each subtask to the appropriate skill agent
4. **Parallel Execution** - Runs independent subtasks concurrently for speed
5. **Result Consolidation** - Combines all results into a comprehensive final response

### Agent Roles

| Agent | Role | Responsibility |
|-------|------|----------------|
| **Supervisor** | Orchestrator | Task planning, coordination, result consolidation |
| **Think Agent** | Problem Solver | Analysis, reasoning, decision-making |
| **Write Agent** | Technical Writer | Documentation, explanations, content creation |
| **Design Agent** | Architect | System design, architecture, planning |
| **Hunt Agent** | Researcher | Information gathering, market research |
| **Learn Agent** | Teacher | Knowledge synthesis, tutorials |
| **Read Agent** | Analyst | Content analysis, summarization |
| **Check Agent** | QA Engineer | Code review, security, best practices |
| **Health Agent** | Diagnostician | System health, performance optimization |

### Session Management

OpenCrew tracks all multi-agent sessions with detailed history:

```bash
# View recent sessions
.venv/Scripts/python.exe -m src.crew_cli history --limit 10

# View statistics
.venv/Scripts/python.exe -m src.crew_cli stats
```

Each session records:
- Task description and execution plan
- Number of agents and subtasks
- Execution time and success/failure status
- Complete results and agent contributions

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

### Multi-Agent Crew Mode (OpenCrew)

Run tasks through the multi-agent orchestration system:

```bash
# Run with streaming progress
.venv/Scripts/python.exe -m src.crew_cli run "Design a scalable API for user management" --stream

# Run with specific skills
.venv/Scripts/python.exe -m src.crew_cli run "Build a ML model for predictions" --skills think,design,check

# View crew vision dashboard
.venv/Scripts/python.exe -m src.crew_cli vision

# Check crew status
.venv/Scripts/python.exe -m src.crew_cli status

# View session history
.venv/Scripts/python.exe -m src.crew_cli history

# View crew statistics
.venv/Scripts/python.exe -m src.crew_cli stats
```

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

### Architecture Components

**Orchestrator** (`src/agents/orchestrator.py`)
- Main entry point for multi-agent mode
- Initializes supervisor and specialist agents
- Manages task execution lifecycle
- Provides progress callbacks and vision dashboard

**Supervisor** (`src/agents/supervisor.py`)
- Decomposes tasks into subtasks using LLM
- Creates execution plans with dependency tracking
- Assigns tasks to specialist agents
- Consolidates results into final response

**Specialist Agents** (`src/agents/specialist_agent.py`)
- 8 agents, each with a specific Waza skill
- Execute tasks independently
- Report progress and results back to supervisor

**Message Bus** (`src/agents/message_bus.py`)
- Inter-agent communication system
- Broadcast and point-to-point messaging
- Session tracking and event management

**Crew Session** (`src/agents/crew_session.py`)
- Persistent session tracking with SQLite
- Session history and statistics
- Success/failure tracking

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
2. **Create New Skills** - Add markdown files to `src/waza-skills/` and create matching specialist agents
3. **Extend Orchestrator** - Add new phases to the execution pipeline (e.g., validation, optimization)
4. **Build Custom Agents** - Create new specialist agents in `src/agents/` for domain-specific tasks
5. **Integrate APIs** - Add web search, code execution, database access to agents
6. **Vision Dashboard** - Build a web-based dashboard using the vision API endpoint
7. **Advanced Planning** - Improve task decomposition with better dependency tracking
8. **Build Mobile App** - Use the REST API with React Native or Flutter
9. **Multi-Crew Support** - Run multiple independent crews for different projects

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
