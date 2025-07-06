from pymongo import MongoClient
from typing import Optional, Dict, Any, List
from .models import File, Dataset, AnalysisResult, User, UserProfile, Plot
from .logger import logger

class MongoDBManager:
    def __init__(self, uri: str = "mongodb://db:27017", db_name: str = "mydb"):
        # When running inside Docker, 'db' refers to the MongoDB container as defined in docker-compose.yml.
        # To run locally without Docker, change 'db' to 'localhost' (i.e., use "mongodb://localhost:27017")
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.files = self.db["files"]
        self.datasets = self.db["datasets"]
        self.analysis = self.db["analysis_results"]
        self.users = self.db["users"]
        self.user_profiles = self.db["user_profiles"]
        self.plots = self.db["plots"]


# ----- FILE OPERATIONS -----
    def create_file(self, file: File) -> str:
        """
        writes the dict to the collection and Returns the document’s id so callers can keep track.
        :param file:
        :return:File id
        """
        self.files.insert_one(file.to_dict())
        return file._id
    
    def get_file(self, file_id: str) -> Optional[File]:
        """
        gets the file from the collection
        :param file_id:
        :return: None if not found, otherwise rehydrates into a File object.
        """
        data = self.files.find_one({"_id": file_id})
        return File.from_dict(data) if data else None
    
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
    
    def get_files_for_user(self, user: User) -> List[File]:
        """
        Returns a list of File objects uploaded by the given user.
        :param user: User object
        :return: List of File objects
        """
        docs = self.files.find({"user_id": user._id})
        return [File.from_dict(d) for d in docs]

    
# ----- DATASET OPERATIONS -----

    def create_dataset(self, ds: Dataset) -> str:
        """
        writes the dataset to the collection and Returns the ds id
        :param ds:
        :return: ds id
        """
        self.datasets.insert_one(ds.to_dict())
        return ds._id
    
    def get_datasets_for_file(self, file_id: str) -> List[Dataset]:
        """
        gets the dataset from the collection
        :param file_id:
        :return: a cursor of all matching docs; convert each to a Dataset.
        """
        docs = self.datasets.find({"file_id": file_id})
        return [Dataset.from_dict(d) for d in docs]

    def delete_dataset(self, ds_id: str) -> bool:
        result = self.datasets.delete_one({"_id": ds_id})
        return result.deleted_count > 0
    
 # ----- ANALYSIS OPERATIONS -----   
    def create_analysis(self, ar: AnalysisResult) -> str:
        """
        writes the analysis result to the collection and Returns the analysis result id
        :param ar:
        :return: analysis result id
        """
        self.analysis.insert_one(ar.to_dict())
        return ar._id


    def get_analysis_for_file(self, file_id: str) -> List[AnalysisResult]:
        """
        gets the analysis result from the collection
        :param file_id:
        :return: a cursor of all matching docs; convert each to a AnalysisResult.
        """
        docs = self.analysis.find({"file_id": file_id})
        return [AnalysisResult.from_dict(d) for d in docs]


    def delete_analysis(self, ar_id: str) -> bool:
        result = self.analysis.delete_one({"_id": ar_id})
        return result.deleted_count > 0
    
# ----- USER OPERATIONS -----
    def create_user(self, user: User) -> str:
        """
        writes the user to the collection and Returns the user id
        :param user:
        :return: user id
        """
        self.users.insert_one(user.to_dict())
        return user._id

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        gets the user from the collection
        :param username:
        :return: None if not found, otherwise rehydrates into a User object.
        """
        data = self.users.find_one({"username": username})
        return User.from_dict(data) if data else None
    
    def delete_user(self, user_id: str) -> bool:
        """
        deletes the user from the collection
        :param user_id:
        :return: True if at least one doc was deleted, otherwise False
        """
        result = self.users.delete_one({"_id": user_id})
        return result.deleted_count > 0

# ----- PLOT OPERATIONS -----
    def create_plot(self, plot: Plot) -> str:
        """
        Saves the plot to the collection and returns the plot id
        :param plot: Plot object to save
        :return: plot id
        """
        self.plots.insert_one(plot.to_dict())
        return plot._id
    
    def get_plot(self, plot_id: str) -> Optional[Plot]:
        """
        Gets the plot from the collection
        :param plot_id: ID of the plot to retrieve
        :return: None if not found, otherwise rehydrates into a Plot object
        """
        data = self.plots.find_one({"_id": plot_id})
        return Plot.from_dict(data) if data else None
    
    def delete_plot(self, plot_id: str) -> bool:
        """
        Deletes the plot from the collection
        :param plot_id: ID of the plot to delete
        :return: True if at least one doc was deleted, otherwise False
        """
        result = self.plots.delete_one({"_id": plot_id})
        return result.deleted_count > 0
    
    def get_plots_for_user(self, user_id: str, only_presented: Optional[bool] = None) -> List[Plot]:
        """
        Returns a list of Plot objects belonging to the given user
        :param user_id: ID of the user
        :param only_presented: If True, return only presented images. If False, return only not presented images. If None, return all images.
        :return: List of Plot objects
        """
        query: Dict[str, Any] = {"user_id": user_id}
        if only_presented is not None:
            query["is_presented"] = only_presented
        
        docs = self.plots.find(query)
        return [Plot.from_dict(d) for d in docs]
    
    def present_plot(self, plot_id: str, is_presented: bool) -> bool:
        """
        Updates the is_presented field of a plot
        :param plot_id: ID of the plot to update
        :param is_presented: Boolean value to set
        :return: True if at least one doc was modified, otherwise False
        """
        result = self.plots.update_one({"_id": plot_id}, {"$set": {"is_presented": is_presented}})
        return result.modified_count > 0