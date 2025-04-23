from config.database_UJ import client

db = client.cirrostrats                 # get a particular db
ctf = db['test_es']   # create/get a collection
cta = db['test_airports']   # create/get a collection

lcf = list(ctf.find({'count':{"$exists":True}},{'flightID':1, 'count':1}))
lca = list(cta.find({'count':{"$exists":True}},{'code':1, 'name':1, 'count':1}))

# Cache for the merged daa - Sorted
merged_data = None

def get_search_suggestion_data(cta_data=lca, ctf_data=lcf):
    """Load and merge data from both collections."""
    global merged_data
    
    # if merged_data is not None:
    #     return merged_data
    
    # # Fetch data from MongoDB
    # cta_data = list(cta.find({'count': {"$exists": True}}, 
    #                          {'code': 1, 'count': 1, 'name': 1}))
    # ctf_data = list(ctf.find({'count': {"$exists": True}}, 
    #                          {'flightID': 1, 'count': 1}))
    
    # Create unified search index
    search_index = []
    
    # Add airport entries
    for airport in cta_data:
        name = airport.get('name', '')
        search_index.append({
            'id': str(airport['_id']),
            'type': 'airport',
            'code': airport['code'],
            'name': name,
            'display': f"{airport['code']} - {name}" if name else airport['code'],
            'count': airport.get('count', 0),
            'search_text': f"{airport['code']} {name}".lower()
        })
    
    # Add flight entries
    for flight in ctf_data:
        search_index.append({
            'id': str(flight['_id']),
            'type': 'flight',
            'flightID': flight['flightID'],
            'display': flight['flightID'],
            'count': flight.get('count', 0),
            'search_text': flight['flightID'].lower()
        })
    
    # Sort by popularity (count)
    search_index.sort(key=lambda x: x['count'], reverse=True)
    
    merged_data = search_index
    return merged_data

