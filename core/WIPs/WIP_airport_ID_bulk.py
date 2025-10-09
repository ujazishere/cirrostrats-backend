"""
Airport ID Bulk Processing Utility (Work In Progress)

PROJECT RESTRUCTURING IMPACT (October 2025):
This WIP file was comprehensively updated during the project cleanup to use the new organized directory structure.

ORIGINAL PROBLEMS:
1. Used Django-specific paths: 'dj_app/root/pkl/' and 'dj/dj_app/root/pkl/'
2. Paths were environment-specific and wouldn't work in standalone FastAPI setup
3. Data files were scattered without clear organization
4. Mixed general data files with core-specific functionality files

CHANGES MADE:
1. Updated all_US_airports_dict.pkl paths to point to new data/ directory
2. Updated airport_identifiers_US.pkl paths to point to core/pkl/ directory
3. Changed from Django-specific paths to relative paths
4. Added comprehensive documentation explaining the restructuring

WHY THESE CHANGES:
- Separated general data files (data/) from core-specific files (core/pkl/)
- Made paths work in both Django and standalone FastAPI environments
- Improved project organization following best practices
- Made the code more maintainable and portable
- Clear separation of concerns: general data vs core functionality data

PATH LOGIC EXPLANATION:
- General data (all_US_airports_dict.pkl): Moved to data/ directory
  * From core/WIPs/ to data/: ../../data/ (up 2 levels, then into data/)
- Core-specific data (airport_identifiers_US.pkl): Stays in core/pkl/
  * From core/WIPs/ to core/pkl/: ../pkl/ (up 1 level, then into pkl/)

This dual approach ensures:
- General datasets are centralized and easily accessible
- Core functionality data remains close to the code that uses it
- Both Django and FastAPI environments can access the files
"""

import pickle
import os

# PROJECT RESTRUCTURING NOTES (October 2025):
# This file was updated during project cleanup to use new organized directory structure
# All general data files moved to data/ directory, core-specific files remain in core/pkl/

# WARNING: TO OPEN FILE, DJANGO IS USING /WEATHER_WORK/DJ AS WORKING DIRECTORY WHEREAS THE RAW FILE IS USING /CIRROSTRATS 

# print(os.getcwd())

# .keys() in the dict are states and the value is a list.
# This list contains 2 items.
    # first one is the link(a string) and other is the list of all airports of that state
# Example: {'Florida': ['https:link.com', ['ZPH - Zephyrhills Municipal' , 'KDAB - Daytona airport']]}

# RESTRUCTURING UPDATE: Paths updated to reflect new directory structure
# General data files (all_US_airports_dict.pkl) moved to data/ directory
# Core-specific files (airport_identifiers_US.pkl) remain in core/pkl/ directory
# Old paths: 'dj_app/root/pkl/' and 'dj/dj_app/root/pkl/'
# New paths: Use relative paths from current file location

# Use following variables depending on the use case;
django_path = '../../data/all_US_airports_dict.pkl'  # From core/WIPs/ to data/
external_path = '../../data/all_US_airports_dict.pkl'  # From core/WIPs/ to data/

django_path_id = '../pkl/airport_identifiers_US.pkl'  # From core/WIPs/ to core/pkl/
external_path_id = '../pkl/airport_identifiers_US.pkl'  # From core/WIPs/ to core/pkl/

# COMMENTED OUT: Django-specific airport data loading
# This was the original approach for loading all US airports dictionary
# with open(django_path, 'rb') as f:
    # airports = pickle.load(f)

# ACTIVE PICKLE FILE PROCESSING: Airport Identifiers (3-letter codes)
# 
# WHAT THIS DOES:
# - Loads airport_identifiers_US.pkl containing ~20,296 airport IDs
# - Filters for 3-letter airport codes only (IATA format)
# - Creates a list of 3-letter identifiers for further processing
#
# FILE DETAILS:
# - Source: core/pkl/airport_identifiers_US.pkl (core-specific data)
# - Content: List of airport identifiers in various formats ['DAB', 'EWR', 'X50', 'AL44', etc.]
# - Purpose: Used for bulk airport ID processing and validation
#
# RESTRUCTURING NOTE:
# - This file stayed in core/pkl/ (not moved to data/) because it's tightly coupled
#   with core airport processing functionality, unlike general data files
#
# PROCESSING LOGIC:
# - Load all airport identifiers from pickle file
# - Filter to keep only 3-character codes (standard IATA format)
# - Store in id_3_letter list for downstream processing
id_3_letter = []
with open(external_path_id, 'rb') as f:
    id = pickle.load(f)  # Load ~20,296 airport IDs from core/pkl/airport_identifiers_US.pkl
    
# Filter for 3-letter airport codes only (IATA standard)
for i in id:
    if len(i) == 3:
        id_3_letter.append(i)
        
print(f"Filtered {len(id_3_letter)} three-letter airport codes from {len(id)} total identifiers")


# ['florida'][0] refers to link, ['florida'][1] refers to all the airports. ['florida'][1][0] refers to the first airport
# print(((airports['Florida'][1][100])))
