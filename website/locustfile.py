from locust import HttpUser, task, between
import random
import string
import io


def random_string(length=8):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

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

