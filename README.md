# 📚 Book Library REST API

A fully functional REST API for managing a personal book collection, built with **Flask** and **SQLite**. Includes input validation, error handling, filtering and statistics.

## Features
- Full CRUD: create, read, update, delete books
- Filter by genre, read status, or search by title/author
- Input validation with descriptive error messages
- Library statistics endpoint
- Auto-seeded with sample data on first run

## Requirements
```bash
pip install -r requirements.txt
```

## Running
```bash
python app.py
# API available at http://localhost:5000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API documentation |
| GET | `/books` | List all books |
| GET | `/books?genre=Sci-Fi` | Filter by genre |
| GET | `/books?search=python` | Search by title/author |
| GET | `/books?read=true` | Filter read books |
| GET | `/books/<id>` | Get single book |
| POST | `/books` | Add new book |
| PUT | `/books/<id>` | Update a book |
| DELETE | `/books/<id>` | Delete a book |
| GET | `/books/stats` | Library statistics |

## Example Requests

```bash
# Get all books
curl http://localhost:5000/books

# Add a book
curl -X POST http://localhost:5000/books \
  -H "Content-Type: application/json" \
  -d '{"title": "Python Crash Course", "author": "Eric Matthes", "genre": "Programming", "year": 2019, "rating": 4.6}'

# Update rating
curl -X PUT http://localhost:5000/books/1 \
  -H "Content-Type: application/json" \
  -d '{"rating": 5.0, "read": true}'

# Get stats
curl http://localhost:5000/books/stats
```

## Skills Demonstrated
- RESTful API design with Flask
- SQLite integration and raw SQL queries
- Input validation and error handling (422, 404, 400)
- Query parameters for filtering and searching
- JSON serialization
- HTTP status codes
