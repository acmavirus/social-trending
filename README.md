# ⚡ TrendSense - Real-Time Intelligent RSS Aggregator

A sophisticated, enterprise-grade containerized full-stack ecosystem designed for high-throughput real-time news acquisition, sophisticated cleaning, and dynamic visualizations. 

TrendSense automates knowledge retrieval by tracking configured global and domestic news endpoints utilizing a highly reactive architecture.

---

## 🚀 Technology Stack Architecture

Built on a cutting-edge, Dockerized Microservices paradigm:

- **⚡ API Backend Core**: `Python 3.11` driven by `FastAPI` for asynchronous non-blocking throughput.
- **🤖 Intelligent Crawler**: Custom asynchronous aggregator leveraging `Feedparser`, `httpx`, and `APScheduler` for periodic automated ingestion workflows.
- **💿 Data Persistence Layer**: `MongoDB` cluster utilizing non-relational high-density schema for flexible JSON feed normalization with built-in duplication protection.
- **🎨 Advanced Presentation Layer**: Stunning Single Page Application (SPA) built purely on modern **Vanilla CSS & JS** featuring dark-mode optimization, glassmorphism aesthetics, and dynamic state synchronization.
- **🌐 Gateway Edge Routing**: `Nginx` acting as reverse proxy providing efficient static delivery and seamless CORS resolution to backplane services.

---

## 💎 Core Features

1. **Autonomous Knowledge Collection**: Automated cycle scheduling polls distributed endpoints every 15 minutes, silently merging high-velocity events.
2. **Dynamic Ecosystem Ingestion**: Fully integrated User Interface workflow to dynamically inject, delete, and reconfigure operational RSS feeds natively directly into the Database.
3. **Deterministic Intelligence Filters**: Advanced substring pattern recognition and instant categorical source isolation filtering.
4. **Sub-second State Syncing**: Automated background synchronization triggers immediately upon system reconfiguration—zero cooldown necessary.
5. **Zero-Touch Orchestration**: Single command unified cluster instantiation through isolated Docker infrastructure networks.

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

Upon cluster convergence, Docker automatically initiates:
1. Specialized MongoDB cluster initialization.
2. Hypercorn/Uvicorn-wrapped FastAPI Application Engine (Internally listening on `:8000`).
3. Hardened Nginx Reverse Proxy rendering presentation assets (Listening externally on `:8080`).

### Ecosystem Entry Points

- **Production Presentation UI**: [http://localhost:8080](http://localhost:8080)
- **Reactive API Gateway Hub**: [http://localhost:8000](http://localhost:8000)
- **Standard OpenAPI Compliance Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📝 Source Operations Configuration

Out-of-the-box defaults leverage standard domestic indices (VnExpress, Tuổi Trẻ) alongside foundational global giants (NYT, The Guardian, Wired, SCMP). 

To administer and refine this baseline dynamically, access the sidebar controls through the Dashboard UI or via custom scripts targeted at our `/api/sources` endpoints.
