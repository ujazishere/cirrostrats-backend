from config.database import gate_rows_collection


async def gate_returns_service(referenceId):
    """ Nidhi: Returns gate from ewrGates """
    
    return_crit = {'_id':0}
    # print('referenceId', referenceId)
    find_crit = {'_id': referenceId}
    res = gate_rows_collection.find_one(find_crit, return_crit)
    # print('res', res)
    return res