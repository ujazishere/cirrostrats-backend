from dj.dj_app.root.root_class import Root_class
import re
import pickle
from collections import Counter
import json
import requests
import os

# regex notes:
    # . is every character
    # * is as many characters
# Looking for probabilities and pattern.
# Try to find what follows what and how often. then try to see the surroundings of that two 
    # elements and how ofen they occor. keep looping

# load all datis
def load_em_all():
    base_path = r"C:\Users\ujasv\OneDrive\Desktop\pickles"
    all_pickle_files = os.listdir(base_path)            # get all file names in pickles folder
    # get just the ones with datis_info_stack in name
    datis_info_stack_file_names = [i for i in all_pickle_files if 'datis_info_stack' in i]

    datis_bulk = []
    for i in datis_info_stack_file_names:
        path = base_path+"\\"+ i
        with open(path, 'rb') as f:
            datis_bulk += pickle.load(f)
    print(f'total datis files: {len(datis_info_stack_file_names)}', f'total datis: {len(datis_bulk)}')
    return datis_bulk

datis_bulk = load_em_all()


datis_pattern = {'airport_id': r'[A-Z]{1,3} ',
'atis_info': r'(ATIS|ARR/DEP|DEP|ARR) INFO [A-Z] ',
'time_in_zulu': r'(\d{1,4}Z(\.| ))',        #4 digits followed by `Z`
'special_or_not': r'(SPECIAL\.)? ',    #SPECIAL then `.` or just `.`
'winds': r'((\d{5}(G|KT)(\d{2}KT)?)|VRB\d\dKT) ',    # winds that account for regular, variable and gusts
'variable_wind_direction': r'(\d{3}V\d{3} )?',
'SM': r'(M?((\d )?\d{1,2}/)?\d{1,2}SM )?',            # DOESNT ACCOUNT FOR FRACTIONALS
'TSRA_kind': r'(-|\+)?(RA|SN|TSRA|HZ|DZ)?(( )?BR)?( )?',
'vertical_visibility': r'',
# Right after SM there are light or heavy RA SN DR BR and vertical visibilities that need to be accounted for
'sky_condition': r'(((VV|FEW|CLR|BKN|OVC|SCT)(\d{3})?(CB)? ){1,10})?',       
'temperature': r'(M?\d\d/M?\d\d )',
'altimeter': r'A\d{4} \(([A-Z]{3,5}( |\))){1,4}(\. | )',      # Accounts for dictated bracs and trailing `. ` or just ` `
'RMK': r'(RMK(.*?)\. )?',
# 'trailing_atis': r'\.\.\.ADVS YOU HAVE INFO [A-Z]\.'
# 'simul_app': r'(SIMUL([A-Z]*)? )(([A-Z])* )*USE. ?',          # no digits SIMUL
                    }

# trim datis of pattern upto rmk section.
patt = ''.join([datis_pattern[i] for i in list(datis_pattern.keys())])
print(patt)
trimmed_datis = [re.sub(patt,'',i) for i in datis_bulk]

# Deleting all trailing crap.
rws_only = []
for y in trimmed_datis:
    aa = re.search('NOTAM?S?|NOTICES?|READ|(LAHSO|LAND AND HOLD SHORT OPERATIONS)|TWY|TWR|CTC|FREQ|BIRD|ADVS|(\. RWY (.*?)CONDITION CODE)|CLSD',y)
    rws_only.append(y[:aa.start()])

trimmed_datis = rws_only       

# this code will replace digits with `*` and show two uniq concurrent occurances sorted
tots = {}    # sentences with digits replaced with `*` showing only those that contain start
for i in trimmed_datis:
    for each_sentence in i.split('.'):
        # if sentance is not empty/ empty space:
        if each_sentence and each_sentence != ' ':
            # replace each digit with a star
            each_sentence_replaced_digs = ''.join(char if not char.isdigit() else '*' for char in each_sentence)
            # if there are digits/stars in the sentence:
            if '*' in each_sentence_replaced_digs:
                split_stn = each_sentence_replaced_digs.split()
                total_splits = len(split_stn)
                for indices in range(total_splits):
                    item_itself = split_stn[indices]
                    if indices == 0:        # if its the first item 
                        uniq_twos = '<bw>' + item_itself
                    elif indices == (total_splits-1):     # its its the last item
                        uniq_twos = item_itself + '</ew>'
                    else:                   # if items are in the middle
                        item_itself_2 = split_stn[indices+1]    # this is the following word
                        uniq_twos = item_itself + ' ' + item_itself_2
                    rw_title = r'R( Y|Y|WY|UNWAY)S?'
                    found = re.search(rw_title,uniq_twos)
                    if not found:
                        tots[uniq_twos] = tots.get(uniq_twos,0)+1

