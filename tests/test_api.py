import os
import tempfile
import unittest
from pathlib import Path


TEMP_DIR = tempfile.TemporaryDirectory()
os.environ["DATABASE_PATH"] = str(Path(TEMP_DIR.name) / "test.db")

from app.database import initialize_database  # noqa: E402
from app.query_service import execute_readonly_query, validate_sql  # noqa: E402


class QuerySafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        initialize_database()

    def test_sales_query(self) -> None:
        result = execute_readonly_query(
            "SELECT region, COUNT(*) AS order_count FROM orders GROUP BY region"
        )
        self.assertEqual(result["row_count"], 4)

    def test_rejects_delete(self) -> None:
        with self.assertRaises(ValueError):
            validate_sql("DELETE FROM orders")

    def test_rejects_multiple_statements(self) -> None:
        with self.assertRaises(ValueError):
            validate_sql("SELECT 1; SELECT 2")


if __name__ == "__main__":
    unittest.main()
