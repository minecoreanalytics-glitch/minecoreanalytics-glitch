<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Morpheus Intelligence Platform

A universal data intelligence platform that transforms how organizations discover, understand, and leverage their data assets through automated metadata discovery, knowledge graph construction, and AI-powered insights.

**Version:** 1.0 (MVP Development - Phase 0.5)  
**Status:** ~90% Backend Complete | Frontend In Progress

---

## 📚 Documentation

Complete project documentation is available in [`./doc/`](./doc/):

- **[Product Overview](./doc/PRD.md)** - Vision, features, and requirements
- **[Architecture](./doc/architecture.md)** - System design and components
- **[Development Plan](./doc/dev-plan.md)** - MVP roadmap and current status
- **[Technical Requirements](./doc/requirements.md)** - Dependencies and specifications
- **[Changelog](./doc/changelog.md)** - Complete change history

For a complete documentation index, see **[`./doc/README.md`](./doc/README.md)**

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ or 20+
- **Python** 3.11+
- **Google Cloud BigQuery** access (for data source connectivity)
- **Gemini API** key (for AI features)

### Frontend Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   - Set `GEMINI_API_KEY` in [`.env.local`](.env.local)

3. **Run development server:**
   ```bash
   npm run dev
   ```

### Backend Setup

1. **Navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure credentials:**
   - Place BigQuery service account JSON in `backend/temp_creds.json`
   - Or configure via environment variables (see [`backend/README.md`](backend/README.md))

5. **Run backend server:**
   ```bash
   python main.py
   ```

---

## 🏗️ Project Structure

```
morpheus-intelligence-platform/
├── doc/                    # 📚 All project documentation
│   ├── README.md          # Documentation index
│   ├── PRD.md             # Product requirements
│   ├── architecture.md    # System architecture
│   └── ...                # Other docs
├── backend/               # 🐍 Python FastAPI backend
│   ├── core/             # Core platform components
│   ├── modules/          # Feature modules
│   └── scripts/          # Utility scripts
├── components/           # ⚛️ React UI components
├── pages/               # 📄 Application pages
├── services/            # 🔧 Frontend services
└── laststep.md          # 📝 Last change tracking
```

---

## ✨ Key Features

- **Universal Data Connectivity** - Connect to BigQuery (more sources coming)
- **Automated Metadata Catalog** - Discover and catalog data assets automatically
- **Knowledge Graph** - Visual representation of data relationships
- **AI-Powered Analytics** - Natural language queries with Gemini
- **Customer 360 View** - Unified customer data exploration

See [`./doc/PRD.md`](./doc/PRD.md) for complete feature list.

---

## 🔄 Current Status

**Phase 0.5: Stabilization** (~90% Complete)

### ✅ Completed
- Core backend APIs operational
- BigQuery connector working (9 datasets, 43 tables, 765 columns discovered)
- Metadata catalog functional
- Graph builder implemented
- React components and routing

### ⚠️ In Progress
- Frontend rendering issues being debugged
- Loading states and error handling
- End-to-end testing

See [`./doc/dev-plan.md`](./doc/dev-plan.md) for detailed roadmap.

---

## 🛠️ Development

### Making Changes

Before making any changes, follow the Code Mode SOP:

1. **Read context:** [`./laststep.md`](./laststep.md) and [`./doc/README.md`](./doc/README.md)
2. **Create rollback point:** Git commit or file-based rollback
3. **Make changes:** Small, reviewable increments
4. **Update docs:** [`./doc/changelog.md`](./doc/changelog.md) and [`./laststep.md`](./laststep.md)

See [`./doc/rollback-policy.md`](./doc/rollback-policy.md) for rollback procedures.

### Running Tests

```bash
# Backend tests
cd backend/scripts
python test_full_flow.py

# Frontend (when available)
npm test
```

---

## 📋 Documentation Standards

- All documentation in [`./doc/`](./doc/) as Markdown
- Update [`./doc/changelog.md`](./doc/changelog.md) for all changes
- Record decisions in [`./doc/decisions.md`](./doc/decisions.md)
- Track last change in [`./laststep.md`](./laststep.md)

---

## 🤝 Contributing

1. Review [`./doc/PRD.md`](./doc/PRD.md) for product vision
2. Check [`./doc/dev-plan.md`](./doc/dev-plan.md) for current priorities
3. Follow architecture in [`./doc/architecture.md`](./doc/architecture.md)
4. Create rollback point before changes
5. Update documentation

---

## 📞 Support

- **Documentation:** [`./doc/README.md`](./doc/README.md)
- **Architecture Questions:** [`./doc/architecture.md`](./doc/architecture.md)
- **Current Status:** [`./laststep.md`](./laststep.md)
- **Change History:** [`./doc/changelog.md`](./doc/changelog.md)

---

## 📄 License

[License information to be added]

---

**View this app in AI Studio:** https://ai.studio/apps/temp/1

**Git Repository:** Initialized (commits: e64fe67, cb1940b)
