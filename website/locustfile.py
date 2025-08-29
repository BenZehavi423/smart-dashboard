from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)  # Simulate a user waiting 1-5 seconds between tasks

    def on_start(self):
        """
        This method is called when a new user is simulated.
        It simulates the login process.
        """
        self.client.post("/login", {
            "username": "testuser",
            "password": "password"
        })

    @task
    def view_profile(self):
        """
        This task simulates a user viewing their profile page.
        """
        self.client.get("/profile")

    @task
    def view_business_page(self):
        """
        This task simulates a user viewing a business page.
        """
        # Replace 'test-business' with a business name that exists in your database
        self.client.get("/business_page/test-business")

    @task
    def generate_plot(self):
        """
        This task simulates a user generating a plot. This is a good
        endpoint to stress test as it involves the LLM.
        """
        # Replace with a valid file_id from your database
        file_id = "your_file_id_here"

        self.client.post("/analyze_data/test-business", json={
            "file_id": file_id,
            "prompt": "Create a bar chart of sales"
        })