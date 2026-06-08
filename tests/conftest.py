import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    # Force TESTING environment variable before any modules are imported
    os.environ["TESTING"] = "true"
    yield
    
    # Clean up test database file at the end of the test session
    import src.database as db
    if os.path.exists(db.DB_PATH):
        try:
            os.remove(db.DB_PATH)
            print(f"\n[Teardown] Successfully removed test database: {db.DB_PATH}")
        except Exception as e:
            print(f"\n[Teardown] Error removing test database: {e}")
