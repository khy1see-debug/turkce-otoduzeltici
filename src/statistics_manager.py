"""
Statistics management for turkce-otoduzeltici.
Logs corrections and computes usage statistics using SQLite.
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime

def get_config_dir():
    """Return the path to the application configuration directory."""
    appdata = os.getenv('APPDATA')
    if appdata:
        config_dir = Path(appdata) / "turkce-otoduzeltici"
    else:
        config_dir = Path.home() / ".config" / "turkce-otoduzeltici"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def get_db_path():
    """Return the full path to the SQLite database file."""
    return get_config_dir() / "stats.db"

class StatisticsManager:
    def __init__(self):
        self.db_path = get_db_path()
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def create_tables(self):
        """Create the necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        # Table for individual corrections
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                original_text TEXT NOT NULL,
                corrected_text TEXT NOT NULL
            )
        ''')
        # Index on timestamp for faster queries if needed
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON corrections(timestamp)
        ''')
        self.conn.commit()

    def record_correction(self, original_text, corrected_text):
        """
        Record a correction event.
        :param original_text: The original selected text before correction.
        :param corrected_text: The corrected text after applying fix_sentence.
        """
        if original_text == corrected_text:
            # No actual correction, skip recording to save space
            return
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO corrections (timestamp, original_text, corrected_text) VALUES (?, ?, ?)",
            (datetime.now().isoformat(), original_text, corrected_text)
        )
        self.conn.commit()

    def get_total_corrections(self):
        """Return the total number of corrections recorded."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM corrections")
        result = cursor.fetchone()
        return result[0] if result else 0

    def get_top_corrections(self, limit=5):
        """
        Return the most frequent corrections as a list of tuples:
        (original_text, corrected_text, count)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT original_text, corrected_text, COUNT(*) as freq
            FROM corrections
            WHERE original_text != corrected_text
            GROUP BY original_text, corrected_text
            ORDER BY freq DESC
            LIMIT ?
        ''', (limit,))
        return [(row['original_text'], row['corrected_text'], row['freq']) for row in cursor.fetchall()]

    def get_time_saved_seconds(self):
        """
        Estimate time saved in seconds.
        Assumes average typing speed of 0.2 seconds per character (adjustable).
        Time saved = sum(len(corrected) - len(original)) * 0.2 for each correction.
        Note: This is a rough estimate; actual time saved depends on user's typing speed and the nature of errors.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT SUM(LENGTH(corrected_text) - LENGTH(original_text)) as total_diff
            FROM corrections
            WHERE original_text != corrected_text
        ''')
        result = cursor.fetchone()
        total_diff = result[0] if result and result[0] is not None else 0
        # Convert to seconds: assuming 0.2 seconds per character
        return total_diff * 0.2

    def get_time_saved_formatted(self):
        """Return time saved as a formatted string (e.g., '2 saat 30 dakika')."""
        seconds = self.get_time_saved_seconds()
        if seconds < 60:
            return f"{int(seconds)} saniye"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes} dakika {secs} saniye"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours} saat {minutes} dakika"

    def clear_statistics(self):
        """Clear all correction records."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM corrections")
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()