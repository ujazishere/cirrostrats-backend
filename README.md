
# Cirrostrats Backend

A FastAPI-based backend service for flight tracking and weather data aggregation.

## Project Structure

```text
cirrostrats-backend/
├── core/                   # Core business logic
│   ├── api/               # External API integrations
│   ├── search/            # Search functionality
│   ├── tests/             # Unit tests
│   └── pkl/               # Pickle data files
├── routes/                # API route definitions
├── services/              # Business service layer
├── models/                # Data models
├── schema/                # API schemas
├── utils/                 # Utility functions
├── data/                  # Data files (JSON, pickle)
├── docs/                  # Documentation
├── notebooks/             # Jupyter notebooks (development)
├── config/                # Configuration files
├── .github/               # GitHub workflows
├── main.py               # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── Dockerfile.backend    # Docker configuration
└── .env.example         # Environment variables template
```

## Setup Options

### Option A: Docker Container (Recommended)

Full-stack deployment with frontend, backend, and nginx:

1. **Clone the base repository:** [https://github.com/Cirrostrats/base](https://github.com/Cirrostrats/base)
2. **Follow instructions in `base/README.md`**

### Option B: Backend Only (Development)

#### Prerequisites

- Python 3.8+
- MongoDB Atlas account
- FlightAware API key (optional)

#### Installation

1. **Clone this repository**

   ```bash
   git clone <repository-url>
   cd cirrostrats-backend
   ```

2. **Create environment file**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your actual configuration values.

3. **Set up Python virtual environment**

   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment**

   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

5. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

6. **Run the FastAPI server**

   ```bash
   uvicorn main:app --reload
   ```

7. **Access the application**

   The backend will be running at [http://127.0.0.1:8000](http://127.0.0.1:8000)

## MongoDB Connection Setup

1. Go to MongoDB Atlas web account page → Database Access → Create user and note username/password
2. Go to Clusters → Connect → Connecting with MongoDB for VS Code → Copy connection string
3. Insert your username and password into the connection string
4. Add the connection string to your `.env` file

## API Documentation

Once the server is running, you can access:

- **Interactive API docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Features

- Flight tracking and aggregation
- Weather data integration
- Search functionality with fuzzy matching
- Real-time notifications
- Gate information processing
- EDCT (Estimated Departure Clearance Time) lookups
