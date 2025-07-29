
# 🦅 Meet API

**Meet** is a FastAPI-based backend service for user management, meetings, and social features. Built for scalability and modern development workflows.
![hla](https://github.com/user-attachments/assets/34b17770-0121-48c6-9fa1-556c157dcf95)

---

Roadmap

- [x] Auth
- [x] User
- [x] Follow
- [x] Meeting
- [ ] Docker & Deployment


---

## 🚀 Features

- ✅ User registration, authentication, and profile management  
- 📅 Meeting creation and participant management  
- 👥 Social features: follow/unfollow users  
- ❤️ Health checks and robust error handling  
- 🧱 Modular service and repository layers  
- 🛠️ Alembic migrations for database schema management  
- 🐳 Docker & Docker Compose support for containerized development  

---

## 📁 Project Structure

```
.
├── app/                 # Main FastAPI app
├── alembic/             # Alembic database migrations
├── zarf/                # Container setup
├── pyproject.toml       # Poetry config & dependencies
└── README.md            # Project documentation
```

---

## ⚙️ Getting Started

### 🧰 Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/)
- [Docker](https://www.docker.com/) *(optional, for containerized development)*

### 📦 Installation

```bash
poetry install
```

### 🏃 Running the Development Server

```bash
poetry run uvicorn app.main:app --reload
```

Or with VS Code:

> **Run Task → Start FastAPI Development Server**

---

## 🔄 Database Migrations

```bash
alembic upgrade head
```

---

## 🧪 Running Tests

```bash
poetry run pytest
```

---

## 🐳 Using Docker

```bash
docker compose up --build
```

---

## 📘 API Documentation

Once the server is running, access:

- Swagger UI → [http://localhost:8000/docs](http://localhost:8000/docs)  
- ReDoc → [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🤝 Contributing

1. Fork the repository  
2. Create a feature branch:

```bash
git checkout -b feature/YourFeature
```

3. Commit your changes  
4. Push to GitHub:

```bash
git push origin feature/YourFeature
```

5. Open a Pull Request
