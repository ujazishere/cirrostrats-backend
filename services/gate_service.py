try:        # This is in order to keep going when collections are not available
    from config.database import db_UJ
except Exception as e:
    print('Mongo collection(Luis) connection unsuccessful\n', e)
    

async def gate_returns_service(gate):
    """ Nidhi: Returns gate from ewrGates """
    gate_rows_collection = db_UJ['ewrGates']   # create/get a collection
    
    return_crit = {'_id':0}
    find_crit = {'Gate':{'$regex':gate}}
    res = gate_rows_collection.find(find_crit, return_crit)

    ewr_gates = list(res)

    if ewr_gates:
        return ewr_gates