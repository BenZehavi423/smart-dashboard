from pymongo import MongoClient
from typing import Optional, Dict, Any, List
from .models import File, Dataset, AnalysisResult, User, Plot
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
        self.plots = self.db["plots"]
        self.businesses = self.db["businesses"]


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

    def get_files_for_business(self, business: Business) -> List[File]:
        """
        Returns a list of File objects uploaded by the given business.
        :param business: Business object
        :return: List of File objects
        """
        docs = self.files.find({"business_id": business._id})
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

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        updates the user in the collection
        :param user_id:
        :param updates:
        :return: True if at least one doc was modified, otherwise False
        """
        result = self.users.update_one({"_id": user_id}, {"$set": updates})
        return result.modified_count > 0
    
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
        try:
            self.plots.insert_one(plot.to_dict())
            logger.info(f"Plot created successfully: {plot.image_name}", 
                        extra_fields={'plot_id': plot._id, 'business_id': plot.business_id, 'plot_name': plot.image_name})
            return plot._id
        except Exception as e:
            logger.error(f"Failed to create plot: {plot.image_name}", 
                         extra_fields={'business_id': plot.business_id, 'plot_name': plot.image_name, 'error': str(e)})
            raise
    
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

    def get_plots_for_business(self, business_id: str, only_presented: Optional[bool] = None) -> List[Plot]:
        """
        Returns a list of Plot objects belonging to the given business
        :param business_id: ID of the business
        :param only_presented: If True, return only presented images. If False, return only not presented images. If None, return all images.
        :return: List of Plot objects
        """
        query: Dict[str, Any] = {"business_id": business_id}
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

    def get_presented_plots_for_business_ordered(self, business_name: str) -> List[Plot]:
        """
        Returns presented plots for a business ordered according to user profile
        :param business_name: Name of the business
        :return: List of Plot objects in the correct order
        """
        # Get business with plot order
        business = self.get_business_by_name(business_name)

        # Get all presented plots
        presented_plots = self.get_plots_for_business(business._id, only_presented=True)

        # Create a dictionary for quick lookup
        plots_dict = {plot._id: plot for plot in presented_plots}
        
        # Order plots according to profile order
        ordered_plots = []
        for plot_id in business.presented_plot_order:
            if plot_id in plots_dict:
                ordered_plots.append(plots_dict[plot_id])
        
        # Add any plots that are presented but not in the order list (new plots)
        for plot in presented_plots:
            if plot._id not in business.presented_plot_order:
                ordered_plots.append(plot)
        
        return ordered_plots

    def update_plot_presentation_order(self, business_name: str, plot_order: List[str]) -> bool:
        """
        Updates the presentation order of plots for a business
        :param business_name: Name of the business
        :param plot_order: List of plot IDs in the desired order
        :return: True if update was successful
        """
        try:
            logger.info(f"Updating plot presentation order for business: {business_name}", 
                        extra_fields={'business_name': business_name, 'plot_order_length': len(plot_order)})

            result = self.update_business(business_name, {"presented_plot_order": plot_order})

            if result:
                logger.info(f"Successfully updated plot presentation order for business: {business_name}")
            else:
                logger.error(f"Failed to update plot presentation order for business: {business_name}")

            return result
        except Exception as e:
            logger.error(f"Error updating plot presentation order for business: {business_name}", 
                         extra_fields={'business_name': business_name, 'error': str(e)})
            return False
    
    def update_multiple_plots(self, plot_updates: List[Dict[str, Any]]) -> bool:
        """
        Updates multiple plots at once
        :param plot_updates: List of dicts with plot_id and updates
        :return: True if all updates were successful
        """
        try:
            logger.info(f"Updating {len(plot_updates)} plots", 
                        extra_fields={'updates_count': len(plot_updates)})
            
            for update in plot_updates:
                plot_id = update["plot_id"]
                updates = {k: v for k, v in update.items() if k != "plot_id"}
                self.plots.update_one({"_id": plot_id}, {"$set": updates})
                
                logger.debug(f"Plot updated: {plot_id}", 
                             extra_fields={'plot_id': plot_id, 'updates': updates})
            
            logger.info(f"Successfully updated {len(plot_updates)} plots")
            return True
        except Exception as e:
            logger.error(f"Failed to update multiple plots", 
                         extra_fields={'updates_count': len(plot_updates), 'error': str(e)})
            return False

# ----- BUSINESS OPERATIONS -----
    def create_business(self, business: Business) -> str:
        """
        Creates a new business entry
        :param business: Business object representing the business
        :return: Business id
        """
        self.businesses.insert_one(business.to_dict())
        return business._id

    def get_business_by_id(self, business_id: str) -> Optional[Business]:
        """
        Retrieves a business by its ID
        :param business_id: ID of the business
        :return: Business object if found, None otherwise
        """
        data = self.businesses.find_one({"_id": business_id})
        return Business.from_dict(data) if data else None

    def get_business_by_name(self, business_name: str) -> Optional[Business]:
        """
        Retrieves a business by its name
        :param business_name: Name of the business
        :return: Business object if found, None otherwise
        """
        data = self.businesses.find_one({"name": business_name})
        return Business.from_dict(data) if data else None

    def update_business(self, business_id: str, updates: Dict[str, Any]) -> bool:
        """
        Updates a business entry
        :param business_id: ID of the business to update
        :param updates: Dictionary of fields to update
        :return: True if at least one doc was modified, otherwise False
        """
        result = self.businesses.update_one({"_id": business_id}, {"$set": updates})
        return result.modified_count > 0

    def delete_business(self, business_id: str) -> bool:
        """
        Deletes a business entry
        :param business_id: ID of the business to delete
        :return: True if at least one doc was deleted, otherwise False
        """
        result = self.businesses.delete_one({"_id": business_id})
        return result.deleted_count > 0

    def get_businesses_for_owner(self, owner_id: str) -> List[Business]:
        """
        Retrieves all businesses owned by a specific user
        :param owner_id: ID of the owner
        :return: List of Business objects
        """
        businesses = self.businesses.find({"owner": owner_id})
        return [Business.from_dict(d) for d in businesses]
