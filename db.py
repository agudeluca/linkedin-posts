import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="linkedin_jobs.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Create jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT,
                content TEXT UNIQUE,
                found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create job_scans table to track scanning history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_scans (
                scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                jobs_found INTEGER,
                status TEXT,
                error_message TEXT
            )
        ''')
        
        self.conn.commit()
        cursor.close()
        
    def job_exists(self, job_id):
        """Check if a job already exists in the database"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM jobs WHERE job_id = ?', (job_id,))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists
        
    def add_job(self, job_data):
        """Add a new job to the database"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO jobs (
                    job_id, title, url, content, found_at
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                job_data['job_id'],
                job_data['title'],
                job_data['url'],
                job_data.get('content', ''),
                job_data['found_at'],
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding job to database: {e}")
            return False
        finally:
            cursor.close()
            
    def log_scan(self, jobs_found, status="success", error_message=None):
        """Log a scanning session"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO job_scans (jobs_found, status, error_message)
            VALUES (?, ?, ?)
        ''', (jobs_found, status, error_message))
        self.conn.commit()
        cursor.close()
        
    def get_recent_jobs(self, limit=50):
        """Get the most recent jobs"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM jobs 
            ORDER BY found_at DESC 
            LIMIT ?
        ''', (limit,))
        jobs = cursor.fetchall()
        cursor.close()
        return jobs
        
    def close(self):
        """Close the database connection"""
        self.conn.close()
