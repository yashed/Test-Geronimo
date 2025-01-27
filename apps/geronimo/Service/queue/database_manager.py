import sqlite3
import os
import json

DB_DIR = os.getenv("DATA_DIR", "/tmp")
DB_FILE = os.path.join(DB_DIR, "GeronimoV1.db")


class DatabaseManager:
    def __init__(self):
        # Ensure the database directory exists
        os.makedirs(DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        task_query = """
        CREATE TABLE IF NOT EXISTS task_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firstName TEXT,
            lastName TEXT,
            email TEXT,
            phone TEXT,
            jobTitle TEXT,
            company TEXT,
            country TEXT,
            state TEXT,
            area_of_interest TEXT,
            contact_reason TEXT,
            industry TEXT,
            can_help_comment TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        email_query = """
        CREATE TABLE IF NOT EXISTS email_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            subject TEXT,
            sender TEXT,
            recipient TEXT,
            cc TEXT,
            FOREIGN KEY (task_id) REFERENCES task_queue (id)
        )
        """

        self.conn.execute(task_query)
        self.conn.execute(email_query)
        self.conn.commit()

    def add_task(self, lead_info):
        task_query = """
        INSERT INTO task_queue (firstName, lastName, email, phone, jobTitle, company, country, state,
                                area_of_interest, contact_reason, industry, can_help_comment, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
        """
        cursor = self.conn.execute(
            task_query,
            (
                lead_info["firstName"],
                lead_info["lastName"],
                lead_info["email"],
                lead_info["phone"],
                lead_info["jobTitle"],
                lead_info["company"],
                lead_info["country"],
                lead_info.get("state", ""),
                lead_info["areaOfInterest"],
                lead_info["contactReason"],
                lead_info.get("industry", ""),
                lead_info["canHelpComment"],
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def add_email_info(self, email_info):
        email_query = """
        INSERT INTO email_info (task_id, subject, sender, recipient, cc)
        VALUES (?, ?, ?, ?, ?)
        """
        self.conn.execute(
            email_query,
            (
                email_info["task_id"],
                email_info["subject"],
                email_info["from_"],
                json.dumps(email_info["to"]),
                json.dumps(email_info.get("cc", [])),
            ),
        )
        self.conn.commit()

    def get_pending_tasks(self):
        task_query = "SELECT * FROM task_queue WHERE status = 'PENDING'"
        cursor = self.conn.execute(task_query)
        tasks = [
            dict(zip([column[0] for column in cursor.description], row))
            for row in cursor.fetchall()
        ]

        for task in tasks:
            email_query = "SELECT * FROM email_info WHERE task_id = ?"
            email_cursor = self.conn.execute(email_query, (task["id"],))
            email_info = email_cursor.fetchone()
            if email_info:
                email_columns = [column[0] for column in email_cursor.description]
                task["email_info"] = dict(zip(email_columns, email_info))
                task["email_info"]["recipient"] = json.loads(
                    task["email_info"]["recipient"]
                )
                task["email_info"]["cc"] = json.loads(task["email_info"]["cc"])
        print("Full Task -", tasks)
        return tasks

    def get_mail_info(self, task_id):
        email_query = "SELECT * FROM email_info WHERE task_id = ?"
        email_cursor = self.conn.execute(email_query, (task_id,))
        email_info = email_cursor.fetchone()
        if email_info:
            email_columns = [column[0] for column in email_cursor.description]
            email_info = dict(zip(email_columns, email_info))
            email_info["recipient"] = json.loads(email_info["recipient"])
            email_info["cc"] = json.loads(email_info["cc"])
        return email_info

    def update_task_status(self, task_id, status):
        query = "UPDATE task_queue SET status = ? WHERE id = ?"
        self.conn.execute(query, (status, task_id))
        self.conn.commit()


if __name__ == "__main__":
    db_manager = DatabaseManager()
    print("Database initialized.")
