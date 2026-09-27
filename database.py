import sqlite3
from pathlib import Path

DB_PATH=Path(__file__).with_name("attendance.db")

def get_db():
    db=sqlite3.connect(DB_PATH)
    db.row_factory=sqlite3.Row
    return db

def init_db():
    db=get_db()
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Faculty'
    );
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        roll_number TEXT UNIQUE NOT NULL,
        email TEXT,
        department TEXT,
        password TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present','Absent')),
        UNIQUE(student_id,date),
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    """)
    if not db.execute("SELECT id FROM users WHERE username='admin'").fetchone():
        db.execute("INSERT INTO users(username,password,role) VALUES('admin','admin123','Faculty')")
    if db.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]==0:
        db.executemany("""INSERT INTO students(name,roll_number,email,department,password)
                          VALUES(?,?,?,?,?)""",[
            ("Arun Kumar","CSE001","arun@example.com","CSE","student123"),
            ("Priya Sharma","CSE002","priya@example.com","CSE","student123"),
            ("Rahul Verma","CSE003","rahul@example.com","CSE","student123")
        ])
    db.commit(); db.close()
