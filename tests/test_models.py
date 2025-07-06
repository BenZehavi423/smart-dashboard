import pytest
from datetime import datetime
import bcrypt
from website.web.models import File, Dataset, AnalysisResult, User

def test_file_serialization_roundtrip():
    file = File(filename="data.csv", user_id="user123")
    d = file.to_dict()
    assert "_id" in d
    assert "filename" in d
    assert "user_id" in d
    reconstructed = File.from_dict(d)
    assert reconstructed._id == file._id
    assert reconstructed.filename == file.filename
    assert reconstructed.user_id == file.user_id
    assert isinstance(reconstructed.upload_date, datetime)

def test_dataset_serialization_roundtrip():
    records = [{"a": 1}, {"b": 2}]
    dataset = Dataset(file_id="fid", records=records)
    d = dataset.to_dict()
    assert d["file_id"] == "fid"
    reconstructed = Dataset.from_dict(d)
    assert reconstructed._id == dataset._id
    assert reconstructed.records == records

def test_analysis_result_serialization_roundtrip():
    stats = {"mean": 5.5, "count": 100}
    result = AnalysisResult(file_id="fid", stats=stats)
    d = result.to_dict()
    assert d["stats"] == stats
    reconstructed = AnalysisResult.from_dict(d)
    assert reconstructed.file_id == result.file_id
    assert reconstructed.stats == stats
    assert isinstance(reconstructed.created_at, datetime)

def test_user_serialization_roundtrip():
    raw_password = "Secret123"
    hashed = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()
    user = User(username="alice", email="alice@example.com", password_hash=hashed)
    d = user.to_dict()
    assert "_id" in d
    assert "username" in d
    assert "email" in d
    assert "password_hash" in d
    reconstructed = User.from_dict(d)
    assert reconstructed._id == user._id
    assert reconstructed.username == user.username
    assert reconstructed.email == user.email
    assert reconstructed.password_hash == user.password_hash
