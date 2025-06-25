from pymongo import MongoClient
from typing import Optional, Dict, Any, List
from web.models import File, Dataset, AnalysisResult

class MongoDBManager:
    def __init__(self, uri: str = "mongodb://localhost:27017", db_name: str = "mydb"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.files = self.db["files"]
        self.datasets = self.db["datasets"]
        self.analysis = self.db["analysis_results"]

    def create_file(self, file: File) -> str:
        """
        writes the dict to the collection and Returns the document’s id so callers can keep track.
        :param file:
        :return:File id
        """
        self.files.insert_one(file.to_dict())
        return file._id

    def create_dataset(self, ds: Dataset) -> str:
        """
        writes the dataset to the collection and Returns the ds id
        :param ds:
        :return: ds id
        """
        self.datasets.insert_one(ds.to_dict())
        return ds._id

    def create_analysis(self, ar: AnalysisResult) -> str:
        """
        writes the analysis result to the collection and Returns the analysis result id
        :param ar:
        :return: analysis result id
        """
        self.analysis.insert_one(ar.to_dict())
        return ar._id

    def get_file(self, file_id: str) -> Optional[File]:
        """
        gets the file from the collection
        :param file_id:
        :return: None if not found, otherwise rehydrates into a File object.
        """
        data = self.files.find_one({"_id": file_id})
        return File.from_dict(data) if data else None

    def get_datasets_for_file(self, file_id: str) -> List[Dataset]:
        """
        gets the dataset from the collection
        :param file_id:
        :return: a cursor of all matching docs; convert each to a Dataset.
        """
        docs = self.datasets.find({"file_id": file_id})
        return [Dataset.from_dict(d) for d in docs]

    def get_analysis_for_file(self, file_id: str) -> List[AnalysisResult]:
        """
        gets the analysis result from the collection
        :param file_id:
        :return: a cursor of all matching docs; convert each to a AnalysisResult.
        """
        docs = self.analysis.find({"file_id": file_id})
        return [AnalysisResult.from_dict(d) for d in docs]

    def update_file(self, file_id: str, updates: Dict[str, Any]) -> bool:
        """
        check for if file was updated or not
        :param file_id:
        :param updates:
        :return: True if at least one doc was modified, otherwise False
        """
        result = self.files.update_one({"_id": file_id}, {"$set": updates})
        return result.modified_count > 0

    def delete_file(self, file_id: str) -> bool:
        result = self.files.delete_one({"_id": file_id})
        return result.deleted_count > 0

    def delete_dataset(self, ds_id: str) -> bool:
        result = self.datasets.delete_one({"_id": ds_id})
        return result.deleted_count > 0

    def delete_analysis(self, ar_id: str) -> bool:
        result = self.analysis.delete_one({"_id": ar_id})
        return result.deleted_count > 0