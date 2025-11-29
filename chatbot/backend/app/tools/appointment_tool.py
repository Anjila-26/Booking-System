import os
import re
import sqlite3
from datetime import datetime


class AppointmentTool:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of the database."""
        if self._initialized:
            return

        if self.db_path is None:
            # Use absolute path in the app directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(current_dir, "..", "appointments.db")
            self.db_path = os.path.abspath(self.db_path)
        
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir:  # Only create directory if path has a directory component
            os.makedirs(db_dir, exist_ok=True)
        
        self.init_db()
        self._initialized = True

    def init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
        except sqlite3.OperationalError as e:
            raise RuntimeError(
                f"Unable to open database file at {self.db_path}. "
                f"Error: {str(e)}. "
                "Please ensure the directory exists and is writable."
            ) from e
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                service TEXT,
                date_time TEXT,
                status TEXT DEFAULT 'pending'
            )
        """
        )
        conn.commit()
        conn.close()

    def add_appointment(self, user_id, service, date_time):
        self._ensure_initialized()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO appointments (user_id, service, date_time)
            VALUES (?, ?, ?)
        """,
            (user_id, service, date_time),
        )
        conn.commit()
        conn.close()
        return "Appointment added successfully."

    def cancel_appointment(self, appointment_id):
        self._ensure_initialized()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE appointments SET status = 'cancelled' WHERE id = ?
        """,
            (appointment_id,),
        )
        conn.commit()
        conn.close()
        return (
            "Appointment cancelled successfully."
            if cursor.rowcount > 0
            else "Appointment not found."
        )

    def reschedule_appointment(self, appointment_id, new_date_time):
        self._ensure_initialized()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE appointments SET date_time = ? WHERE id = ?
        """,
            (new_date_time, appointment_id),
        )
        conn.commit()
        conn.close()
        return (
            "Appointment rescheduled successfully."
            if cursor.rowcount > 0
            else "Appointment not found."
        )

    def get_appointments(self, user_id=None):
        self._ensure_initialized()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if user_id:
            cursor.execute(
                "SELECT * FROM appointments WHERE user_id = ?", (user_id,)
            )
        else:
            cursor.execute("SELECT * FROM appointments")
        results = cursor.fetchall()
        conn.close()
        return results

    @staticmethod
    def format_booking_id(appointment_id):
        """Format appointment ID as BOOK-{id}-{year}"""
        year = datetime.now().year
        return f"BOOK-{appointment_id:02d}-{year}"

    @staticmethod
    def extract_booking_id_from_text(text):
        """Extract booking ID from text. Returns None if not found."""
        text_lower = text.lower()
        
        # Pattern 1: BOOK-01-2025 format
        pattern1 = r'book-(\d+)-(\d+)'
        match = re.search(pattern1, text_lower)
        if match:
            return int(match.group(1))
        
        # Pattern 2: Just the number after BOOK- or # or "booking"
        pattern2 = r'(?:book-|#|booking\s*)(\d+)'
        match = re.search(pattern2, text_lower)
        if match:
            return int(match.group(1))
        
        # Pattern 3: Just a standalone number (if context suggests it's a booking ID)
        # This is less reliable, so we'll be conservative
        if 'booking' in text_lower or 'appointment' in text_lower:
            pattern3 = r'\b(\d+)\b'
            match = re.search(pattern3, text_lower)
            if match:
                return int(match.group(1))
        
        return None