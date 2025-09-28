""" This is a class for parsing individual DATIS, METAR and TAF data."""

import re
import pickle
from bs4 import BeautifulSoup as bs4
import requests
import json
from .root_class import Root_class,Fetching_Mechanism
from datetime import datetime


# TODO VHP Weather: add the ability to see the departure as well as the arrival datis
# TODO Feature: extract all airpoirts METAR and TAF  in the airport database
            # compare all unique values and group identical ones
            # analyze data for format patterns to make a template for output

class Weather_parse:
    def __init__(self) -> None:
        # Variables to be used for static html injection that feeds to explicitly show pertinent information like lower visibility and ceilings, windshear, runway use and so on.
        self.pink_text_color = r'<span class="pink_text_color">\1\2</span>'
        self.red_text_color = r'<span class="red_text_color">\1\2</span>'
        self.yellow_highlight = r'<span class="yellow_highlight">\1\2</span>'
        self.box_around_text = r'<span class="box_around_text">\1\2</span>'         # Change name to `box_around_text`
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

    def visibility_color_code(self,incoming_weather_data):

        # Surrounds the matched pattern with the html declared during initialization(the __init__ method).
        lifr_frac = re.sub(self.lifr_fractional_patt, self.pink_text_color,incoming_weather_data)
        ifr_frac = re.sub(self.ifr_fractional_patt, self.red_text_color,lifr_frac)
        lifr_digits = re.sub(self.lifr_single_or_douple,self.pink_text_color,ifr_frac)
        ifr_digits = re.sub(self.ifr_single_or_douple,self.red_text_color,lifr_digits)
        processed_incoming_data = ifr_digits

        if processed_incoming_data:
            return processed_incoming_data
        else:
            # print('Nothing to process in visibility_color_code func')
            return incoming_weather_data

    def datis_processing(self, datis_raw):
        #     # DATIS NOTE: Major use in raw_weather_pull and html_injected_weather.
        """
        Process DATIS data into a consistent structure.
        Args:
            datis_raw (list or dict): Raw DATIS data, can be a list of dicts or a dict with an 'error' key.
            if there is arr and dep, returns combined as N/A and arr and dep as is.
            if there is only combined, returns combined as that value and the other as None.
            for non list non dict input, returns N/A, None, None and triggers notification for investigation.

        Returns: {
            'combined': str or 'N/A',
            'arr': str or None, 
            'dep': str or None
        }
        """
        # Initialize result structure
        result = {'combined': 'N/A', 'arr': None, 'dep': None}
        
        # # Handle error case
        if isinstance(datis_raw, dict) and datis_raw.get('error'):
            return result
        # Rare case- Handle non-list,non-dict input (already processed or unexpected format) - return "N/A"
        elif not isinstance(datis_raw, list):
            # TODO: Consider logging/notification this unexpected format - if not dict if not list, then what?- Should be investigated
            # logging.warning("Unexpected DATIS format: %s", datis_raw)
            return result
        
        # Process list input
        for item in datis_raw:
            datis_text = item.get('datis', '')
            data_type = item.get('type', '')
            
            if data_type == 'combined':
                result['combined'] = datis_text
            elif data_type == 'arr':
                result['arr'] = datis_text
            elif data_type == 'dep':
                result['dep'] = datis_text
        
        return result    

    
    def zulu_extraction(self, weather_input, weather_type:str):
        """ Extracts the zulu time from the weather input. 
            If datis is True, it will extract the zulu time from the datis input.
            If taf is True, it will extract the zulu time from the taf input.
            Otherwise, it will extract the zulu time from the metar input.
        """
        if weather_type == 'datis':
            zulu_item_re = re.findall('[0-9]{4}Z', weather_input)       # regex zulu
        elif weather_type == 'taf' or weather_type == 'metar':
            # Not necessary if only using 4 digits. Use this if DDHHMM is required.
            zulu_item_re = re.findall('[0-9]{6}Z', weather_input)       # regex zulu
            
        if zulu_item_re:    # There may be multiple zulu times in the datis, taf or metar. This will return the first one.
            return zulu_item_re[0]
        else:
            return 'N/A'

    def zulu_recency(self, weather_input, datis=None, taf=None):
        """ TODO:
            1. Hazard-- If the weather is over a month old or even day, the zt may be way off.
            2. Datis,metar sometimes have multiple zulu times. check weather_examination for this anomaly - zulu_anomaly 
               """

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
        
    def html_injected_weather(self, mock_test_data=None,
                          weather_raw=None,
                          ):
        """ This function takes in either mock_test_data or weather_raw as dict with datis, metar, taf data.
            html injection is done here for highlighting purposes - LIFR, IFR, Alternate IFR, ATIS code, 
            altimeter settings, LLWS, RW in use, and such are highlighted in this function.
        """
        # TODO DATIS: Next step logically seens to be to overhaul this function to return dict for datis returns
        if mock_test_data:
            metar_raw = mock_test_data['metar']
            datis_raw = mock_test_data['datis']
            taf_raw = mock_test_data['taf']
        
        elif weather_raw:
            raw_return = weather_raw        # This wont do the datis processing.
            # DATIS TODO: This is where datis params needs fixed
            datis_raw = self.datis_processing(datis_raw=raw_return.get('datis','N/A'))
            metar_raw = raw_return.get('metar')
            taf_raw = raw_return.get('taf')

        # LIFR PAttern for ceilings >>> Anything below 5 to pink METAR

        # Add null checks before regex operations
        low_ifr_metar_ceilings = re.sub(self.BKN_OVC_PATTERN_LIFR, self.pink_text_color, metar_raw) if metar_raw else ""
        # LIFR pattern for ceilings >>> anything below 5 to pink TAF 
        low_ifr_taf_ceilings = re.sub(self.BKN_OVC_PATTERN_LIFR, self.pink_text_color, taf_raw) if taf_raw else ""
        # LIFR pattern for ceilings >>> anything below 5 to pink DATIS 
        low_ifr_datis_ceilings = re.sub(self.BKN_OVC_PATTERN_LIFR, self.pink_text_color, datis_raw) if datis_raw else ""
        # print('within lowifr', datis_raw)

        # IFR Pattern for ceilings METAR
        ifr_metar_ceilings = re.sub(self.BKN_OVC_PATTERN_IFR, self.red_text_color, low_ifr_metar_ceilings)
        # IFR pattern for ceilings TAF
        ifr_taf_ceilings = re.sub(self.BKN_OVC_PATTERN_IFR, self.red_text_color, low_ifr_taf_ceilings)
        # IFR pattern for ceilings DATIS
        ifr_datis_ceilings = re.sub(self.BKN_OVC_PATTERN_IFR, self.red_text_color, low_ifr_datis_ceilings)

        # ACCOUNT FOR VISIBILITY `1 /2 SM`  mind the space in betwee. SCA had this in TAF and its not accounted for.

        # LIFR PAttern for visibility >>> Anything below 5 to pink METAR
        lifr_ifr_metar_visibility = self.visibility_color_code(ifr_metar_ceilings)
        # LIFR pattern for visibility >>> anything below 5 to pink TAF 
        lifr_ifr_taf_visibility = self.visibility_color_code(ifr_taf_ceilings)
        # LIFR pattern for visibility >>> anything below 5 to pink DATIS 
        lifr_ifr_datis_visibility = self.visibility_color_code(ifr_datis_ceilings)

        # original metar alternate for ceilings text color >> NEED HIGHLIGHT FOR ANYTHING BELOW 20
        highlighted_metar = re.sub(self.BKN_OVC_PATTERN_alternate, self.yellow_highlight, lifr_ifr_metar_visibility)

        # original taf alternate for ceilings text color
        highlighted_taf = re.sub(self.BKN_OVC_PATTERN_alternate, self.yellow_highlight, lifr_ifr_taf_visibility)
        highlighted_taf = highlighted_taf.replace("FM", "<br>\xa0\xa0\xa0\xa0FM") if highlighted_taf else ""   # line break for FM section in TAF for HTML
        highlighted_datis = re.sub(self.BKN_OVC_PATTERN_alternate, self.yellow_highlight, lifr_ifr_datis_visibility)

        highlighted_datis = re.sub(self.ATIS_INFO, self.box_around_text, highlighted_datis) if highlighted_datis else ""
        highlighted_datis = re.sub(self.ALTIMETER_PATTERN, self.box_around_text, highlighted_datis) if highlighted_datis else ""
        highlighted_datis = re.sub(self.LLWS, self.yellow_warning, highlighted_datis) if highlighted_datis else ""
        highlighted_datis = re.sub(self.RW_IN_USE, self.box_around_text,highlighted_datis) if highlighted_datis else ""

        highlighted_metar = re.sub(self.ALTIMETER_PATTERN, self.box_around_text, highlighted_metar) if highlighted_metar else ""

        return dict({ 'datis': highlighted_datis,
                    'datis_zt': self.zulu_recency(datis_raw,datis=True) if datis_raw else "",
                    'datis_ts': self.zulu_extraction(datis_raw, weather_type='datis') if datis_raw else "",
                    
                    'metar': highlighted_metar, 
                    'metar_zt': self.zulu_recency(metar_raw) if metar_raw else "",
                    'metar_ts': self.zulu_extraction(metar_raw,weather_type='metar') if metar_raw else "",

                    'taf': highlighted_taf,
                    'taf_zt': self.zulu_recency(taf_raw,taf=True) if taf_raw else "",
                    'taf_ts': self.zulu_extraction(taf_raw,weather_type='taf') if taf_raw else "",
                    })
