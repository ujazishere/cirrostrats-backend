
def search_suggestion_format(c_docs, limit=1000,):         # cta- collection test airports; ctf- collection test flights
    # TODO: Fix this fuckery! This formatting is terrible - cant re-use it like this. Separate formating logic from returning logic.
    
    # create unified search index
    search_index = []
    
    for doc in c_docs:

        terminanl_gate_st = doc.get('Terminal/Gate')
        airport_st = doc.get('airport_st')
        fid_st = doc.get('fid_st')

        # logic to separaate out flightID from airport and terminal/gates.
        if terminanl_gate_st:
            val,val_field,val_type = terminanl_gate_st, 'Terminal/Gate','Terminal/Gate'
        elif airport_st:
            val,val_field,val_type = airport_st, 'airport','airport'
        elif fid_st:
            val,val_field,val_type = fid_st, 'flightID', 'flight'

        passed_data = { 
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
