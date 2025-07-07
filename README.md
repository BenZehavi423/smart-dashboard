## Usage

Start Docker engine  
Run `docker-compose up`  
This will start the app server and MongoDB listener.

## Status

-  Registration page works and stores data in MongoDB  
-  Login process not yet implemented but login page exists
-  Tests currently run locally – `Dockerfile.tests` exists but test container setup is incomplete

## LLM API
- to use The llm you need to create a .env file.
<BR> In the file you need to write: GEMINI_API_KEY="YOUR API TOKEN FROM GEMINI API"