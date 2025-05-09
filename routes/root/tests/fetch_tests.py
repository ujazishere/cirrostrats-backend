
def tests():
    """
    TODO: This is for testing to see the data returns from fv and fs are reliable. needs more work.
    """
    airline_code = 'UA'
    # flt_num = '4546'
    # flt_num = '414'
    flt_num = '4433'
    # flt_num = '362'
    date = 20250503
    airport = 'KORD'

    flt_nums = ['4418','4433','414','4546','362','213','1411','5555']
    from routes.root.dep_des import Pull_flight_info
    flt_info = Pull_flight_info()
    # flt_info.flight_view_gate_info(airline_code='UA',flt_num='4461')

    for i in flt_nums:
        aa = flt_info.flightstats_dep_arr_timezone_pull(airline_code='UA',flt_num_query=i)
        airport = aa['flightStatsOrigin'][1:]
        # print('treagfdsv',i)
        print(aa)
        print(flt_info.flight_view_gate_info(airline_code,i,airport,))
    # x(flt_num,airport,date,airline_code)

