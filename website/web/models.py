from datetime import datetime
from typing import List, Dict, Any
import uuid

# uuid generates unique identifiers (if id didn't passed)


class File:
    def __init__(self, filename: str, upload_date: datetime = None, user_id: str = None, _id: str = None):
        self._id = _id or str(uuid.uuid4())
        self.filename = filename
        self.upload_date = upload_date or datetime.utcnow()
        self.user_id = user_id

    def to_dict(self) -> Dict[str, Any]:
        # Converts the File object into a plain dictionary suitable for insertion into MongoDB
        return {
            "_id": self._id,
            "filename": self.filename,
            "upload_date": self.upload_date,
            "user_id": self.user_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "File":
        # A factory method that takes a MongoDB document (a dict) and returns a File instance with the same fields.
        return cls(
            filename=data["filename"],
            upload_date=data.get("upload_date"),
            user_id=data.get("user_id"),
            _id=data.get("_id"),
        )

class Dataset:
    def __init__(self, file_id: str, records: List[Dict[str, Any]], _id: str = None):
        self._id = _id or str(uuid.uuid4())
        self.file_id = file_id
        self.records = records

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_id": self._id,
            "file_id": self.file_id,
            "records": self.records,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dataset":
        return cls(
            file_id=data["file_id"],
            records=data.get("records", []),
            _id=data.get("_id"),
        )

class AnalysisResult:
    def __init__(self, file_id: str, stats: Dict[str, Any], created_at: datetime = None, _id: str = None):
        self._id = _id or str(uuid.uuid4())
        self.file_id = file_id
        self.stats = stats
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_id": self._id,
            "file_id": self.file_id,
            "stats": self.stats,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        return cls(
            file_id=data["file_id"],
            stats=data.get("stats", {}),
            created_at=data.get("created_at"),
            _id=data.get("_id"),
        )