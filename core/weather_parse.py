""" This is a class for parsing individual DATIS, METAR and TAF data."""

import re
from .root_class import Root_class
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
    

    def color_code(self, weather:str, taf=False):
        """
        Function to color-code the weather data based on LIFR and IFR patterns.

        Parameters:
        weather (str): The weather data to be color-coded.
        taf (bool): Whether to add line breaks or empty spaces before FM block for HTML in TAF.

        Returns:
        str: The color-coded weather data.
        """

        # LIFR pattern for ceilings >>> Anything below 500ft to pink.
        html_injected_weather = re.sub(self.BKN_OVC_PATTERN_LIFR, self.pink_text_color, weather) if weather else ""
        # IFR pattern for below 1000ft.
        html_injected_weather = re.sub(self.BKN_OVC_PATTERN_IFR, self.red_text_color, html_injected_weather) if html_injected_weather else ""
        # TODO: ACCOUNT FOR VISIBILITY `1 /2 SM`  mind the space in between. SCA had this in TAF and its not accounted for.
        # IFR and LIFR pattern for visibility >>> Anything below 3 to red and below 1 to pink.
        html_injected_weather = self.visibility_color_code(html_injected_weather)
        # Alternate for ceilings text color >> HIGHLIGHT FOR ANYTHING BELOW 2000ft
        html_injected_weather = re.sub(self.BKN_OVC_PATTERN_alternate, self.yellow_highlight, html_injected_weather)

        if taf:     # This is for TAF only to add line breaks or empty spaces before FM block for HTML
            html_injected_weather = html_injected_weather.replace("FM", "<br>\xa0\xa0\xa0\xa0FM") if html_injected_weather else ""   # line break for FM section in TAF for HTML

        final_highlight = html_injected_weather
        return final_highlight

    def html_injected_weather(self, weather_raw):
        """ This function takes in either mock_test_data or weather_raw as dict with datis, metar, taf data.
            html injection is done here for highlighting purposes - LIFR, IFR, Alternate IFR, ATIS code, 
            altimeter settings, LLWS, RW in use, and such are highlighted in this function.
        """

        datis_raw = weather_raw.get('datis','N/A')
        metar_raw = weather_raw.get('metar')
        taf_raw = weather_raw.get('taf')
        

        highlighted_metar = self.color_code(metar_raw)
        highlighted_metar = re.sub(self.ALTIMETER_PATTERN, self.box_around_text, highlighted_metar) if highlighted_metar else ""
        
        highlighted_taf = self.color_code(taf_raw,taf=True)
        
        datis_collective = {}
        if isinstance(datis_raw,dict):
            for k,datis in datis_raw.items():
                if datis:
                    datis_collective[k] = {
                        'datis': self.color_code(datis),
                        'datis_zt': self.zulu_recency(datis, datis=True) if datis else "",
                        'datis_ts': self.zulu_extraction(datis, weather_type='datis') if datis else ""
                    }
                    
                    # Apply all the regex substitutions to the 'datis' field
                    processed_datis = datis_collective[k]['datis']
                    processed_datis = re.sub(self.ATIS_INFO, self.box_around_text, processed_datis) if processed_datis else ""
                    processed_datis = re.sub(self.ALTIMETER_PATTERN, self.box_around_text, processed_datis) if processed_datis else ""
                    processed_datis = re.sub(self.LLWS, self.yellow_warning, processed_datis) if processed_datis else ""
                    processed_datis = re.sub(self.RW_IN_USE, self.box_around_text, processed_datis) if processed_datis else ""
                    
                    datis_collective[k]['datis'] = processed_datis

        return dict({ 'datis': datis_collective,
                    
                    'metar': highlighted_metar, 
                    'metar_zt': self.zulu_recency(metar_raw) if metar_raw else "",
                    'metar_ts': self.zulu_extraction(metar_raw,weather_type='metar') if metar_raw else "",

                    'taf': highlighted_taf,
                    'taf_zt': self.zulu_recency(taf_raw,taf=True) if taf_raw else "",
                    'taf_ts': self.zulu_extraction(taf_raw,weather_type='taf') if taf_raw else "",
                    })
