# Idea Bridge 🌉

> **Bridge the Gap Between Vision & Execution.**
> An open, lightweight, and collaborative ecosystem connecting innovators, domain experts, and builders to propose ideas, recruit collaborators, vote on concepts, and advance projects from spark to completion.

---

## 📑 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture & Tech Stack](#architecture--tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
  - [Ideas Endpoints](#ideas-endpoints)
  - [Engagement & Collaboration Endpoints](#engagement--collaboration-endpoints)
  - [System Stats](#system-stats)
- [Stage Lifecycle](#stage-lifecycle)
- [Testing](#testing)
- [Design Decisions](#design-decisions)
- [Contributing](#contributing)
- [License](#license)

---

## 🌟 Overview

Great ideas often stall because dreamers lack builders, and builders lack high-impact ideas. **Idea Bridge** serves as the connective tissue between ideation and tangible implementation.

Whether you're developing climate solutions, open-source developer tooling, civic technology, or healthcare innovations, Idea Bridge offers a clean and distraction-free platform to:
1. **Pitch**: Propose problem statements and targeted solutions.
2. **Validate**: Collect community upvotes, critiques, and actionable feedback.
3. **Assemble**: Recruit cross-disciplinary collaborators by specific skillsets.
4. **Track**: Advance ideas across defined development stages with a visual pipeline.

---

## ✨ Key Features

- **💡 Idea Feed & Exploration**:
  - Full-text search across titles, descriptions, and hashtags.
  - Multi-criteria filtering by **Category** (*Technology, Sustainability, Education, Healthcare, Civic Tech, Creative, Other*) and **Stage**.
  - Dynamic sorting by most upvoted, newest, oldest, or alphabetical.

- **📊 Live Analytics Dashboard**:
  - Real-time counters showing total ideas, active collaborations, registered builders, and completed bridges.

- **🚀 Interactive Stage Workflow**:
  - Visual stage progression stepper tracking ideas through 5 distinct lifecycle phases.
  - Easy stage updates for project owners and collaborators.

- **🤝 Collaborator Recruitment Roster**:
  - Clearly articulated desired roles for each idea.
  - One-click join form for builders to submit their skills and contact info.

- **💬 Threaded Feedback & Discussions**:
  - Contextual comments section on each idea for peer review and brainstorming.

- **⚡ Zero-Dependency Lightweight Architecture**:
  - Built entirely using Python 3 standard library (`http.server`, `sqlite3`, `json`) and vanilla modern HTML5/CSS3/JavaScript.
  - No bloated `node_modules` or complex compilation required for runtime.

---

## 🏗 Architecture & Tech Stack

```
+-------------------------------------------------------------+
|                      Client Browser                         |
|   HTML5 + CSS3 (Modern Responsive Flex/Grid) + Vanilla JS   |
+-------------------------------------------------------------+
                              |
                     HTTP / RESTful JSON
                              |
                              v
+-------------------------------------------------------------+
|                 Idea Bridge HTTP Server                     |
|            Python 3 http.server (server.py)                 |
|       - REST API Route Dispatcher & Validator               |
|       - Static Asset Server (public/ index, css, js)        |
+-------------------------------------------------------------+
                              |
                         SQL Queries
                              |
                              v
+-------------------------------------------------------------+
|                   SQLite Database Layer                     |
|                 db.py & idea_bridge.db                      |
|       - Relational foreign keys & CASCADE deletions         |
|       - Automated migrations & default seed dataset         |
+-------------------------------------------------------------+
```

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend** | Python 3 (`http.server`) | Robust, zero external runtime dependencies, ultra-fast cold start. |
| **Database** | SQLite 3 (`sqlite3`) | Self-contained, ACID compliant, serverless, zero setup. |
| **Frontend** | Vanilla HTML5, CSS3, JS (ES6+) | Blazing fast, universally compatible, clean component styling. |
| **Testing** | Python `unittest` + Playwright | Full unit, API integration, and visual UI verification. |

---

## 📂 Project Structure

```text
.
├── db.py                 # SQLite database schema, seeds, queries, and CRUD API
├── server.py             # HTTP server handling REST endpoints and serving static assets
├── public/               # Frontend single-page application assets
│   ├── index.html        # Semantic HTML UI structure, forms, and modals
│   ├── styles.css        # Responsive CSS theme, layout, cards, and animations
│   └── app.js            # Client-side state management, DOM interactions, and API calls
├── tests/                # Automated test suite
│   └── test_api.py       # Comprehensive unit and integration tests (14 test cases)
└── README.md             # Project documentation and specifications
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (Tested on Python 3.10, 3.11, 3.12).
- Any modern web browser (Chrome, Firefox, Safari, Edge).

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/Idea_Bridge.git
   cd Idea_Bridge
   ```

2. **Start the server:**
   ```bash
   python3 server.py
   ```

3. **Open the application:**
   Navigate to `http://localhost:8000` in your web browser.
   The database will automatically initialize with sample ideas and data upon first launch.

### Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | Port number the HTTP server listens on | `8000` |
| `IDEA_BRIDGE_DB` | Path to the SQLite database file | `idea_bridge.db` |

Example running on a custom port:
```bash
PORT=9000 python3 server.py
```

---

## 📡 API Reference

All requests and responses use standard `application/json` payloads.

### Ideas Endpoints

#### `GET /api/ideas`
Returns a list of ideas matching optional filters.

**Query Parameters:**
- `category` *(string, optional)*: Filter by category (e.g. `Technology`, `Sustainability`).
- `stage` *(string, optional)*: Filter by stage (e.g. `Discovery`, `In Progress`).
- `search` *(string, optional)*: Substring search across title, description, and tags.
- `sort` *(string, optional)*: Sorting mode (`votes`, `newest`, `oldest`, `title`). Default is `votes`.

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "EcoCycle: Campus Food Waste to Compost Bridge",
    "description": "A campus-wide smart bin system...",
    "category": "Sustainability",
    "stage": "In Progress",
    "tags": "sustainability,iot,gardening",
    "author_name": "Elena Rostova",
    "author_email": "elena@example.edu",
    "votes": 14,
    "target_role": "Hardware/IoT Developer",
    "created_at": "2026-11-03T06:30:00+00:00",
    "updated_at": "2026-11-03T06:30:00+00:00",
    "comment_count": 2,
    "collaborator_count": 2
  }
]
```

#### `GET /api/ideas/<id>`
Retrieves full details for a single idea, including all associated comments and collaborators.

#### `POST /api/ideas`
Publishes a new idea bridge.

**Request Body:**
```json
{
  "title": "SolarPond: Thermoelectric Community Power",
  "description": "Harnessing temperature gradients to generate nighttime energy.",
  "category": "Sustainability",
  "stage": "Looking for Team",
  "tags": "solar,energy,clean-tech",
  "target_role": "Thermal Engineer",
  "author_name": "Tara Nair",
  "author_email": "tara@solarpnd.org"
}
```

#### `PATCH /api/ideas/<id>`
Updates editable fields of an idea (e.g., advancing the stage or updating description).

**Request Body:**
```json
{
  "stage": "Completed"
}
```

#### `DELETE /api/ideas/<id>`
Deletes an idea and cascades deletion to all nested comments and collaborator records.

---

### Engagement & Collaboration Endpoints

#### `POST /api/ideas/<id>/vote`
Upvotes or downvotes an idea.

**Request Body:**
```json
{
  "delta": 1
}
```

#### `POST /api/ideas/<id>/comments`
Adds a comment or piece of feedback to an idea.

**Request Body:**
```json
{
  "author_name": "Jordan Lee",
  "content": "Excellent initiative! Happy to contribute."
}
```

#### `POST /api/ideas/<id>/collaborators`
Registers a builder as a collaborator on this project bridge.

**Request Body:**
```json
{
  "name": "Jordan Lee",
  "role": "Thermal Engineer",
  "contact_info": "jordan@cleantech.dev"
}
```

---

### System Stats

#### `GET /api/stats`
Returns aggregated platform metrics for the hero dashboard.

**Response (200 OK):**
```json
{
  "total_ideas": 6,
  "total_votes": 125,
  "total_collaborators": 6,
  "active_projects": 3,
  "completed_projects": 1,
  "categories": {
    "Sustainability": 2,
    "Technology": 1,
    "Healthcare": 1
  },
  "stages": {
    "Discovery": 1,
    "In Progress": 2,
    "Completed": 1
  }
}
```

---

## 🔄 Stage Lifecycle

Idea Bridge models projects along a transparent 5-step maturity pipeline:

```
[ 1. Discovery ] ──▶ [ 2. Discussion ] ──▶ [ 3. Looking for Team ] ──▶ [ 4. In Progress ] ──▶ [ 5. Completed ]
```

1. **Discovery**: Initial raw concept formulation, problem exploration, and viability assessment.
2. **Discussion**: Community feedback loop, refining requirements, scoping challenges.
3. **Looking for Team**: Defining target builder roles and assembling key contributors.
4. **In Progress**: Active execution, prototype construction, and design validation.
5. **Completed**: Finished bridge, released deliverable, or operational initiative.

---

## 🧪 Testing

The repository includes a comprehensive automated test suite testing the database layer, API handlers, data validation, and cascade behaviors.

Run all tests using Python's built-in test runner:
```bash
python3 -m unittest discover tests -v
```

All 14 unit and integration tests run in isolated temporary databases to guarantee zero interference with existing local data.

---

## 🎯 Design Decisions

1. **Zero External Runtime Dependencies**:
   - Eliminates vulnerabilities, dependency drift, and runtime installation overhead.
   - Anyone with a standard Python installation can clone and run immediately.
2. **Progressive Enhancement & Semantic HTML**:
   - Fast initial paint time.
   - Clean keyboard accessibility and responsive layout across desktops, tablets, and phones.
3. **ACID Relational Integrity with SQLite**:
   - Foreign key constraints enabled with `ON DELETE CASCADE` ensures clean data hygiene without orphan comments or collaborator records.

---

## 🤝 Contributing

Contributions are warmly welcomed! To contribute:
1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/amazing-idea-feature`).
3. Write clean, tested code and verify with `python3 -m unittest discover tests`.
4. Commit your changes with clear messages (`git commit -m 'feat: Add export to Markdown option'`).
5. Push to the branch (`git push origin feature/amazing-idea-feature`).
6. Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.
