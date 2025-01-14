

# One of two ways to do this:
**A: Docker container(spools up frontend, backend and nginx using docker:) - Most efficient and Full-Featured:**

**OR**

**B: Without docker(Spool up just the backend) - Python FastAPI**


## A: Docker container(spools up frontend, backend and nginx using docker:) - Most efficient and Full-Featured:

1. **Clone the base repo:f** [https://github.com/Cirrostrats/base](https://github.com/Cirrostrats/base)

2. **Follow instructions in `base/README.md`**


## B: Without docker(Spool up just the backend - Python FastAPI)

1. **Clone this cirrostrats-backend repo**

2. **Running the Backend:**

   **`.env` contents:**
   **Create an `.env` file inside of the `cirrostrats-backend` folder :**
   **paste the following into this `.env` file, replacing the `connection_string` with your MongoDB connection string.**
      
      ```bash
      # .env (for local environment)
      connection_string='***'
      env='development'         # Use this locally. For production change it to 'production'
      ```

   a. **Ensure Python Installation:** Make sure Python is installed on your machine.


   b. **Initialize Virtual Environment (venv):** Ensure you are working in `cirrostrats-backend` directory

   ```bash
   python -m venv venv
   ```

   c. **Activate the Virtual Environment:**

   ```bash
   source venv/bin/activate
   ```

   d. **Install Required Packages:**

   ```bash
   pip install -r requirements.txt
   ```

   e. **Run the FastAPI Server:**

   ```bash
   uvicorn main:app --reload
   ```

   f. **Access the Backend Locally:** The project will be locally running at [http://127.0.0.1:8000](http://127.0.0.1:8000).


