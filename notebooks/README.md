# Development Notebooks

This directory contains Jupyter notebooks used for development, experimentation, and proof-of-concept work.

## Notebooks

- **`Misc.ipynb`** - General development and testing notebook
- **`edct-poc.ipynb`** - EDCT (Estimated Departure Clearance Time) proof of concept
- **`mongo.ipynb`** - MongoDB database testing and experimentation
- **`search-index.ipynb`** - Search functionality development and testing

## Usage

These notebooks are used for:

- Prototyping new features
- Testing database queries
- Experimenting with algorithms
- Data analysis and exploration
- API testing and validation

## Setup

To run these notebooks:

1. Install Jupyter in your virtual environment:

   ```bash
   pip install jupyter
   ```

2. Start Jupyter from the project root:

   ```bash
   jupyter notebook
   ```

3. Navigate to the `notebooks/` directory in the Jupyter interface

## Path Updates Required

**IMPORTANT:** After moving notebooks to this directory, the import paths need to be updated in each notebook:

### Required Import Path Changes

**Old imports (when notebooks were in root):**

```python
from config.database import db_UJ, client, collection_airports_cache_legacy
from routes.root.root_class import Root_class
from routes.root.search.search_interface import SearchInterface
from routes.route import get_search_suggestions
```

**New imports (from notebooks/ directory):**

```python
from ..config.database import db_UJ, client, collection_airports_cache_legacy
from ..routes.root.root_class import Root_class
from ..routes.root.search.search_interface import SearchInterface
from ..routes.route import get_search_suggestions
```

### Alternative: Add Parent Directory to Path

Add this cell at the beginning of each notebook:

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

Then use the original import statements without modification.

### Files That Need Updates

- `search-index.ipynb` - Update config.database and routes imports
- `mongo.ipynb` - Update config.database and routes imports  
- `edct-poc.ipynb` - Update routes.root.api and config.database imports
- `Misc.ipynb` - Update data file paths and check for any project imports

### Data File Path Updates Required

**IMPORTANT:** Some notebooks also reference data files that were moved to the `data/` directory:

**In `Misc.ipynb` (line ~176):**

```python
# Old path (when notebook was in root):
# with open('publicuj_searches_unique_sorts.pkl', 'wb') as f:

# New path (from notebooks/ directory):
# with open('../data/publicuj_searches_unique_sorts.pkl', 'wb') as f:
```

**In `search-index.ipynb` (line ~214):**

```python
# Old path (when notebook was in root):
qc = QueryClassifier(icao_file_path="unique_icao.pkl")

# New path (from notebooks/ directory):
qc = QueryClassifier(icao_file_path="../data/unique_icao.pkl")
```

**General rule for data file paths in notebooks:**

- **From notebooks/ to data/:** Use `../data/filename.pkl`
- **From notebooks/ to core/pkl/:** Use `../core/pkl/filename.pkl`

## Note

These notebooks may contain experimental code and are not part of the production application. They serve as development tools and documentation of the development process.
