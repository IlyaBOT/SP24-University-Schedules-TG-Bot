import sqlite3
import tempfile
import unittest
from pathlib import Path

import schedule


class WeekSwitchTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = schedule.SETTINGS_DB_PATH
        schedule.SETTINGS_DB_PATH = Path(self.temp_dir.name) / "settings.db"

    def tearDown(self):
        schedule.SETTINGS_DB_PATH = self.original_db_path
        schedule.get_schedule_for_today_cached.cache_clear()
        self.temp_dir.cleanup()

    def test_switch_is_persistent_and_reversible(self):
        initial_week = schedule.get_current_week()

        switched_week = schedule.switch_current_week()
        self.assertNotEqual(switched_week, initial_week)
        self.assertEqual(schedule.get_current_week(), switched_week)

        with sqlite3.connect(schedule.SETTINGS_DB_PATH) as conn:
            saved_shift = conn.execute(
                "SELECT value FROM bot_settings WHERE key = ?",
                (schedule.WEEK_SHIFT_KEY,),
            ).fetchone()
        self.assertEqual(saved_shift, ("1",))

        self.assertEqual(schedule.switch_current_week(), initial_week)


if __name__ == "__main__":
    unittest.main()
