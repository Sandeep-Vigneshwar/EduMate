import os
import mysql.connector
from mysql.connector import Error
import json

class DatabaseHandler:
    def __init__(self):
        self.connection = self.connect_to_db()
        self.create_main_table()
        # Removed creation of scraped_data table as it's no longer needed.

    def connect_to_db(self):
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password=os.getenv("db_pass"),  # Update with your MySQL password
                database='edumate'
            )
            return conn
        except Error as e:
            print(f"Error connecting to database: {e}")
            return None

    def create_main_table(self):
        query = '''CREATE TABLE IF NOT EXISTS subjects (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    subject_name VARCHAR(255) UNIQUE,
                    cdp_path TEXT,
                    pyq_path TEXT,
                    notes_path TEXT
                   );'''
        self.execute_query(query)

    def create_subject_table(self, subject_name):
        # Create subject-specific table with two columns: topic_name and file_name
        query = f'''CREATE TABLE IF NOT EXISTS `{subject_name}` (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    topic_name VARCHAR(255) UNIQUE,
                    file_name TEXT
                   );'''
        self.execute_query(query)

    def subject_exists(self, subject_name):
        query = "SELECT subject_name FROM subjects WHERE subject_name = %s"
        cursor = self.connection.cursor()
        cursor.execute(query, (subject_name,))
        result = cursor.fetchone()
        return True if result else False

    def fetch_topics(self, subject_name):
        query = f"SELECT topic_name, file_name FROM `{subject_name}`"
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def insert_subject(self, subject_name, cdp_path, pyq_path, notes_path):
        query = '''INSERT INTO subjects (subject_name, cdp_path, pyq_path, notes_path)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE cdp_path=VALUES(cdp_path), pyq_path=VALUES(pyq_path), notes_path=VALUES(notes_path);'''
        self.execute_query(query, (subject_name, cdp_path, pyq_path, notes_path))

    def insert_topics(self, subject_name, ranked_topics):
        # This method was used to insert extracted topics.
        # We are not using it now as scraped topics will be inserted via insert_scraped_topic.
        self.create_subject_table(subject_name)
        query = f'''INSERT INTO `{subject_name}` (topic_name, file_name)
                   VALUES (%s, %s)
                   ON DUPLICATE KEY UPDATE file_name=VALUES(file_name);'''
        # ranked_topics is not used here.
        self.execute_batch_query(query, ranked_topics)

    def insert_scraped_topic(self, subject_name, topic, pdf_path):
        # Insert scraped topic (with PDF file) into the subject-specific table.
        self.create_subject_table(subject_name)
        query = f'''INSERT INTO `{subject_name}` (topic_name, file_name)
                   VALUES (%s, %s)
                   ON DUPLICATE KEY UPDATE file_name=VALUES(file_name);'''
        self.execute_query(query, (topic, pdf_path))

    def execute_query(self, query, values=None):
        try:
            cursor = self.connection.cursor()
            if values:
                cursor.execute(query, values)
            else:
                cursor.execute(query)
            self.connection.commit()
        except Error as e:
            print(f"Database error: {e}")

    def execute_batch_query(self, query, values):
        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, values)
            self.connection.commit()
        except Error as e:
            print(f"Database batch error: {e}")
