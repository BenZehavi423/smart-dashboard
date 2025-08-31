# SmartDashboard: AI-Powered Business Intelligence

SmartDashboard is a comprehensive web application designed to help business owners and their teams turn raw data into actionable insights. By leveraging the power of AI, users can upload their business data, generate intelligent summaries, and create custom visualizations, all within a secure, multi-user environment.

## ✨ Features

* **Secure User Authentication**: Users can sign up and log in to a secure environment, with all passwords hashed for maximum security.
* **Business-Centric Organization**: Users can create and manage multiple businesses, each with its own set of data, plots, and editors.
* **Collaborative Editing**: Business owners can invite other users as "editors," allowing for seamless collaboration on business data and visualizations.
* **AI-Powered Plot Generation**: Users can generate custom plots and visualizations from their data by simply describing what they want to see in plain English.
* **Real-Time Editing Lock**: To prevent conflicts, our application uses WebSockets to ensure that only one user can edit a business's plots at a time.
* **Robust and Scalable Backend**: Built with a modern, containerized architecture using Docker, Flask, and MongoDB, our application is designed to be both scalable and resilient.

## 🚀 Running the Application

To run SmartDashboard, you will need to have Docker and Docker Compose installed on your system.

**1. Clone the Repository**
```bash
git clone <your-repository-url>
cd <your-repository-name>u need to write: GEMINI_API_KEY="YOUR API TOKEN FROM GEMINI API"
```

**2. Create the Environment File** <br>
Create a file named .env in the root of the project and add your Gemini API key:
```bash
GEMINI_API_KEY="YOUR_API_TOKEN_HERE"
```
**3. Run with Docker Compose**
From the root of the project, run the following command:
```bash
docker-compose up --build
```
This will build the necessary Docker images and start all the services. The web application will be available at http://localhost:5000.

**🧪 Running the Tests**<br>
*Need to implement* 