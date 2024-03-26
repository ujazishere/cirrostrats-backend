### Backend

1. **Open Terminal:** You'll need to have 2 different terminals open.

2. **Running the Backend:**

   a. **Change Directory (CD):** Navigate into the `fast-api` directory.

   b. **Ensure Python Installation:** Make sure Python is installed on your machine.

   c. **Initialize Virtual Environment (venv):**

   ```bash
   python -m venv venv
   ```

   d. **Activate the Virtual Environment:**

   ```bash
   source venv/bin/activate
   ```

   e. **Create an env file inside of fast-api folder :**
   right click, fast api folder, select create new folder and name it '.env'
   inside of the folder create a variable named connection_string=''
   inside of the quotes add your connection string with username and password.

   f. **Install Required Packages:**

   ```bash
   pip install -r requirements.txt
   ```

   g. **Run the Server:**

   ```bash
   uvicorn main:app --reload
   ```

   h. **Access the Project:** The project will be running on [http://127.0.0.1:8000](http://127.0.0.1:8000).
