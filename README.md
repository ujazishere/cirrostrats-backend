### Backend


### Can be spooled up by using one of two ways:

## Docker container(spools up frontend, backend and nginx):
1. **Clone the base repo:f** https://github.com/Cirrostrats/base

2. **Clone backend and the frontend repos within the base repo**

3. **Create an env file inside of the cirrostrats-backend folder :**

   Create new file and name it '.env'
   inside of the file create a variable named connection_string=''
   inside of the quotes add your connection string with username and password for the mongo db.

4. **Run docker compose command to build and run the container:**

   ```docker-compose up --build```

## Without Docker(Just backend):

1. **Open Terminal:** You'll need to open the terminal via your computer or visual code

2. **Running the Backend:**

   a. **Ensure Python Installation:** Make sure Python is installed on your machine.


   b. **Initialize Virtual Environment (venv):**

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

   e. **Run the Server:**

   ```bash
   uvicorn main:app --reload
   ```

   f. **Browser acess of the backend:** The project will be running on [http://127.0.0.1:8000](http://127.0.0.1:8000).

   g. **Accessing the frontend Project:** frontend for this project is at: https://github.com/ujazishere/cirrostrats-frontend
