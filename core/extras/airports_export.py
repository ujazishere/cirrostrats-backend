"""
Airport Data Export Utility

PROJECT RESTRUCTURING IMPACT (October 2025):
This file was significantly updated during the comprehensive project cleanup and restructuring.

ORIGINAL PROBLEM:
- Used hardcoded absolute path: r'C:\Users\ujasv\OneDrive\Desktop\codes\cirrostrats-backend\all_US_airports_dict.pkl'
- Path was user-specific and non-portable
- Data files were scattered in root directory with no organization

CHANGES MADE:
1. Updated path from hardcoded absolute to relative path
2. Path changed to point to new data/ directory: '../../data/all_US_airports_dict.pkl'
3. Added comprehensive documentation explaining the change

WHY THESE CHANGES:
- Removed user-specific hardcoded paths that wouldn't work on other machines
- Centralized all data files in organized data/ directory
- Made the project portable across different environments and developers
- Followed FastAPI best practices for project structure
- Improved maintainability and professional appearance

PATH LOGIC:
- From: core/extras/ directory (this file's location)
- To: data/ directory (new centralized data location)  
- Relative path: ../../data/ (up 2 levels to root, then into data/)

The restructuring ensures this utility can find airport data regardless of:
- Operating system (Windows/Mac/Linux)
- User directory structure
- Project location on filesystem
"""

import json
import pickle
import re
import os

"""
Dumps all US airports from a pickle file allegedly. 
this is the source structure key as state : value as [link, [airport_1, airport_2, airport_3]]
example:
{'Alabama': ['https://skyvector.com/airports/United%20States/Alabama',
  ['TOI - Troy Municipal At N Kenneth Campbell Field Airport',

final return is a list of dictionaries with id, name and code
the label code would be better used as either ICAO or IATA
"""

# RESTRUCTURING UPDATE: Dynamic path resolution for maximum compatibility
# pointing to the new data/ directory where all general data files were moved
# during project cleanup (October 2025)
# Old path: r'C:\Users\ujasv\OneDrive\Desktop\codes\cirrostrats-backend\all_US_airports_dict.pkl'
# New approach: Dynamic path that works regardless of execution context

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate to project root and into data directory
data_path = os.path.join(script_dir, '..', '..', 'data', 'all_US_airports_dict.pkl')
# Normalize the path for cross-platform compatibility
airports = os.path.normpath(data_path)
with open(airports, 'rb') as f:
    x = pickle.load(f)

xx = []
for a,b in x.items():
    US_state = a
    cities = b[1]
    for each_city in cities:
        xx.append(each_city)

airport_dict = {}
for i in xx:
    
    first_dash_index = re.search(r'-', i).start()
    
    # Splitting the string by the first dash
    first_part = i[:first_dash_index][:-1]
    second_part = i[first_dash_index + 1:][1:]
    
    airport_dict.update({first_part:second_part})

airport_list = []
for airport_id, airport_name in airport_dict.items():
    airport_data = {
        'id': airport_id,
        'name': airport_name,
        'code': airport_id  # Assuming the code is the same as the airport ID
    }
    airport_list.append(airport_data)


with open('airports_dump.json','w') as f:
    json.dump(airport_dict,f)