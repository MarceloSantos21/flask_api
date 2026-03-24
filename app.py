"""
Book Library REST API
=====================
A full CRUD REST API built with Flask and SQLite.
Endpoints for managing a personal book collection.
"""

from flask import Flask, request, jsonify, abort
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
DB_FILE = "library.db"


# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS books (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                author      TEXT    NOT NULL,
                genre       TEXT,
                year        INTEGER,
                rating      REAL,
                read        INTEGER NOT NULL DEFAULT 0,
                notes       TEXT,
                created_at  TEXT    NOT NULL
            );
        """)
        # Seed some example data if empty
        count = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        if count == 0:
            seed_data = [
                ("Clean Code", "Robert C. Martin", "Programming", 2008, 4.5, 1, "Great read for any developer."),
                ("The Pragmatic Programmer", "David Thomas", "Programming", 1999, 4.8, 1, "Must-read classic."),
                ("Fluent Python", "Luciano Ramalho", "Programming", 2015, 4.7, 0, "Deep dive into Python."),
                ("Sapiens", "Yuval Noah Harari", "History", 2011, 4.3, 1, "Fascinating perspective on humanity."),
                ("Dune", "Frank Herbert", "Sci-Fi", 1965, 4.9, 0, "Epic sci-fi universe."),
            ]
            conn.executemany(
                "INSERT INTO books (title, author, genre, year, rating, read, notes, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [(t, a, g, y, r, rd, n, datetime.now().isoformat()) for t, a, g, y, r, rd, n in seed_data]
            )
        conn.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def book_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "author": row["author"],
        "genre": row["genre"],
        "year": row["year"],
        "rating": row["rating"],
        "read": bool(row["read"]),
        "notes": row["notes"],
        "created_at": row["created_at"],
    }


def validate_book(data: dict, require_all: bool = True) -> tuple[dict, list]:
    errors = []
    cleaned = {}

    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            errors.append("'title' must be a non-empty string.")
        else:
            cleaned["title"] = data["title"].strip()
    elif require_all:
        errors.append("'title' is required.")

    if "author" in data:
        if not isinstance(data["author"], str) or not data["author"].strip():
            errors.append("'author' must be a non-empty string.")
        else:
            cleaned["author"] = data["author"].strip()
    elif require_all:
        errors.append("'author' is required.")

    if "year" in data and data["year"] is not None:
        try:
            yr = int(data["year"])
            if not (0 < yr <= datetime.now().year + 1):
                errors.append("'year' must be a valid year.")
            else:
                cleaned["year"] = yr
        except (ValueError, TypeError):
            errors.append("'year' must be an integer.")

    if "rating" in data and data["rating"] is not None:
        try:
            rt = float(data["rating"])
            if not (0.0 <= rt <= 5.0):
                errors.append("'rating' must be between 0 and 5.")
            else:
                cleaned["rating"] = round(rt, 1)
        except (ValueError, TypeError):
            errors.append("'rating' must be a number.")

    if "genre" in data:
        cleaned["genre"] = data["genre"]
    if "notes" in data:
        cleaned["notes"] = data["notes"]
    if "read" in data:
        cleaned["read"] = int(bool(data["read"]))

    return cleaned, errors


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({
        "message": "📚 Book Library API",
        "version": "1.0",
        "endpoints": {
            "GET  /books": "List all books (supports ?genre=, ?read=, ?search=)",
            "GET  /books/<id>": "Get a single book",
            "POST /books": "Add a new book",
            "PUT  /books/<id>": "Update a book",
            "DELETE /books/<id>": "Delete a book",
            "GET  /books/stats": "Library statistics",
        }
    })


@app.route("/books", methods=["GET"])
def get_books():
    genre = request.args.get("genre")
    read = request.args.get("read")
    search = request.args.get("search")

    query = "SELECT * FROM books WHERE 1=1"
    params: list = []

    if genre:
        query += " AND LOWER(genre) = LOWER(?)"
        params.append(genre)
    if read is not None:
        query += " AND read = ?"
        params.append(1 if read.lower() in ("1", "true", "yes") else 0)
    if search:
        query += " AND (LOWER(title) LIKE ? OR LOWER(author) LIKE ?)"
        params += [f"%{search.lower()}%", f"%{search.lower()}%"]

    query += " ORDER BY title"

    with get_db() as conn:
        books = conn.execute(query, params).fetchall()

    return jsonify({
        "count": len(books),
        "books": [book_to_dict(b) for b in books]
    })


@app.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id: int):
    with get_db() as conn:
        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        abort(404, description=f"Book #{book_id} not found.")
    return jsonify(book_to_dict(book))


@app.route("/books", methods=["POST"])
def create_book():
    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Request body must be JSON.")

    cleaned, errors = validate_book(data, require_all=True)
    if errors:
        return jsonify({"errors": errors}), 422

    cleaned["created_at"] = datetime.now().isoformat()

    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO books (title, author, genre, year, rating, read, notes, created_at) "
            "VALUES (:title, :author, :genre, :year, :rating, :read, :notes, :created_at)",
            {
                "title": cleaned.get("title"),
                "author": cleaned.get("author"),
                "genre": cleaned.get("genre"),
                "year": cleaned.get("year"),
                "rating": cleaned.get("rating"),
                "read": cleaned.get("read", 0),
                "notes": cleaned.get("notes"),
                "created_at": cleaned["created_at"],
            }
        )
        conn.commit()
        book = conn.execute("SELECT * FROM books WHERE id = ?", (cur.lastrowid,)).fetchone()

    return jsonify(book_to_dict(book)), 201


@app.route("/books/<int:book_id>", methods=["PUT"])
def update_book(book_id: int):
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not existing:
        abort(404, description=f"Book #{book_id} not found.")

    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Request body must be JSON.")

    cleaned, errors = validate_book(data, require_all=False)
    if errors:
        return jsonify({"errors": errors}), 422
    if not cleaned:
        abort(400, description="No valid fields provided for update.")

    set_clause = ", ".join(f"{k} = :{k}" for k in cleaned)
    cleaned["id"] = book_id

    with get_db() as conn:
        conn.execute(f"UPDATE books SET {set_clause} WHERE id = :id", cleaned)
        conn.commit()
        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()

    return jsonify(book_to_dict(book))


@app.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id: int):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
    if cur.rowcount == 0:
        abort(404, description=f"Book #{book_id} not found.")
    return jsonify({"message": f"Book #{book_id} deleted successfully."}), 200


@app.route("/books/stats", methods=["GET"])
def get_stats():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        read = conn.execute("SELECT COUNT(*) FROM books WHERE read=1").fetchone()[0]
        avg_rating = conn.execute("SELECT AVG(rating) FROM books WHERE rating IS NOT NULL").fetchone()[0]
        genres = conn.execute(
            "SELECT genre, COUNT(*) as count FROM books WHERE genre IS NOT NULL GROUP BY genre ORDER BY count DESC"
        ).fetchall()
        top_rated = conn.execute(
            "SELECT title, author, rating FROM books WHERE rating IS NOT NULL ORDER BY rating DESC LIMIT 3"
        ).fetchall()

    return jsonify({
        "total_books": total,
        "books_read": read,
        "books_unread": total - read,
        "average_rating": round(avg_rating, 2) if avg_rating else None,
        "genres": [{"genre": g["genre"], "count": g["count"]} for g in genres],
        "top_rated": [{"title": b["title"], "author": b["author"], "rating": b["rating"]} for b in top_rated],
    })


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(422)
def handle_error(e):
    return jsonify({"error": e.description}), e.code


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"\n📚 Book Library API running at http://localhost:{port}\n")
    app.run(debug=True, port=port)
