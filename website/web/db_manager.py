from pymongo import MongoClient
from typing import Optional, Dict, Any, List
from .models import File, Dataset, AnalysisResult, User, Plot, Business
from .logger import logger
from datetime import datetime

class MongoDBManager:
    def __init__(self, uri: str = "mongodb://db:27017", db_name: str = "mydb"):
        # When running inside Docker, 'db' refers to the MongoDB container as defined in docker-compose.yml.
        # To run locally without Docker, change 'db' to 'localhost' (i.e., use "mongodb://localhost:27017")
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.files = self.db["files"]
        self.analysis = self.db["analysis_results"]
        self.users = self.db["users"]
        self.plots = self.db["plots"]
        self.businesses = self.db["businesses"]
        self.dashboards = self.db["dashboards"]



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
    
    def get_any_file(self) -> Optional[File]:
        """
        Return any File document from the collection (first match), or None if empty.
        """
        doc = self.files.find_one({})
        return File.from_dict(doc) if doc else None

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

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        gets the user from the collection by user ID
        :param user_id:
        :return: None if not found, otherwise rehydrates into a User object.
        """
        data = self.users.find_one({"_id": user_id})
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
            logger.info(f"Updating plot presentation order for business ID: {business_id}",
                        extra_fields={'business_id': business_id, 'plot_order_length': len(plot_order)})

            result = self.update_business(business_id, {"presented_plot_order": plot_order})

            if result:
                logger.info(f"Successfully updated plot presentation order for business: {business_name}")
            else:
                logger.warning(f"Plot presentation order update was acknowledged but did not modify the document for business ID: {business_id}")

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
        return result.acknowledged

    def delete_business(self, business_id: str) -> bool:
        """
        Deletes a business entry anf all associated data
        :param business_id: ID of the business to delete
        :return: True if at least one doc was deleted, otherwise False
        """
        # Delete all files associated with the business
        files_result = self.files.delete_many({"business_id": business_id})
        logger.info(f"Deleted {files_result.deleted_count} files for business {business_id}")

        # Step 2: Delete all plots associated with the business
        plots_result = self.plots.delete_many({"business_id": business_id})
        logger.info(f"Deleted {plots_result.deleted_count} plots for business {business_id}")

        # Step 3: Delete the business itself
        business_result = self.businesses.delete_one({"_id": business_id})
        logger.info(f"Deleted {business_result.deleted_count} business entry for {business_id}")

        return business_result.deleted_count > 0

    def get_businesses_for_owner(self, owner_id: str) -> List[Business]:
        """
        Retrieves all businesses owned by a specific user
        :param owner_id: ID of the owner
        :return: List of Business objects
        """
        businesses = self.businesses.find({"owner": owner_id})
        return [Business.from_dict(d) for d in businesses]

    def get_businesses_for_editor(self, editor_id: str) -> List[Business]:
        """
        Retrieves all businesses a specific user is an editor for.
        :param editor_id: ID of the user
        :return: List of Business objects
        """
        # The 'editors' field is an array, so we query for documents
        # where the editor_id is in the 'editors' array.
        businesses = self.businesses.find({"editors": editor_id})
        return [Business.from_dict(d) for d in businesses]

    def save_plot_changes_for_business(self, business_id: str, plot_updates: List[Dict[str, Any]],
                                       plot_order: List[str]) -> bool:
        """
        Atomically saves all changes for the 'Edit Plots' page for a specific business.
        :param business_id: The ID of the business being updated.
        :param plot_updates: A list of dictionaries, each with 'plot_id' and 'is_presented'.
        :param plot_order: A list of plot IDs in the new desired order.
        :return: True if all operations were acknowledged.
        """
        try:
            # Update the is_presented status for each plot
            for update in plot_updates:
                plot_id = update["plot_id"]
                is_presented = update["is_presented"]
                self.plots.update_one({"_id": plot_id}, {"$set": {"is_presented": is_presented}})

            # Update the plot order on the business document
            business_update_result = self.businesses.update_one(
                {"_id": business_id},
                {"$set": {"presented_plot_order": plot_order}}
            )

            return business_update_result.acknowledged

        except Exception as e:
            logger.error(f"Error saving plot changes for business {business_id}: {e}")
            return False

    def get_businesses_as_editor(self, user_id: str) -> List[Business]:
        """
        Retrieves all businesses where a user is an editor but not the owner.
        :param user_id: ID of the user
        :return: List of Business objects
        """
        query = {
            "editors": user_id,
            "owner": {"$ne": user_id}
        }
        businesses = self.businesses.find(query)
        return [Business.from_dict(d) for d in businesses]


