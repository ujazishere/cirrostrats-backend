# Copyright (c) 2025 Cirrostrats.
# Licensed under the Elastic License 2.0.
# See LICENSE.txt for details.



"""
Cirrostrats Backend - FastAPI Application Entry Point

COMPREHENSIVE PROJECT RESTRUCTURING (October 2025):
This application underwent a complete cleanup and restructuring to follow FastAPI best practices
and improve overall project organization, maintainability, and developer experience.

MAJOR CHANGES IMPLEMENTED:

1. DIRECTORY STRUCTURE REORGANIZATION:
   - Created data/ directory for all general data files (JSON, pickle files)
   - Created notebooks/ directory for Jupyter development notebooks  
   - Created docs/ directory for documentation and project notes
   - Maintained existing core/, routes/, services/, models/, schema/, utils/ structure

2. DATA FILE ORGANIZATION:
   - Moved 7 data files from root to data/ directory:
     * airports.json, all_US_airports_dict.pkl, bulk_weather_returns_mock.pkl
     * forMDB.pkl, mock_ajms_data.pkl, publicuj_searches_unique_sorts.pkl, unique_icao.pkl
   - Kept core-specific data files in core/pkl/ for logical separation
   - Clear distinction: general data (data/) vs core functionality data (core/pkl/)

3. PATH UPDATES ACROSS CODEBASE:
   - Updated 8+ files with hardcoded or incorrect paths
   - Changed from absolute paths to relative paths for portability
   - Fixed case-sensitive filename issues (ForMDB.pkl -> forMDB.pkl)
   - Added comprehensive comments explaining all path changes

4. DEVELOPMENT ARTIFACTS ORGANIZATION:
   - Moved Jupyter notebooks to notebooks/ directory with usage documentation
   - Removed unnecessary batch files (dcub.bat)
   - Kept important development notebooks (edct-poc.ipynb, mongo.ipynb, etc.)

5. DOCUMENTATION IMPROVEMENTS:
   - Added .env.example template for environment variables
   - Created comprehensive README.md with project structure
   - Added RESTRUCTURING_LOG.md documenting all changes
   - Fixed all markdown linting issues

6. IMPORT PATH MIGRATION:
   - Provided migration guide for notebook imports
   - Created helper scripts for path updates
   - Documented all required changes for development workflow

BENEFITS ACHIEVED:
- Professional project structure following industry best practices
- Improved portability across different environments and developers
- Better separation of concerns (data, code, documentation, development)
- Enhanced maintainability and onboarding experience
- Production-ready deployment structure
- Clear audit trail of all changes made

FILES MODIFIED: 8 core files updated, 4 new files created, 1 file removed
IMPACT: Significantly improved project organization without breaking functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
from routes.route import register_routes

app = FastAPI()

origins = [
    "http://localhost:5173",
    "https://your-ngrok-url.ngrok-free.app",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routes(app)

@app.get("/")
def root():
    return {"message": "Hello World"}
