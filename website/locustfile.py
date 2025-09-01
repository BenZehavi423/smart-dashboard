from locust import HttpUser, task, between
import random
import string
import io
import os

def random_string(length=8):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    file_id = None

    def on_start(self):
        """
        Called when a new Locust user is created.
        This function will create a new, unique user and business for each simulated user.
        """
        self.username = "user_" + random_string()
        self.password = "password123"

        self.client.post("/register", {
            "username": self.username,
            "password": self.password
        })

        self.client.post("/login", {
            "username": self.username,
            "password": self.password
        })

        self.business_name = "business-" + random_string()
        self.client.post("/new_business", {
            "name": self.business_name
        })

    @task(3)
    def view_business_page(self):
        """
        This task simulates a user viewing their business page.
        """
        self.client.get(f"/business_page/{self.business_name}", name="/business_page/[business_name]")

    @task(2)
    def upload_and_analyze(self):
        """
        This task simulates a user uploading a file and then analyzing it.
        """
        # Create a dummy CSV file in memory
        csv_content = "header1,header2\nvalue1,value2\nvalue3,value4"
        file = io.BytesIO(csv_content.encode('utf-8'))
        file.name = "test.csv"

        # Upload the file
        response = self.client.post(
            f"/upload_files/{self.business_name}",
            files={'file': file},
            name="/upload_files/[business_name]"
        )

        if response.status_code == 200 and response.json().get('success'):
            # Get the list of files to find the ID of the uploaded file
            files_response = self.client.get("/dashboard/files", name="/dashboard/files")
            if files_response.status_code == 200:
                files_data = files_response.json().get('files', [])
                if files_data:
                    # Get the most recently uploaded file
                    self.file_id = files_data[-1].get('_id')

        # If a file has been uploaded, analyze it
        if self.file_id:
            self.client.post(
                f"/analyze_data/{self.business_name}",
                json={"file_id": self.file_id, "prompt": "Create a bar chart"},
                name="/analyze_data/[business_name]"
            )

    def on_stop(self):
        """
        Called when the Locust test is stopped.
        This function will delete the user and all their associated data.
        """
        if self.username:
            self.client.post("/delete_user", name="/delete_user")