oth = []
for i in tots.keys():
    if i[0] == 'R':
        oth.append(i.split()[0])
Counter(oth)

# This one finds all unique words that are not digits
tots = {}
for i in trimmed_datis:
    for each_sentence in i.split('.'):
        # if sentance is not empty/ empty space:
        if each_sentence and each_sentence != ' ':
            # replace each digit with a star
            each_sentence_replaced_digs = ''.join(char if not char.isdigit() else '*' for char in each_sentence)
            # if there are digits/stars in the sentence:
            if '*' in each_sentence_replaced_digs:
                split_stn = each_sentence_replaced_digs.split()
                total_splits = len(split_stn)
                for indices in range(total_splits):
                    item_itself = split_stn[indices]
                    matches=re.search(r'\*',item_itself)
                    if not matches:     # If theyre not digits then unique those words
                        tots[item_itself] = tots.get(item_itself,0)+1

# this is to find items around digits
tots = {}
for i in trimmed_datis:
    for each_sentence in i.split('.'):
        # if sentance is not empty/ empty space:
        if each_sentence and each_sentence != ' ':
            # replace each digit with a star
            each_sentence_replaced_digs = ''.join(char if not char.isdigit() else '*' for char in each_sentence)
            # if there are digits/stars in the sentence:
            if '*' in each_sentence_replaced_digs:
                split_stn = each_sentence_replaced_digs.split()
                total_splits = len(split_stn)
                for indices in range(total_splits):
                    item_itself = split_stn[indices]
                    matches=re.search(r'\*',item_itself)
                    if matches:         # If that one item has digit/start
                        if indices == 0:        # if its the first item 
                            uniq_twos = '<bw>' + item_itself
                        elif indices == (total_splits-1):     # its its the last item
                            uniq_twos = item_itself + '</ew>'
                        else:                   # if items are in the middle
                            item_before = split_stn[indices-1]
                            item_itself_2 = split_stn[indices+1]    # this is the following word
                            uniq_twos =item_before + ' ' + item_itself + ' ' + item_itself_2
                        
                        # What is this sorcery?
                        rw_title = r'R( Y|Y|WY|UNWAY)S?'
                        found = re.search(rw_title,uniq_twos)
                        if not found:
                            tots[uniq_twos] = tots.get(uniq_twos,0)+1
extracted_pattern = r'VIS(UAL)?|ILS|AP(PROA)?CH(ES)?|ARR(IVALS)?|DEPG?(ART(ING|URES))?'

def extra():
    # get all indices of rws. 
    flattened_datis_string = ''.join(trimmed_datis)              # Flatten datis into one string
    def get_runway_indices(flattened_datis_string):
        rw_patt = r"\d{1,2}(R|L|C)?"
        indices = []
        matches = re.finditer(rw_patt, flattened_datis_string)
        for match in matches:
            indices.append(match.start())
        return indices

    # lists upto 10 chars either side that surrounds rw
    def rw_surroundings():
        rw_indices = get_runway_indices(flattened_datis_string)
        rw_surroundings = []        
        for i in rw_indices:
            rw_surroundings.append(flattened_datis_string[i-10:i+10])
        return rw_surroundings

    # get first item thats right before the runway.
    def first_item_before_rw():
        tots = {}
        for i in rw_surroundings():
            i = i.split()
            for indices in range(len(i)):
                each_ele = i[indices]
                if re.search(r'\d{1,2}(R|L|C)?',each_ele):
                    if indices != 0:
                        uniq = i[indices-1]
                        tots[uniq] = tots.get(uniq,0) + 1
        return Counter(tots)
    first_item_before_rw()
    # investigate r'ILS|DEP(G|ART)?|LANDING|LNDG|ARRIVALS|APCH|VISUAL|IN USE'
        # use this pattern to extract sentences and analyze them for uniques

