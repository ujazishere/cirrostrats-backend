
def format_returns():
    """
    # Unused currently. Need mechanism to format the suggestions to be returned to the frontend.
    this is supposed to account for suggestions as well as parseQuery results
    """
    return

def search_suggestion_format(c_docs, limit=1000,):         # cta- collection test airports; ctf- collection test flights

    # TODO VHP: Fix this fuckery! This formatting is terrible - unable to re-use it with this approach.
            # Separate formating logic from returning logic.
            
    # create unified search index
    search_index = []
    
    for doc in c_docs:

        terminanl_gate_st = doc.get('Terminal/Gate')
        airport_st = doc.get('airport_st')
        fid_st = doc.get('fid_st')

        # logic to separaate out flightID from airport and terminal/gates.
        if terminanl_gate_st:
            val_field,val,val_type = 'Terminal/Gate', terminanl_gate_st, 'Terminal/Gate'
        elif airport_st:
            val_field,val,val_type = 'airport', airport_st, 'airport'
        elif fid_st:
            val_field,val,val_type = 'flightID', fid_st, 'flight'

        passed_data = { 
            'stId': str(doc['_id']),
            'id': str(doc['r_id']),
            f"{val_field}":val,         # attempt to make a key field/property for an object in frontend.
            'display': val,             # This is manipulated later hence the duplicate.
            'type': val_type,
            'ph': doc.get('ph', 0),
            'search_text': val.lower()
            }
        
        search_index.append(passed_data)
    
    # sort by popularity (count), it obv comes in sorted. this is just an extra precautionary step.
    search_index.sort(key=lambda x: x['ph'], reverse=True)
    
    return search_index
