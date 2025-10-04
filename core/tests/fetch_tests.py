try:        # This is in order to keep going when collections are not available
    # from config.database import collection_airports, collection_weather, collection_searchTrack
    from config.database import collection_flights, db_UJ
except Exception as e:
    print('Mongo collection(Luis) connection unsuccessful\n', e)

def tests():
    """
    TODO VHP Test: This is for testing to see the data returns from fv and fs are reliable. needs more work.
    """
    airline_code = 'UA'
    # flt_num = '4546'
    # flt_num = '414'
    flt_num = '4433'
    # flt_num = '362'
    date = 20250503
    airport = 'KORD'

    flt_nums = ['4418','4433','414','4546','362','213','1411','5555']
    from core.dep_des import Pull_flight_info
    flt_info = Pull_flight_info()
    # flt_info.flight_view_gate_info(airline_code='UA',flt_num='4461')

    for i in flt_nums:
        aa = flt_info.flightstats_dep_arr_timezone_pull(airline_code='UA',flt_num_query=i)
        airport = aa['flightStatsOrigin'][1:]
        # print('treagfdsv',i)
        print(aa)
    # x(flt_num,airport,date,airline_code)

async def icao_regional_to_major_match():

    import datetime as dt
    from datetime import timedelta
    today = dt.datetime.now(dt.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    """ Return only the docs that have versions array and that array length is more than 1?
        and returns should return only those versions. Complicated but fascinating """
    
    # query = "^ASA"
    query = "^RPA"
    total_min_versions = 1    # versions array lenth is greater than x
    v = {
        "$elemMatch": {
          "timestamp": {
            "$gte": today,
            "$lt": tomorrow
          }
        }
      }
    crit = {
      "flightID": { "$regex": query },
      "versions": v,
      # "versions": { "$exists": "true" },
      "$expr": { "$gt": [{ "$size": "$versions" }, total_min_versions]},    #versions array lenth is greater than 1
    }
    returns = {'flightID': 1, '_id': 1, 'versions': v}
    airline = [doc for doc in collection_flights.find(crit, returns)]
    
    """ Attempt to verify if a particular ICAO is associated with that major and what are the flight digits assigned to it"""
    # len([i['versions'] for i in airline if i.get('versions')]), len([i['flightID'] for i in airline if not i.get('versions')])
    # rpa_ua = sorted([int(i['flightID'][3:]) for i in airline])[1:234]
    
    
    rpa_ua = sorted([int(i['flightID'][3:]) for i in airline])[235:]        # digits 3000-3999
    rpa_aa = sorted([int(i['flightID'][3:]) for i in airline])[247:]        # digits 4000:
    # [i for i in airline if i['flightID'] == 'RPA4335']
    # collection_flights.find_one({'flightID': 'RPA3302'})
    
    # Testing flight nunber if its a UA flight by fact checking/comparing jms and webscraped returned
    flightID = str(rpa_aa[0])
    from routes.route import flight_stats_url
    x = await flight_stats_url('UA'+flightID)
    # print(x)
    print(x['flightStatsOrigin'],x['flightStatsDestination'])
    all = collection_flights.find_one({'flightID': 'RPA'+flightID},{'versions':v, '_id':0})
    all['versions'][0]['departure'],all['versions'][0]['arrival']
    
    # Testing another flight.
    from routes.route import flight_stats_url
    flightID = 'DL1199'
    x = await flight_stats_url('UA'+flightID)
    
    
    # Idea for this  funciton is to match the collection ICAO flight with webscrape flightID that is associated with a regionals major
    # in case of replublic flights 3000-3999 are united ones and 4000: are AA. 5000: are DL; 9000: are again AA.
    # test_rpa_icao_5000 = rpa_aa[340:353]
    test_rpa_aa_9000 = rpa_ua[-3:]
    icao= []
    for i in test_rpa_aa_9000[:5]:
        flightID = str(i)
        icao.append(await flight_stats_url(flightID,airline_code='AA'))     # This airline code is supposed to be deprecated. it accounts for parsing airline code from flightID
        mc = collection_flights.find_one({'flightID': 'RPA'+flightID},{'versions':v, '_id':0})
        print(mc['versions'][0]['departure'],mc['versions'][0]['arrival'])