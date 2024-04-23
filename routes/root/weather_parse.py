# # This is for Jupyter
# 
# datis ="""2SM BR VCSH FEW015 OVC060 TEMPO 0300/0303 1 1/2SM FG BKN015
#     FM030300 00000KT 1SM -SHRA FG OVC002
#     FM031300 19005KT 3/4SM BR OVC004
#     FM031500 23008KT 1/26SM OVC005
#     FM031800 25010KT 1/4SM OVC015
#     FM032100 25010KT M1/4SM BKN040"> KRIC 022355Z 0300/0324 00000KT 2SM BR VCSH FEW015 OVC060 TEMPO 0300/0303 1 1/2SM FG BKN015
#     FM030300 00000KT 1SM -SHRA FG OVC002
#     FM031300 19005KT 3/4SM BR OVC004
#     FM031500 23008KT 1/26SM OVC005
#     FM031800 25010KT 1/4SM OVC015
#     FM032100 25010KT M1/4SM BKN040"""

# import re
# from routes.root.weather_parse import WeatherParse
# wp = WeatherParse()
# wp.visibility_color_code(react=True,incoming_weather_data=wp.test_datis)
# wp.weather_highlight_array(
#     {'D-ATIS':wp.test_datis,'METAR':wp.test_metar,'TAF':wp.test_taf}
# )

import re
import pickle
from bs4 import BeautifulSoup as bs4
import requests
import json
from .root_class import Root_class,Pull_class
from datetime import datetime


# TODO: extract all airpoirts METAR and TAF  in the airport database
            # compare all unique values and group identical ones
            # analyze data for format patterns to make a template for output
# TODO: seperate raw data from html highlight. 
        # should have ability to return both raw(for externam use) and highlighted data for use in web.


