"""
Idea Bridge - Database Layer
Provides SQLite database connection, table initialization, seeding, and CRUD queries.
"""

import sqlite3
import os
from datetime import datetime, timezone

def get_db_path(db_path=None):
    if db_path is not None:
        return db_path
    return os.environ.get("IDEA_BRIDGE_DB", "idea_bridge.db")

def get_connection(db_path=None):
    path = get_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path=None):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ideas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        stage TEXT NOT NULL DEFAULT 'Discovery',
        tags TEXT DEFAULT '',
        author_name TEXT NOT NULL,
        author_email TEXT DEFAULT '',
        votes INTEGER NOT NULL DEFAULT 0,
        target_role TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idea_id INTEGER NOT NULL,
        author_name TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (idea_id) REFERENCES ideas (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collaborators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idea_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        contact_info TEXT DEFAULT '',
        joined_at TEXT NOT NULL,
        FOREIGN KEY (idea_id) REFERENCES ideas (id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # Seed initial data if table is empty
    cursor.execute("SELECT COUNT(*) AS count FROM ideas")
    count = cursor.fetchone()["count"]
    if count == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.cursor()

    sample_ideas = [
        (
            "EcoCycle: Campus Food Waste to Compost Bridge",
            "A campus-wide smart bin system that logs organic food waste and bridges student volunteers with local community gardens for composting and organic fertilizer distribution.",
            "Sustainability",
            "In Progress",
            "sustainability,iot,gardening,community",
            "Elena Rostova",
            "elena@example.edu",
            14,
            "Hardware/IoT Developer",
            now,
            now
        ),
        (
            "OpenMentor: Skill Exchange for Junior Developers",
            "A peer-to-peer mentoring platform matching junior software engineers with senior engineers for 30-minute targeted code reviews and career design sessions.",
            "Education",
            "Looking for Team",
            "mentorship,web,career,peer-learning",
            "Marcus Chen",
            "marcus@example.com",
            27,
            "Frontend Engineer (React/Vue)",
            now,
            now
        ),
        (
            "CivicVoice: Hyperlocal Policy Pulse",
            "A mobile and web application empowering neighborhood residents to propose, deliberate on, and track urban infrastructure micro-proposals before municipal city council meetings.",
            "Civic Tech",
            "Discussion",
            "civic,govtech,urban-planning,democracy",
            "Aisha Patel",
            "aisha@civicvoice.org",
            9,
            "Policy Analyst & UI Designer",
            now,
            now
        ),
        (
            "HealthBridge: Offline Health Clinic Triage Assistant",
            "A lightweight progressive web application that helps community health workers perform initial symptom triage and emergency routing even without active internet connectivity.",
            "Healthcare",
            "Discovery",
            "healthcare,offline-first,pwa,social-impact",
            "Dr. David Kim",
            "david.kim@globalhealth.org",
            18,
            "Mobile / PWA Developer",
            now,
            now
        ),
        (
            "AlgoVisualizer: Interactive Distributed Systems Simulator",
            "An open-source visualization toolkit showing Raft consensus, Byzantine fault tolerance, and vector clocks in real time with step-by-step interactive animations.",
            "Technology",
            "Completed",
            "algorithms,education,distributed-systems,graphics",
            "Sarah Jenkins",
            "sarah@cs.edu",
            42,
            "Documentation & Community Lead",
            now,
            now
        )
    ]

    cursor.executemany("""
    INSERT INTO ideas (title, description, category, stage, tags, author_name, author_email, votes, target_role, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_ideas)

    # Add sample comments and collaborators for sample ideas
    sample_comments = [
        (1, "Liam O'Connor", "Great initiative! We have 2 local community plots ready to partner.", now),
        (1, "Priya Sharma", "Can we connect weight sensor cells with ESP32 microcontrollers?", now),
        (2, "Alex River", "Would love to mentor on system design topics. Count me in!", now),
        (4, "Fatima Zahra", "Offline SQLite and ServiceWorkers make this very viable. I have experience with this.", now),
    ]
    cursor.executemany("""
    INSERT INTO comments (idea_id, author_name, content, created_at)
    VALUES (?, ?, ?, ?)
    """, sample_comments)

    sample_collabs = [
        (1, "Carlos Mendez", "Hardware Engineer", "carlos@example.com", now),
        (1, "Sofia Rossi", "Outreach Lead", "sofia@example.com", now),
        (2, "Kenji Sato", "Backend Developer", "kenji@example.com", now),
        (5, "Sarah Jenkins", "Creator", "sarah@cs.edu", now),
        (5, "Alex Meyer", "Web Animations Contributor", "alex@example.com", now)
    ]
    cursor.executemany("""
    INSERT INTO collaborators (idea_id, name, role, contact_info, joined_at)
    VALUES (?, ?, ?, ?, ?)
    """, sample_collabs)

    conn.commit()

# CRUD operations
def list_ideas(db_path=None, category=None, stage=None, search=None, sort_by="votes"):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = """
    SELECT i.*,
           COUNT(DISTINCT c.id) AS comment_count,
           COUNT(DISTINCT col.id) AS collaborator_count
    FROM ideas i
    LEFT JOIN comments c ON i.id = c.idea_id
    LEFT JOIN collaborators col ON i.id = col.idea_id
    WHERE 1=1
    """
    params = []

    if category and category.lower() != "all":
        query += " AND LOWER(i.category) = LOWER(?)"
        params.append(category)

    if stage and stage.lower() != "all":
        query += " AND LOWER(i.stage) = LOWER(?)"
        params.append(stage)

    if search:
        search_pattern = f"%{search.strip().lower()}%"
        query += " AND (LOWER(i.title) LIKE ? OR LOWER(i.description) LIKE ? OR LOWER(i.tags) LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern])

    query += " GROUP BY i.id"

    if sort_by == "newest":
        query += " ORDER BY i.created_at DESC"
    elif sort_by == "oldest":
        query += " ORDER BY i.created_at ASC"
    elif sort_by == "title":
        query += " ORDER BY i.title ASC"
    else:  # default votes
        query += " ORDER BY i.votes DESC, i.created_at DESC"

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_idea(idea_id, db_path=None):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
    idea = cursor.fetchone()
    if not idea:
        conn.close()
        return None

    idea_dict = dict(idea)

    cursor.execute("SELECT * FROM comments WHERE idea_id = ? ORDER BY created_at ASC", (idea_id,))
    idea_dict["comments"] = [dict(c) for c in cursor.fetchall()]

    cursor.execute("SELECT * FROM collaborators WHERE idea_id = ? ORDER BY joined_at ASC", (idea_id,))
    idea_dict["collaborators"] = [dict(col) for col in cursor.fetchall()]

    conn.close()
    return idea_dict

def create_idea(data, db_path=None):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
    INSERT INTO ideas (title, description, category, stage, tags, author_name, author_email, target_role, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("title", "").strip(),
        data.get("description", "").strip(),
        data.get("category", "General").strip(),
        data.get("stage", "Discovery").strip(),
        data.get("tags", "").strip(),
        data.get("author_name", "Anonymous").strip(),
        data.get("author_email", "").strip(),
        data.get("target_role", "").strip(),
        now,
        now
    ))
    idea_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_idea(idea_id, db_path)

def update_idea(idea_id, data, db_path=None):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    fields = []
    values = []
    allowed_fields = ["title", "description", "category", "stage", "tags", "target_role", "author_name", "author_email"]
    for field in allowed_fields:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])

    if not fields:
        conn.close()
        return get_idea(idea_id, db_path)

    fields.append("updated_at = ?")
    values.append(now)
    values.append(idea_id)

    query = f"UPDATE ideas SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    return get_idea(idea_id, db_path)

def delete_idea(idea_id, db_path=None):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def vote_idea(idea_id, delta=1, db_path=None):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE ideas SET votes = MAX(0, votes + ?) WHERE id = ?", (delta, idea_id))
    conn.commit()
    cursor.execute("SELECT votes FROM ideas WHERE id = ?", (idea_id,))
    row = cursor.fetchone()
    conn.close()
    return row["votes"] if row else None

def add_comment(idea_id, author_name, content, db_path=None):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
    INSERT INTO comments (idea_id, author_name, content, created_at)
    VALUES (?, ?, ?, ?)
    """, (idea_id, author_name.strip(), content.strip(), now))
    comment_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
    comment = dict(cursor.fetchone())
    conn.close()
    return comment

def add_collaborator(idea_id, name, role, contact_info="", db_path=None):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
    INSERT INTO collaborators (idea_id, name, role, contact_info, joined_at)
    VALUES (?, ?, ?, ?, ?)
    """, (idea_id, name.strip(), role.strip(), contact_info.strip(), now))
    collab_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM collaborators WHERE id = ?", (collab_id,))
    collab = dict(cursor.fetchone())
    conn.close()
    return collab

def get_stats(db_path=None):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total_ideas, SUM(votes) AS total_votes FROM ideas")
    row = cursor.fetchone()
    total_ideas = row["total_ideas"] or 0
    total_votes = row["total_votes"] or 0

    cursor.execute("SELECT COUNT(*) AS total_collaborators FROM collaborators")
    total_collaborators = cursor.fetchone()["total_collaborators"] or 0

    cursor.execute("SELECT COUNT(*) AS active_projects FROM ideas WHERE stage IN ('Looking for Team', 'In Progress')")
    active_projects = cursor.fetchone()["active_projects"] or 0

    cursor.execute("SELECT COUNT(*) AS completed_projects FROM ideas WHERE stage = 'Completed'")
    completed_projects = cursor.fetchone()["completed_projects"] or 0

    cursor.execute("SELECT category, COUNT(*) as count FROM ideas GROUP BY category ORDER BY count DESC")
    category_counts = {r["category"]: r["count"] for r in cursor.fetchall()}

    cursor.execute("SELECT stage, COUNT(*) as count FROM ideas GROUP BY stage")
    stage_counts = {r["stage"]: r["count"] for r in cursor.fetchall()}

    conn.close()
    return {
        "total_ideas": total_ideas,
        "total_votes": total_votes,
        "total_collaborators": total_collaborators,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "categories": category_counts,
        "stages": stage_counts
    }

if __name__ == "__main__":
    init_db()
    ideas = list_ideas()
    print(f"Database initialized successfully with {len(ideas)} ideas.")
    print("Stats:", get_stats())
