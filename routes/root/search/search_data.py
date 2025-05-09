def get_search_suggestion_data(c_docs, limit=1000,):         # cta- collection test airports; ctf- collection test flights
    
    # create unified search index
    search_index = []
    
    # add airport entries
    print('len of total docs',len(c_docs))
    for doc in c_docs:
        val,val_field,val_type = doc.get('airport_st'), 'airport','airport'
        if not val:
            val = doc.get('fid_st')
            val_field = 'flightID'
            val_type = 'flight'
        passed_data = { 
            'id': str(doc['r_id']),
            f"{val_field}":val,         # attempt to make a key field/property for an object in frontend.
            'display': val,             # This is manipulated later hence the duplicate.
            # 'type': 'doc',
            # 'code': doc['code'],
            'type': val_type,
            'ph': doc.get('ph', 0),
            'search_text': val.lower()
            }
        
        search_index.append(passed_data)
    
    # sort by popularity (count), it obv comes in sorted. this is just an extra precautionary step.
    search_index.sort(key=lambda x: x['ph'], reverse=True)
    
    return search_index