class WeatherParse:
    def __init__(self) -> None:
        # Variables to be used for static html injection that feeds to explicitly show pertinent information like lower visibility and ceilings, windshear, runway use and so on.
        self.pink_text_color = r'<span class="pink_text_color">\1\2</span>'
        self.red_text_color = r'<span class="red_text_color">\1\2</span>'
        self.yellow_highlight = r'<span class="yellow_highlight">\1\2</span>'
        self.box_around_text = r'<span class="box_around_text">\1\2</span>'
        self.yellow_warning = r'<span class="yellow_warning">\1\2</span>' 


        # first digit between 1-2 then space all of it optional. Then digit and fwrd slash optional then digit then SM
        # Notice the two groups in regex that exists within brackets. Necessary for regex processing.
        self.lifr_fractional_patt = r'((?<! \d ))((M)?\d/(\d)?\dSM)'        # Just the fractional pattern
        self.ifr_fractional_patt = r'((?<!\d))(([0-2] )(\d/\d{1,2})SM)'
        self.lifr_single_or_douple = r'((?<= )0?)(0SM)'
        self.ifr_single_or_douple = r'((?<= )0?)([1,2]SM)'

        self.SM_PATTERN = r"( [1-2] )?(\d/)?(\d)?(\d)(SM)"       # Matches all Visibilities with trailing SM
        self.SM_PATTERN_fractions = r"([0-2] )?(\d/\d{1,2})SM"          # maps fractional visibilities between 1 and 3
        self.SM_PATTERN_two_digit = r"^[0-9]?[0-9]SM"          # valid 1 and 2 digit visibility
        self.SM_PATTERN_one_digit_ifr = r"^[0-2]SM"          # 0,1 and 2 SM only
        
        self.BKN_OVC_PATTERN_LIFR = r"(BKN|OVC)(00[0-4])"   # BKN or OVC,first two digit `0`, 3rd digit btwn 0-4
        self.BKN_OVC_PATTERN_IFR = r"(BKN|OVC)(00[5-9])"    # BKN/OVC below 10 but above 5
        self.BKN_OVC_PATTERN_alternate = r"(BKN|OVC)(0[1][0-9])"         # Anything and everything below 20

        self.ALTIMETER_PATTERN = r"((?<= )A)(\d{4})"
        self.FREEZING_TEMPS = r'(00|M\d\d)(/M?\d\d)'
        self.ATIS_INFO = r"(DEP|ARR|ARR/DEP|ATIS)( INFO [A-Z])"
        self.LLWS = r"()((?<=)(LLWS|WIND|LOW LEVEL ).*?\.)"

        # The empty bracks in the beginning is to make groups as it is easier to work with 2 groups completely different from each other. Temp fix that works.
        self.RW_IN_USE = r'()((SIMUL([A-Z]*)?,?|VISUAL (AP(P)?(ROA)?CH(E)?(S)?)|(ILS(/VA|,)?|(ARRIVALS )?EXPECT|RNAV|((ARVNG|LNDG) AND )?DEPG|LANDING)) (.*?)(IN USE\.|((RWY|RY|RUNWAY|APCH|ILS|DEP|VIS) )(\d{1,2}(R|L|C)?)\.))'
        # self.RW_IN_US = r'(ARRIVALS EXPECT|SIMUL|RUNWAYS|VISUAL|RNAV|ILS(,|RY|))(.*?)\.'

        self.test_datis = "DEN ARR INFO L 1953Z. 27025G33KT 10SM FEW080 SCT130 SCT200 01/M19 A2955 (TWO NINER FIVE FIVE) RMK AO2 PK WND 29040/1933 SLP040. LLWS ADZYS IN EFCT. HAZUS WX INFO FOR CO, KS, NE, WY AVBL FM FLT SVC. PIREP 30 SW DEN, 2005Z B58T RPRTD MDT-SVR, TB, BTN 14THSD AND 10 THSD DURD. PIREP DEN AREA,, 1929Z PC24 RPRTD MDT, TB, BTN AND FL 190 DURD. EXPC ILS, RNAV, OR VISUAL APCH, SIMUL APCHS IN USE, RWY 25, RWY 26. NOTICE TO AIR MISSION. S C DEICE PAD CLOSED. DEN DME OTS. BIRD ACTIVITY VICINITY ARPT. ...ADVS YOU HAVE INFO L."
        self.test_metar = "KIND 012054Z 16004KT 1/2SM R05L/P6000FT BR OVC004 08/08 A2978 RMK AO2 SFC VIS 3 SLP085 T00830078 56006"
        self.test_taf = """
                        KRIC 022355Z 0300/0324 00000KT 2SM BR VCSH FEW015 OVC060 TEMPO 0300/0303 1 1/2SM FG BKN015
    FM030300 00000KT 1SM -SHRA FG OVC002
    FM031300 19005KT 3/4SM BR OVC004
    FM031500 23008KT 1/26SM OVC005
    FM031800 25010KT 1/4SM OVC015
    FM032100 25010KT M1/4SM BKN040
                        """

        self.taf_top_body = """KRIC 022355Z 0300/0324 00000KT 2SM BR VCSH FEW015 OVC060 TEMPO 0300/0303 1 1/2SM FG BKN015"""
        self.taf_FM_group = """FM030300 00000KT 1SM -SHRA FG OVC002
FM031300 19005KT 3/4SM BR OVC004
FM031500 23008KT 1/26SM OVC005
FM031800 25010KT 1/4SM OVC015
FM032100 25010KT M1/4SM BKN040"""

    def visibility_color_code(self,react=None,incoming_weather_data=None):

        if react:
            vis_patterns_to_be_matched=[
                self.lifr_fractional_patt,
                self.ifr_fractional_patt,
                self.lifr_single_or_douple,
                self.ifr_single_or_douple
            ]
            highlight_returns = [
                match
                for each_pattern in vis_patterns_to_be_matched
                # ':=' is a walrus operator that assigns the match to the variable.
                if (match := re.findall(each_pattern,incoming_weather_data))
            ]

            highlight_returns = [y[1] for i in highlight_returns for y in i]

            return highlight_returns
        
            # This is the old and tedious way of accomplishing the above.
            # highlight_returns = []
            # aa = re.search(self.lifr_fractional_patt,incoming_weather_data)
            # bb = re.search(self.ifr_fractional_patt,incoming_weather_data)
            # cc = re.search(self.lifr_single_or_douple,incoming_weather_data)
            # dd = re.search(self.ifr_single_or_douple,incoming_weather_data)
            # if aa:
            #     highlight_returns.append(aa.group())
            # if bb:
            #     highlight_returns.append(bb.group())
            # if cc:
            #     highlight_returns.append(cc.group())
            # if dd:
            #     highlight_returns.append(dd.group())
            # return highlight_returns
        else:
            # Surrounds the matched pattern with the html declared during initialization(the __init__ method).
            lifr_frac = re.sub(self.lifr_fractional_patt, self.pink_text_color,incoming_weather_data)
            ifr_frac = re.sub(self.ifr_fractional_patt, self.red_text_color,lifr_frac)
            lifr_digits = re.sub(self.lifr_single_or_douple,self.pink_text_color,ifr_frac)
            ifr_digits = re.sub(self.ifr_single_or_douple,self.red_text_color,lifr_digits)
            processed_incoming_data = ifr_digits




            if processed_incoming_data:
                return processed_incoming_data
            else:
                print('Nothing to process in visibility_color_code func')
                return incoming_weather_data
        

    def datis_processing(self,datis_raw_fetch,datis_arr=None):

        datis_raw = 'N/A'       # Need this to be declared to avoid error when datis is not available
        datis = datis_raw_fetch
        # D-ATIS processing for departure vs arrival
        if type(datis) == list and 'datis' in datis[0].keys():
            if len(datis) == 1:
                datis_raw = datis[0]['datis']
            elif len(datis) == 2:       # Datis arrival and departure have been separated
                if datis[0]['type'] == 'arr':
                    print('Returned Arrival D-ATIS through weather_parse.py')
                    arr_datis = datis[0]['datis']
                else:
                    arr_datis = datis[1]['datis']
                if datis[1]['type'] == 'dep':
                    dep_datis = datis[1]['datis']
                else:
                    dep_datis = datis[0]['datis']
                
                if datis_arr:
                    datis_raw = arr_datis
                else:
                    datis_raw = dep_datis
            else:
                print('Impossible else in DATIS')
                datis_raw = 'N/A'
        return datis_raw


    def raw_weather_pull(self, query=None, datis_arr=None):
        
        # Find ways to convert raw query input into identifiable airport ID
            # What does this mean^^?
        airport_id = query
        awc_metar_api = f"https://aviationweather.gov/api/data/metar?ids={airport_id}"
        metar_raw = requests.get(awc_metar_api)
        metar_raw = metar_raw.content
        metar_raw = metar_raw.decode("utf-8")
        awc_taf_api = f"https://aviationweather.gov/api/data/taf?ids={airport_id}"
        taf_raw = requests.get(awc_taf_api)
        taf_raw = taf_raw.content
        taf_raw = taf_raw.decode("utf-8")

        datis_api =  f"https://datis.clowd.io/api/{airport_id}"
        datis = requests.get(datis_api)
        datis = datis.json()
        datis_raw = self.datis_processing(datis_raw_fetch=datis,datis_arr=datis_arr)

        return dict({ 'datis': datis_raw,
                        'metar': metar_raw, 
                        'taf': taf_raw,
                        })
    

    def processed_weather(self, query=None, dummy=None, datis_arr=None,
                          weather_raw=None,
                          ):
        if dummy:
            datis_raw = dummy['D-ATIS']
            metar_raw = dummy['METAR']
            taf_raw = dummy['TAF']            


        elif weather_raw:
            raw_return = weather_raw        # This wont do the datis processing.
            datis_raw = self.datis_processing(datis_raw_fetch=raw_return['datis'],datis_arr=datis_arr)
            metar_raw = raw_return['metar']
            taf_raw = raw_return['taf']
        else:
            # Pulls raw weather and will also do the datis processing within the function.
            raw_return = self.raw_weather_pull(query=query,datis_arr=datis_arr)     
            datis_raw = raw_return['datis']
            metar_raw = raw_return['metar']
            taf_raw = raw_return['taf']


            

        def zulu_extracts(weather_input, datis=None, taf=None):
            
            # This could be work intensive. Make your own conversion if you can avoid using datetime
            raw_utc = Root_class().date_time(raw_utc='HM')[-4:]
            raw_utc_dt = datetime.strptime(raw_utc,"%H%M")
            
            if datis:
                zulu_item_re = re.findall('[0-9]{4}Z', weather_input)       # regex zulu
            else:
                # Not necessary if only using 4 digits. Use this if DDHHMM is required.
                zulu_item_re = re.findall('[0-9]{4}Z', weather_input)       # regex zulu
                
            if zulu_item_re:        # regex process
                zulu_weather = zulu_item_re[0][:-1]
                zulu_weather_dt = datetime.strptime(zulu_weather,"%H%M")
                diff = raw_utc_dt - zulu_weather_dt
                diff = int(diff.seconds/60) 
                
                dummy_published_time = '2152Z'
                # diff = 56
                if taf:
                    if diff > 350:
                        # diff = dummy_published_time
                        return f'<span class="published-color1">{diff} mins ago </span>'
                    if diff < 10:
                        # diff = dummy_published_time
                        return f'<span class="published-color2">{diff} mins ago</span>'
                    else:
                        # diff = dummy_published_time
                        return f'{diff} mins ago'

                else:
                    if diff > 55:
                        # diff = dummy_published_time
                        return f'<span class="published-color1">{diff} mins ago </span>'
                    if diff <= 5:
                        # diff = dummy_published_time
                        return f'<span class="published-color2">{diff} mins ago</span>'
                    else:
                        # diff = dummy_published_time
                        return f'{diff} mins ago'
            else:
                zulu_weather = 'N/A'
                return zulu_weather
            
            

        
        # Exporting raw weather data for color code processing
        # raw_weather_dummy_data = { 'D-ATIS': datis_raw, 'METAR': metar_raw, 'TAF': taf_raw} 
        # with open(f'raw_weather_dummy_data{airport_id}.pkl', 'wb') as f:
            # print(f"DUMPING RAW WEATHER DATA")
            # pickle.dump(raw_weather_dummy_data, f)




        # LIFR PAttern for ceilings >>> Anything below 5 to pink METAR
        low_ifr_metar_ceilings = re.sub(self.BKN_OVC_PATTERN_LIFR, self.pink_text_color, metar_raw)
        # LIFR pattern for ceilings >>> anything below 5 to pink TAF 
        low_ifr_taf_ceilings = re.sub(self.BKN_OVC_PATTERN_LIFR, self.pink_text_color, taf_raw)
        # LIFR pattern for ceilings >>> anything below 5 to pink DATIS 
        low_ifr_datis_ceilings = re.sub(self.BKN_OVC_PATTERN_LIFR, self.pink_text_color, datis_raw)
        # print('within lowifr', datis_raw)

        # IFR Pattern for ceilings METAR
        ifr_metar_ceilings = re.sub(self.BKN_OVC_PATTERN_IFR, self.red_text_color, low_ifr_metar_ceilings)
        # IFR pattern for ceilings TAF
        ifr_taf_ceilings = re.sub(self.BKN_OVC_PATTERN_IFR, self.red_text_color, low_ifr_taf_ceilings)
        # IFR pattern for ceilings DATIS
        ifr_datis_ceilings = re.sub(self.BKN_OVC_PATTERN_IFR, self.red_text_color, low_ifr_datis_ceilings)
        
        # ACCOUNT FOR VISIBILITY `1 /2 SM`  mind the space in betwee. SCA had this in TAF and its not accounted for.

        # LIFR PAttern for visibility >>> Anything below 5 to pink METAR
        lifr_ifr_metar_visibility = self.visibility_color_code(incoming_weather_data=ifr_metar_ceilings)
        # LIFR pattern for visibility >>> anything below 5 to pink TAF 
        lifr_ifr_taf_visibility = self.visibility_color_code(incoming_weather_data=ifr_taf_ceilings)
        # LIFR pattern for visibility >>> anything below 5 to pink DATIS 
        lifr_ifr_datis_visibility = self.visibility_color_code(incoming_weather_data=ifr_datis_ceilings)

        # original metar alternate for ceilings text color >> NEED HIGHLIGHT FOR ANYTHING BELOW 20
        highlighted_metar = re.sub(self.BKN_OVC_PATTERN_alternate, self.yellow_highlight, lifr_ifr_metar_visibility)

        # original taf alternate for ceilings text color
        highlighted_taf = re.sub(self.BKN_OVC_PATTERN_alternate, self.yellow_highlight, lifr_ifr_taf_visibility)

        # TODO: return as an array instead of inserting the break.
        # highlighted_taf = highlighted_taf.replace("FM", "<br>\xa0\xa0\xa0\xa0FM")   # line break for FM section in TAF for HTML
        highlighted_datis = re.sub(self.BKN_OVC_PATTERN_alternate, self.yellow_highlight, lifr_ifr_datis_visibility)

        highlighted_datis = re.sub(self.ATIS_INFO, self.box_around_text, highlighted_datis)
        highlighted_datis = re.sub(self.ALTIMETER_PATTERN, self.box_around_text, highlighted_datis)
        highlighted_datis = re.sub(self.LLWS, self.yellow_warning, highlighted_datis)
        highlighted_datis = re.sub(self.RW_IN_USE, self.box_around_text,highlighted_datis)
        
        highlighted_metar = re.sub(self.ALTIMETER_PATTERN, self.box_around_text, highlighted_metar)

        return dict({ 'D-ATIS': highlighted_datis,
                    #   'D-ATIS-Highlights': highlight_array
                      'D-ATIS_zt': zulu_extracts(datis_raw,datis=True),
                      
                      'METAR': highlighted_metar, 
                      'METAR_zt': zulu_extracts(metar_raw),

                      'TAF': highlighted_taf,
                      'TAF_zt': zulu_extracts(taf_raw,taf=True),
                      })


    def nested_weather_dict_explosion(self,incoming_weather:dict):
        # Departure weather: assigning dedicated keys for data rather than a nested dictionary to simplify use on front end
        
        weather_returns = {}
        dep_datis = incoming_weather['dep_weather']['D-ATIS']
        dep_metar = incoming_weather['dep_weather']['METAR']
        dep_taf = incoming_weather['dep_weather']['TAF']
        weather_returns['dep_metar'] = dep_metar
        weather_returns['dep_datis'] = dep_datis
        weather_returns['dep_taf'] = dep_taf

        dep_datis_zt = incoming_weather['dep_weather']['D-ATIS_zt']
        dep_metar_zt = incoming_weather['dep_weather']['METAR_zt']
        dep_taf_zt = incoming_weather['dep_weather']['TAF_zt']
        weather_returns['dep_metar_zt'] = dep_metar_zt
        weather_returns['dep_datis_zt'] = dep_datis_zt
        weather_returns['dep_taf_zt'] = dep_taf_zt

        # Destionation Weather: assigning dedicated keys for data rather than a nested dictionary to simplify use on front end
        dest_datis = incoming_weather['dest_weather']['D-ATIS']
        dest_metar = incoming_weather['dest_weather']['METAR']
        dest_taf = incoming_weather['dest_weather']['TAF']
        weather_returns['dest_datis'] = dest_datis
        weather_returns['dest_metar'] = dest_metar
        weather_returns['dest_taf'] = dest_taf

        dest_datis_zt = incoming_weather['dest_weather']['D-ATIS_zt']
        dest_metar_zt = incoming_weather['dest_weather']['METAR_zt']
        dest_taf_zt = incoming_weather['dest_weather']['TAF_zt']
        weather_returns['dest_datis_zt'] = dest_datis_zt
        weather_returns['dest_metar_zt'] = dest_metar_zt
        weather_returns['dest_taf_zt'] = dest_taf_zt

        return weather_returns


    def weather_highlight_array(self,example_data):
        datis_raw = example_data['D-ATIS']
        metar_raw = example_data['METAR']
        taf_raw = example_data['TAF']            
        
        def get_highlights(weather_raw):
            highlights = []
            # rw_in_use = re.search(self.RW_IN_USE,datis_raw)
            # if rw_in_use:
            #     highlighted_datis.append(rw_in_use.group())
            
            ifr_datis_vis = self.visibility_color_code(react=True,incoming_weather_data=weather_raw)
            highlights.extend(ifr_datis_vis)
            datis_patts = [self.BKN_OVC_PATTERN_alternate,
            self.ATIS_INFO,
            self.ALTIMETER_PATTERN,
            self.LLWS,
            self.RW_IN_USE,
            self.BKN_OVC_PATTERN_IFR,
            self.BKN_OVC_PATTERN_LIFR,
            ]
    
            find_all_highllights = [
                match
                for each_pattern in datis_patts
                if (match := re.findall(each_pattern,weather_raw))
            ]
            
            join_mechanism = ["".join(i[0]) for i in find_all_highllights]
            highlights.extend(join_mechanism)

            return highlights
        
        datis_highs,metar_highs,taf_highs = [None]*3
        if datis_raw:
            datis_highs = get_highlights(datis_raw)
        if metar_raw: 
            metar_highs = get_highlights(metar_raw)
        if taf_raw:
            taf_highs = get_highlights(taf_raw)
            


        return {
            "D_ATIS":self.test_datis,
            "METAR": self.test_metar,
            "TAF": [{
                "TopBody":self.taf_top_body,
                "FMGroup": self.taf_FM_group,
        }],
            "D_ATISHighlights": datis_highs,
            "METARHighlights": metar_highs,
            "TAFHighlights": taf_highs,
        }


