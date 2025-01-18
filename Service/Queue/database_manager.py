import sqlite3
import os

DB_DIR = os.getenv("DATA_DIR", "/tmp")
DB_FILE = os.path.join(DB_DIR, "tasks.db")


class DatabaseManager:
    def __init__(self):
        # Ensure the database directory exists
        os.makedirs(DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS task_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            company TEXT,
            country TEXT,
            position TEXT,
            interest TEXT,
            email TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def add_task(self, task):
        query = """
        INSERT INTO task_queue (name, company, country, position, interest, email, status)
        VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
        """
        cursor = self.conn.execute(
            query,
            (
                task["name"],
                task["company"],
                task["country"],
                task["position"],
                task["interest"],
                task["email"],
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_pending_tasks(self):
        query = "SELECT * FROM task_queue WHERE status = 'PENDING'"
        cursor = self.conn.execute(query)
        return [
            dict(zip([column[0] for column in cursor.description], row))
            for row in cursor.fetchall()
        ]

    def update_task_status(self, task_id, status):
        query = "UPDATE task_queue SET status = ? WHERE id = ?"
        self.conn.execute(query, (status, task_id))
        self.conn.commit()

    def get_all_tasks(self):
        query = "SELECT * FROM task_queue"
        cursor = self.conn.execute(query)
        return [
            dict(zip([column[0] for column in cursor.description], row))
            for row in cursor.fetchall()
        ]


# generate main function to test the code
if __name__ == "__main__":
    db_manager = DatabaseManager()
    print(db_manager.get_all_tasks())
