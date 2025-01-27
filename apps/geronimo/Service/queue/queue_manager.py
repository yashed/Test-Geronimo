import queue
import threading
import time
from Service.queue.database_manager import DatabaseManager
from Service.mailService import send_mail
import Helper.langchain_helper as lh
import logging

# Configure logging
logger = logging.getLogger(__name__)

# In-memory queue
task_queue = queue.Queue()


# Background worker
class Worker(threading.Thread):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.daemon = True

    def run(self):
        """
        Handle tasks from the queue
           - Get task from the queue
           - Process the task
           - Send email
           - Update task status in the database

        """
        while True:
            try:
                task = task_queue.get()
                if task is None:
                    break

                logger.info("Processing task: %s", task["id"])

                # Generate full name from first name and last name
                name = task["firstName"] + " " + task["lastName"]

                # Get email info from the database
                email_info = self.db_manager.get_mail_info(task["id"])

                response = lh.generate_data(
                    name, task["company"], task["jobTitle"], task["country"]
                )
                send_mail(response, email_info)

                self.db_manager.update_task_status(task["id"], "COMPLETED")
                logger.info("Task completed: %s", task["id"])
            except Exception as e:
                logger.exception("Error processing task: %s", e)
                self.db_manager.update_task_status(task["id"], "PENDING")
            finally:
                task_queue.task_done()


# Start the worker thread
def start_worker():
    db_manager = DatabaseManager()
    worker = Worker(db_manager)
    worker.start()
    return worker
