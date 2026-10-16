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
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS phrase_learning (
                        phrase TEXT PRIMARY KEY,
                        count INTEGER DEFAULT 1,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                # 3 saniyeyi geçmiş tüm bekleyen düzeltmeleri otomatik kabul et ve öğren
                self._process_pending_acceptances(conn)
            finally:
                conn.close()

    def _process_pending_acceptances(self, conn: sqlite3.Connection):
        """3 saniyeyi geçen ve geri alınmayan (Ctrl+Z basılmayan) düzeltmeleri kabul edildi sayıp öğrenir."""
        import re
        from src.turkish_case import turkish_lower
        cursor = conn.execute('''
            SELECT id, original_text, corrected_text FROM correction_events
            WHERE user_accepted IS NULL AND timestamp < datetime('now', '-3 seconds')
        ''')
        rows = cursor.fetchall()
        for row_id, orig, corr in rows:
            conn.execute('UPDATE correction_events SET user_accepted = 1 WHERE id = ?', (row_id,))
            raw_tokens = re.findall(r"[a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:['’][a-zA-ZçÇğĞıİöÖşŞüÜ]+)?", corr)
            clean_words = []
            for t in raw_tokens:
                stem = re.split(r"['’]", t)[0]
                low = turkish_lower(stem)
                if len(low) >= 3 and low not in {"den", "dan", "ten", "tan", "nin", "nın", "şuan"}:
                    clean_words.append(low)
                    conn.execute('''
                        INSERT OR REPLACE INTO word_learning (word, acceptance_count, rejection_count, last_updated)
                        VALUES (
                            ?,
                            COALESCE((SELECT acceptance_count FROM word_learning WHERE word = ?), 0) + 1,
                            COALESCE((SELECT rejection_count FROM word_learning WHERE word = ?), 0),
                            CURRENT_TIMESTAMP
                        )
                    ''', (low, low, low))
                    self._check_and_promote_word(low, conn)

            # 2-gram ve 3-gram tamlama/cümle öbeği öğrenimi
            for n in (2, 3):
                for i in range(len(clean_words) - n + 1):
                    phrase = " ".join(clean_words[i:i+n])
                    conn.execute('''
                        INSERT OR REPLACE INTO phrase_learning (phrase, count, last_updated)
                        VALUES (
                            ?,
                            COALESCE((SELECT count FROM phrase_learning WHERE phrase = ?), 0) + 1,
                            CURRENT_TIMESTAMP
                        )
                    ''', (phrase, phrase))
        if rows:
            conn.commit()

    def process_pending_now(self):
        """Dışarıdan çağrılabilen senkron kabul ve öğrenme döngüsü."""
        with self._lock:
            conn = self._get_connection()
            try:
                self._process_pending_acceptances(conn)
            finally:
                conn.close()

    def get_frequent_phrases(self, min_count: int = 2) -> list:
        """Kullanıcının sıkça kabul ettiği 2'li ve 3'lü tamlamaları döner."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    'SELECT phrase, count FROM phrase_learning WHERE count >= ? ORDER BY count DESC LIMIT 50',
                    (min_count,)
                )
                return cursor.fetchall()
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
            word: The word or sentence that was rejected (undo'd)
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute('''
                    SELECT id, original_text FROM correction_events
                    WHERE corrected_text = ? AND user_accepted IS NULL
                    ORDER BY timestamp DESC LIMIT 1
                ''', (word,))
                ev_row = cursor.fetchone()
                orig_text = ev_row[1] if ev_row else ""

                # Update the most recent correction event for this word
                conn.execute('''
                    UPDATE correction_events
                    SET user_accepted = 0
                    WHERE corrected_text = ? AND user_accepted IS NULL
                    ORDER BY timestamp DESC LIMIT 1
                ''', (word,))

                corr_tokens = {
                    turkish_lower(re.split(r"['’]", t)[0])
                    for t in re.findall(r"[a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:['’][a-zA-ZçÇğĞıİöÖşŞüÜ]+)?", word)
                }
                orig_tokens = {
                    turkish_lower(re.split(r"['’]", t)[0])
                    for t in re.findall(r"[a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:['’][a-zA-ZçÇğĞıİöÖşŞüÜ]+)?", orig_text)
                } if orig_text else set()

                rejected_targets = (corr_tokens - orig_tokens) if (orig_tokens and corr_tokens != orig_tokens) else corr_tokens
                if not rejected_targets or " " not in word.strip():
                    rejected_targets = set(rejected_targets) | {word.strip()}

                for target_w in rejected_targets:
                    if not target_w:
                        continue
                    conn.execute('''
                        INSERT OR REPLACE INTO word_learning (word, acceptance_count, rejection_count, learned, last_updated)
                        VALUES (
                            ?,
                            COALESCE((SELECT acceptance_count FROM word_learning WHERE word = ?), 0),
                            COALESCE((SELECT rejection_count FROM word_learning WHERE word = ?), 0) + 1,
                            0,
                            CURRENT_TIMESTAMP
                        )
                    ''', (target_w, target_w, target_w))

                # Kullanıcının orijinal yazdığı özel kelime düzeltilip Ctrl+Z ile geri alındıysa orijinal kelimeyi ödüllendir
                for custom_orig in (orig_tokens - corr_tokens):
                    if len(custom_orig) >= 3:
                        conn.execute('''
                            INSERT OR REPLACE INTO word_learning (word, acceptance_count, rejection_count, last_updated)
                            VALUES (
                                ?,
                                COALESCE((SELECT acceptance_count FROM word_learning WHERE word = ?), 0) + 1,
                                COALESCE((SELECT rejection_count FROM word_learning WHERE word = ?), 0),
                                CURRENT_TIMESTAMP
                            )
                        ''', (custom_orig, custom_orig, custom_orig))
                        self._check_and_promote_word(custom_orig, conn)

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
            # Promote if: acceptance >= 2 and acceptance >= 2 * rejection
            if acceptance >= 2 and acceptance >= 2 * rejection:
                # Mark as learned
                conn.execute('''
                    UPDATE word_learning
                    SET learned = 1
                    WHERE word = ?
                ''', (word,))

                logger.info(f"Word '{word}' promoted to personal dictionary via self-learning")
                try:
                    from src.dictionary import ALL_TURKISH_WORDS, BLOCKED_SHORT_CHUNKS, add_personal_word
                    from src.slang import ALL_EXPANSIONS
                    low_w = turkish_lower(word.strip())
                    # Yalnızca ana sözlükte olmayan, TDK yazım hatası olmayan gerçek özel kelimeleri kisisel_sozluk.txt'e yaz
                    if (
                        len(low_w) >= 3
                        and low_w not in ALL_TURKISH_WORDS
                        and low_w not in ALL_EXPANSIONS
                        and low_w not in BLOCKED_SHORT_CHUNKS
                        and low_w not in {"den", "dan", "ten", "tan", "nin", "nın", "şuan"}
                    ):
                        add_personal_word(low_w)
                except Exception:
                    pass

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