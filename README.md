### Backend

1. **Open Terminal:** You'll need to open the terminal via your computer or visual code

2. **Running the Backend:**

   a. **Ensure Python Installation:** Make sure Python is installed on your machine.

   b. **Create an env file inside of fast-api folder :**
   right click, fast api folder, select create new folder and name it '.env'
   inside of the folder create a variable named connection_string=''
   inside of the quotes add your connection string with username and password.

   c. **Initialize Virtual Environment (venv):**

   ```bash
   python -m venv venv
   ```

   d. **Activate the Virtual Environment:**

   ```bash
   source venv/bin/activate
   ```

   e. **Install Required Packages:**

   ```bash
   pip install -r requirements.txt
   ```

   f. **Run the Server:**

   ```bash
   uvicorn main:app --reload
   ```

   g. **Access the Project:** The project will be running on [http://127.0.0.1:8000](http://127.0.0.1:8000).
   h. **Access the Project:** frontend for this project is at:https://github.com/luisarevalo21/cirrostrats-frontend
