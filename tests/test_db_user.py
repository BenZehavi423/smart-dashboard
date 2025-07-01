import unittest
import bcrypt
from web.models import User
from web.db_manager import MongoDBManager

class TestUserDatabase(unittest.TestCase):
    """Test basic User create, fetch and delete operations in MongoDB."""

    def setUp(self):
        # Prepare a clean DB manager before each test
        self.db = MongoDBManager()
        self.username = "testuser"
        self.email = "test@example.com"
        self.password = "MySecurePassword123"
        self.hashed_pw = bcrypt.hashpw(self.password.encode(), bcrypt.gensalt()).decode()

        self.user = User(username=self.username, email=self.email, password_hash=self.hashed_pw)
        self.user_id = self.db.create_user(self.user)

    def test_create_and_get_user(self):
        # Try fetching by username
        fetched = self.db.get_user_by_username(self.username)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched._id, self.user_id)
        self.assertEqual(fetched.email, self.email)

    def tearDown(self):
        # Cleanup the user after each test
        self.db.delete_user(self.user_id)
        self.db.client.close()

if __name__ == "__main__":
    unittest.main()
# This code is for testing the User model's database operations.
# It creates a user, fetches it by username, and cleans up after the test.
