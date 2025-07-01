import unittest
from datetime import datetime
import bcrypt
from web.models import File, Dataset, AnalysisResult, User

class TestModelSerialization(unittest.TestCase):
    """Tests for round-trip serialization and deserialization of model objects."""

    def test_file_serialization_roundtrip(self):
        # Create a File object with minimal fields
        file = File(filename="data.csv", user_id="user123")
        d = file.to_dict()

        # Ensure essential fields exist in the serialized dict
        self.assertIn("_id", d)
        self.assertIn("filename", d)
        self.assertIn("user_id", d)

        # Deserialize and compare fields
        reconstructed = File.from_dict(d)
        self.assertEqual(reconstructed._id, file._id)
        self.assertEqual(reconstructed.filename, file.filename)
        self.assertEqual(reconstructed.user_id, file.user_id)
        self.assertIsInstance(reconstructed.upload_date, datetime)

    def test_dataset_serialization_roundtrip(self):
        # Dataset should retain list of records after round-trip
        records = [{"a": 1}, {"b": 2}]
        dataset = Dataset(file_id="fid", records=records)
        d = dataset.to_dict()

        self.assertEqual(d["file_id"], "fid")

        # Deserialize and verify records
        reconstructed = Dataset.from_dict(d)
        self.assertEqual(reconstructed._id, dataset._id)
        self.assertEqual(reconstructed.records, records)

    def test_analysis_result_serialization_roundtrip(self):
        # Check preservation of stats and timestamp
        stats = {"mean": 5.5, "count": 100}
        result = AnalysisResult(file_id="fid", stats=stats)
        d = result.to_dict()

        self.assertEqual(d["stats"], stats)

        # Deserialize and verify all fields
        reconstructed = AnalysisResult.from_dict(d)
        self.assertEqual(reconstructed.file_id, result.file_id)
        self.assertEqual(reconstructed.stats, stats)
        self.assertIsInstance(reconstructed.created_at, datetime)

    def test_user_serialization_roundtrip(self):
        # Create hashed password and build User object
        raw_password = "Secret123"
        hashed = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()
        user = User(username="alice", email="alice@example.com", password_hash=hashed)
        d = user.to_dict()

        # Ensure all necessary fields are present
        self.assertIn("_id", d)
        self.assertIn("username", d)
        self.assertIn("email", d)
        self.assertIn("password_hash", d)

        # Deserialize and verify
        reconstructed = User.from_dict(d)
        self.assertEqual(reconstructed._id, user._id)
        self.assertEqual(reconstructed.username, user.username)
        self.assertEqual(reconstructed.email, user.email)
        self.assertEqual(reconstructed.password_hash, user.password_hash)


if __name__ == "__main__":
    unittest.main()
