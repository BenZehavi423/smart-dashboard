from datetime import datetime
from website.web import File, Dataset, AnalysisResult

def test_file_serialization_roundtrip():
    """
    Create an instance with minimal args.
    Serialize to dict, check required keys are present.
    Deserialize back to an object, then assert all fields match.
    """
    orig = File(filename="data.csv", user_id="user123")
    d = orig.to_dict()
    assert "_id" in d and "filename" in d and "user_id" in d

    reconstructed = File.from_dict(d)
    assert reconstructed._id == orig._id
    assert reconstructed.filename == orig.filename
    assert reconstructed.user_id == orig.user_id
    assert isinstance(reconstructed.upload_date, datetime)

def test_dataset_serialization_roundtrip():
    """
    Verifies that you can round-trip a list of records without loss.
    """
    records = [{"a": 1}, {"b": 2}]
    orig = Dataset(file_id="fid", records=records)
    d = orig.to_dict()
    assert d["file_id"] == "fid"

    reconstructed = Dataset.from_dict(d)
    assert reconstructed._id == orig._id
    assert reconstructed.records == records

def test_analysis_result_serialization_roundtrip():
    """
    Confirms that both custom data (stats) and timestamps come through intact.
    """
    stats = {"mean": 5.5, "count": 100}
    orig = AnalysisResult(file_id="fid", stats=stats)
    d = orig.to_dict()
    assert d["stats"] == stats

    reconstructed = AnalysisResult.from_dict(d)
    assert reconstructed.file_id == orig.file_id
    assert reconstructed.stats == stats
    assert isinstance(reconstructed.created_at, datetime)