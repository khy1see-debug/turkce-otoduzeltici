"""
Self-learning mechanism for Turkish auto-corrector.
Tracks user corrections and learns new words based on acceptance patterns.
"""
import sqlite3
import time
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SelfLearningManager:
    """Manages self-learning from user corrections."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            # Use APPDATA on Windows, fallback to home directory
            import os
            appdata = os.getenv('APPDATA')
            if appdata:
                config_dir = Path(appdata) / "turkce-otoduzeltici"
            else:
                config_dir = Path.home() / ".config" / "turkce-otoduzeltici"
            config_dir.mkdir(parents=True, exist_ok=True)
            db_path = config_dir / "self_learning.db"

        self.db_path = db_path
        self._lock = threading.Lock()
        self._pending_corrections: Dict[str, float] = {}  # word -> timestamp
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Create an SQLite connection with concurrency timeout and WAL mode."""
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
        return conn

    def _init_database(self):
        """Initialize the SQLite database for self-learning data."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS word_learning (
                        word TEXT PRIMARY KEY,
                        acceptance_count INTEGER DEFAULT 0,
                        rejection_count INTEGER DEFAULT 0,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        learned BOOLEAN DEFAULT 0
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS correction_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_text TEXT NOT NULL,
                        corrected_text TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_accepted BOOLEAN DEFAULT NULL,
                        learned_word TEXT
                    )
                ''')
                conn.commit()
            finally:
                conn.close()

    def record_correction(self, original: str, corrected: str):
        """
        Record a correction event for potential learning.

        Args:
            original: Original text before correction
            corrected: Corrected text after processing
        """
        if original == corrected:
            return  # No actual correction made

        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute('''
                    INSERT INTO correction_events (original_text, corrected_text)
                    VALUES (?, ?)
                ''', (original, corrected))
                conn.commit()

                # Mark as pending for potential undo detection
                # We'll check for Ctrl+Z within 2 seconds
                self._pending_corrections[corrected] = time.time()

                # Clean up old pending entries (older than 5 seconds)
                cutoff = time.time() - 5
                self._pending_corrections = {
                    word: ts for word, ts in self._pending_corrections.items()
                    if ts > cutoff
                }
            finally:
                conn.close()

    def record_acceptance(self, word: str):
        """
        Record that a user accepted a correction (no undo).

        Args:
            word: The word that was corrected to
        """
        with self._lock:
            conn = self._get_connection()
            try:
                # Update the most recent correction event for this word
                conn.execute('''
                    UPDATE correction_events
                    SET user_accepted = 1
                    WHERE corrected_text = ? AND user_accepted IS NULL
                    ORDER BY timestamp DESC LIMIT 1
                ''', (word,))

                # Update learning counters
                conn.execute('''
                    INSERT OR REPLACE INTO word_learning (word, acceptance_count, rejection_count, last_updated)
                    VALUES (
                        ?,
                        COALESCE((SELECT acceptance_count FROM word_learning WHERE word = ?), 0) + 1,
                        COALESCE((SELECT rejection_count FROM word_learning WHERE word = ?), 0),
                        CURRENT_TIMESTAMP
                    )
                ''', (word, word, word))

                conn.commit()

                # Check if word should be learned (promoted to personal dictionary)
                self._check_and_promote_word(word, conn)
            finally:
                conn.close()

    def record_rejection(self, word: str):
        """
        Record that a user rejected a correction (undo/Ctrl+Z).

        Args:
            word: The word that was rejected (undo'd)
        """
        with self._lock:
            conn = self._get_connection()
            try:
                # Update the most recent correction event for this word
                conn.execute('''
                    UPDATE correction_events
                    SET user_accepted = 0
                    WHERE corrected_text = ? AND user_accepted IS NULL
                    ORDER BY timestamp DESC LIMIT 1
                ''', (word,))

                # Update learning counters
                conn.execute('''
                    INSERT OR REPLACE INTO word_learning (word, acceptance_count, rejection_count, last_updated)
                    VALUES (
                        ?,
                        COALESCE((SELECT acceptance_count FROM word_learning WHERE word = ?), 0),
                        COALESCE((SELECT rejection_count FROM word_learning WHERE word = ?), 0) + 1,
                        CURRENT_TIMESTAMP
                    )
                ''', (word, word, word))

                conn.commit()

                # Remove from pending corrections if present
                self._pending_corrections.pop(word, None)
            finally:
                conn.close()

    def _check_and_promote_word(self, word: str, conn: sqlite3.Connection):
        """
        Check if a word should be promoted to personal dictionary.

        Args:
            word: Word to check
            conn: Database connection (must be within transaction)
        """
        cursor = conn.execute(
            'SELECT acceptance_count, rejection_count FROM word_learning WHERE word = ?',
            (word,)
        )
        row = cursor.fetchone()

        if row:
            acceptance, rejection = row
            # Promote if: acceptance >= 3 and acceptance >= 2 * rejection
            if acceptance >= 3 and acceptance >= 2 * rejection:
                # Mark as learned
                conn.execute('''
                    UPDATE word_learning
                    SET learned = 1
                    WHERE word = ?
                ''', (word,))

                logger.info(f"Word '{word}' promoted to personal dictionary via self-learning")
                # Note: Actual addition to personal dictionary happens in dictionary.py

    def get_learned_words(self) -> list:
        """Get list of words learned through self-learning."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    'SELECT word FROM word_learning WHERE learned = 1 ORDER BY word'
                )
                return [row[0] for row in cursor.fetchall()]
            finally:
                conn.close()

    def get_word_stats(self, word: str) -> Tuple[int, int]:
        """
        Get acceptance/rejection stats for a word.

        Returns:
            Tuple of (acceptance_count, rejection_count)
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    'SELECT acceptance_count, rejection_count FROM word_learning WHERE word = ?',
                    (word,)
                )
                row = cursor.fetchone()
                if row:
                    return row
                return (0, 0)
            finally:
                conn.close()

    def cleanup_old_records(self, days: int = 30):
        """Clean up old correction events."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute('''
                    DELETE FROM correction_events
                    WHERE timestamp < datetime('now', '-' || ? || ' days')
                ''', (days,))
                conn.commit()
            finally:
                conn.close()


# Global instance
_self_learning_manager: Optional[SelfLearningManager] = None


def get_self_learning_manager() -> SelfLearningManager:
    """Get or create the global self-learning manager."""
    global _self_learning_manager
    if _self_learning_manager is None:
        _self_learning_manager = SelfLearningManager()
    return _self_learning_manager


def record_correction(original: str, corrected: str):
    """Record a correction event for potential learning."""
    get_self_learning_manager().record_correction(original, corrected)


def record_acceptance(word: str):
    """Record user acceptance of a correction."""
    get_self_learning_manager().record_acceptance(word)


def record_rejection(word: str):
    """Record user rejection (undo) of a correction."""
    get_self_learning_manager().record_rejection(word)


def get_learned_words() -> list:
    """Get list of learned words."""
    return get_self_learning_manager().get_learned_words()


if __name__ == "__main__":
    # Test the self-learning manager
    mgr = SelfLearningManager()
    mgr.record_correction("slm", "selam")
    mgr.record_acceptance("selam")
    mgr.record_correction("tşk", "teşekkür")
    mgr.record_acceptance("teşekkür")
    mgr.record_acceptance("teşekkür")

    print("Learned words:", mgr.get_learned_words())
    print("Selam stats:", mgr.get_word_stats("selam"))
    print("Teşekkür stats:", mgr.get_word_stats("teşekkür"))