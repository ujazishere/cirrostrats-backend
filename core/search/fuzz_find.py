# TODO: investigate this levenshtein since that message shows up dugring backend container spinups.
# from levenshtein import levenshtein  # type: ignore
from fuzzywuzzy import fuzz, process

def fuzz_find(query, data, qc, limit=5):
    """ Uses the frontend formatted suggestions cache collection to search and deliver fuzz found results """

    # For very short queries, prioritize prefix matching
    if len(query) <= 2:

        # First find exact prefix matches
        prefix_matches = [item for item in data 
                         if ' '.join(item['displaySimilarity']).startswith(query.lower())]
        # Return prefix matches if we have enough

        if len(prefix_matches) >= limit:
            return prefix_matches[:limit]
            
        # Otherwise, supplement with fuzzy matches
        remaining = limit - len(prefix_matches)
        search_universe = [item for item in data if item not in prefix_matches]

    else:
        prefix_matches = []
        search_universe = data
        remaining = limit
        #  NOTE: understand that fuzz returns atleast 5 items regarless of matching so exhaustion is non-existant.

    # Get search text from all items
    choices = [' '.join(item['displaySimilarity']) for item in search_universe]

    # Get fuzzy matches using fuzzywuzzy
    fuzzy_matches = process.extract(
        query.lower(), 
        choices,
        limit=remaining,
        scorer=fuzz.partial_ratio  # Better for autocomplete scenarios
    )

    # Get the corresponding items
    fuzzy_items = [search_universe[choices.index(match)] for match, score in fuzzy_matches 
                  if score > 90]  # Minimum similarity threshold
    
    # Combine prefix and fuzzy matches
    scc_items_match_w_query =  prefix_matches + fuzzy_items
    return scc_items_match_w_query
