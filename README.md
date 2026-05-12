# ⚡ TrendSense - Real-Time Intelligent AI Aggregator

A sophisticated, enterprise-grade containerized full-stack ecosystem designed for high-throughput real-time news acquisition, advanced AI-driven cleanups, and dynamic cross-platform broadcasting visualizations. 

TrendSense automates universal knowledge retrieval by tracking global news endpoints utilizing a highly reactive, AI-enhanced architecture.

---

## 🚀 Technology Stack Architecture

Built on a cutting-edge, Dockerized Microservices paradigm:

- **⚡ API Backend Core**: `Python 3.11` driven by `FastAPI` for asynchronous non-blocking throughput.
- **🧠 Cognitive Engine**: Integrated `Google Gemini 1.5 Flash` LLM for ultra-low latency semantic event clustering.
- **🤖 Intelligent Crawler**: Custom asynchronous aggregator leveraging `Feedparser`, `httpx`, and `APScheduler` for periodic autonomous workflows.
- **💿 Data Persistence Layer**: `MongoDB` cluster utilizing non-relational schema for flexible JSON feed normalization.
- **🎨 Advanced Presentation Layer**: Stunning Single Page Application (SPA) built on **Vanilla CSS & JS** featuring dark-mode optimization, glassmorphism aesthetics, and dynamic state synchronization.

---

## 💎 Core Features

1. **Autonomous Knowledge Collection**: Automated scheduling cycles poll distributed endpoints every 15 minutes.
2. **🧠 Gemini AI Semantic De-duplication**: High-density LLM batch analytics that comprehend cross-agency reportings. If multiple outlets report the exact same event, AI collapses the noise and presents you only clean, unique distinct signals.
3. **🔗 Dynamic Webhook Broadcasts**: Sub-second native pushed alerts to **Discord Rich Embeds** and **Telegram Bots** configured purely through graphical interface.
4. **🛡️ State-Aware Push Safety**: Resilient atomic check-locking ensures any unique event delivers exactly once to active output streams. No spam, no repeats.
5. **🎛️ Zero-Touch Live Admin**: Fully integrated Dashboard sidebar to dynamically manage RSS sources, and configure system runtime preferences in real-time directly saved into MongoDB cluster.

---

## 📦 Global Provisioning & Execution

### System Prerequisites
- Validated installation of **Docker** Engine.
- **Docker Compose** binary configured within path.

### Application Instantiation
Spin up the complete clustered ecosystem by executing:

```bash
docker-compose up --build -d
```

Upon cluster convergence, the orchestration routine handles standard deployment:
1. High-availability MongoDB cluster.
2. Uvicorn-wrapped FastAPI Application Engine.
3. Nginx Reverse Proxy rendering presentation assets.

### Ecosystem Entry Points

- **Production Presentation UI**: [http://localhost:8080](http://localhost:8080)
- **Reactive API Gateway Hub**: [http://localhost:8000](http://localhost:8000)
- **OpenAPI Compliance Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛠 Operational Dynamic Configuration

Everything is administered on-the-fly through the Web Dashboard via the **"Notifier Setup"** ⚙️ and dynamic sidebar controls.

### 🔔 Push Notification Channels
- **Discord**: Input Channel Webhook to convert textual items into rich aesthetic cards.
- **Telegram**: Input BotFather API Token and numeric ChatID to receive markdown-rendered text feeds.
- Set master toggles to LIVE to initiate instant flow, or STOP instantly with one click.

### 🧠 Artificial Intelligence Layer
- **Gemini Flash Activation**: Simply paste your Google Generative AI key and toggle on the brain icon.
- All incoming streams undergo immediate vectorized collision analysis against existing cache records instantly.
