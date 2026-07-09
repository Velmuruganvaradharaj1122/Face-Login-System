# Face Recognition Login System

A complete production-ready Face Recognition Login System built with Python 3.12, Flask, OpenCV, face_recognition, SQLAlchemy, and MySQL.
Flask + OpenCV face-recognition login system with separate admin and user portals, per-user/per-group licensing, group dashboards, in-app file sharing & messaging, and a small REST API for integration with other frontends. MySQL-backed via SQL Alchemy, with a Docker/Docker Compose setup.

## Features

- User Registration (stores employee info and facial encodings in MySQL).
- Face Login Authentication (compares captured webcam face with stored encodings).
- Session Management & Protected Dashboard.
- File Sharing & Messaging System (send text, images, videos, and documents within groups).
- REST API Support for integration with other frontends.
- Docker & Docker Compose setup included.

## Prerequisites

- Python 3.12+ (if running locally without Docker)
- MySQL Server 8+
- CMake and C++ Build Tools (required to compile the `dlib` library used by `face_recognition`)

## Setup Instructions

1. **Create a Python virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows PowerShell: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure MySQL:**
   - Make sure MySQL is running on your machine.
   - Run the provided `db_schema.sql` script in your MySQL client to create the database and tables.
   - Update `.env` with your `DB_USER` and `DB_PASSWORD`.

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   - Open your browser and navigate to `http://localhost:5000`.

## Important Security Note
By default, standard webcams do not provide reliable liveness detection (blink detection, depth sensing). This system relies on strict facial matching. For enterprise security, consider integrating a specialized liveness detection service or hardware.
