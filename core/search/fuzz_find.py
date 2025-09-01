# TODO: investigate this levenshtein since that message shows up dugring backend container spinups.
# from levenshtein import levenshtein  # type: ignore
from fuzzywuzzy import fuzz, process

""" Uses the frontend formatted search_index_collection to search and deliver fuzz found results."""
def fuzz_find(query, data, qc, limit=5):
    # For very short queries, prioritize prefix matching
    if len(query) <= 2:

        # First find exact prefix matches
        prefix_matches = [item for item in data 
                         if item['fuzz_find_search_text'].startswith(query.lower())]
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
        parsed_query = qc.parse_query(query)           # Attempt to run the parse query when suggestions are exhausted.
        # TODO: Account for fuzz exhaustion, also understand that fuzz returns atleast 5 items regarless of matching so exhaustion is non-existant.
                    # Check TOD in get_search_suggestions. 
        # print('pq', parsed_query)

    # Get search text from all items
    choices = [item['fuzz_find_search_text'] for item in search_universe]

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
    sti_items_match_w_query =  prefix_matches + fuzzy_items
    return sti_items_match_w_query