new_rw_in_use = r'(EXP(C)? )?(SIMUL([A-Z]*)?,?|VIS(UAL)? ((AP(P)?(ROA)?CH(E)?(S)?))?|(ILS(/VA|,)?|(ARRIVALS )?EXPECT|RNAV|((ARVNG|LNDG) AND )?DEPG|LANDING)) ((.*?\d{1,2}(R|L|C)?.*?)|VISUAL |)(IN USE\.|((RWY|RY|RUNWAY|APCH|ILS|DEP|VIS) )((\d{1,2}(R|L|C)?)(, )?){1,5}\.)'
rw_title = r'R( Y|Y|WY|UNWAY)S?'
anal = r'(ILS|RNAV|RWY|IN USE|DEP|ARR|VIS)'
# Needs a lot of work
rw_in_between = r'(.*?\d{1,2}(R|L|C)?.*?)'
runways = r'\d{1,2}(R|L|C)?'
running_rw_in_use = r'()((SIMUL([A-Z]*)?,?|VIS(UAL)? (AP(P)?(ROA)?CH(E)?(S)?)|(ILS(/VA|,)?|(ARRIVALS )?EXPECT|RNAV|((ARVNG|LNDG) AND )?DEPG|LANDING)) (.*?\d{1,2}(R|L|C)?.*?)(IN USE\.|((RWY|RY|RUNWAY|APCH|ILS|DEP|VIS) )(\d{1,2}(R|L|C)?)\.))'

running_rw_in_use = r'()((SIMUL([A-Z]*)?,?|VISUAL (AP(P)?(ROA)?CH(E)?(S)?)|(ILS(/VA|,)?|(ARRIVALS )?EXPECT|RNAV|((ARVNG|LNDG) AND )?DEPG|LANDING)) (.*?\d{1,2}(R|L|C)?.*?)(IN USE\.|((RWY|RY|RUNWAY|APCH|ILS|DEP|VIS) )(\d{1,2}(R|L|C)?)\.))'
exp = r'(SIMUL([A-Z]*)?,?|VISUAL (AP(P)?(ROA)?CH(E)?(S)?)|(ILS(/VA|,)?|(ARRIVALS )?EXPECT|RNAV|((ARVNG|LNDG) AND )?DEPG|LANDING)) (.*?)(IN USE\.|R(UN)?(W)?(A)?( )?Y(S)?,?|APCH|ILS|DEP(P)?(ARTING)?|VIS(UAL)?)( )((, )?\d{1,2}(R|L|C)?){1,5}\.'
rw_ending = r'(VIS(UAL)?|DEP(P)?(ARTING)?|R(UN)?(W)?(A)?( )?Y(S)?,?|APCH)(?#begs end here)( )((, )?\d{1,2}(R|L|C)?){1,5}\.'
rw_in_use = r'(SIMUL([A-Z ]*)?,? |VISUAL (APCH)|(ILS(/VA|,)?|(ARRIVALS )?EXPECT|RNAV|((ARVNG|LNDG) AND )?DEPG|LANDING)) (.*?)(IN USE\.?|((RWY|RY|RUNWAY|APCH|ILS|DEP|,) )(\d{1,2}(R|L|C)?)\.)'
useful_pattern = r'^(.*?)\.'        # Matches beginning of line to the next .
# funky patter  2,6,13,16,18,20,22,25, 32,35,37, 46,47, 52, 59, 67, 68, 71, 72, 75

patt_match = {
    'SIMUL': r'SIMUL([A-Z]*)?,?\.?',

    }

all_datis_airports_path = r'c:\users\ujasv\onedrive\desktop\codes\cirrostrats\all_datis_airports.pkl'
with open(all_datis_airports_path, 'rb') as f:
    all_datis_airports = pickle.load(f)

# old synchronous series wise ineficient pull. New one is async_datis_extracts
def datis_scrape():

    def datis_raw_data(airport_id):
        datis_api =  f"https://datis.clowd.io/api/{airport_id}"
        datis = requests.get(datis_api)
        datis = json.loads(datis.content.decode('utf-8'))
        datis_raw = 'n/a'
        if type(datis) == list and 'datis' in datis[0].keys():
            datis_raw = datis[0]['datis']
        return datis_raw


    datis_info_stack = []
    for each_id in all_datis_airports:
        datis_info_stack.append(datis_raw_data(each_id))
    
    return datis_info_stack
