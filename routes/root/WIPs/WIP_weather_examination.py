import re
import torch
import pickle
import os
from collections import Counter

# CONCLUSION: Majors:

# use METAR DECODER on https://e6bx.com/metar-decoder/
# TODO: Attempt to derive the Typical_met pattern on the metar and the taf to determine prominent info:
         # VFR/IFR/LIFR; Freezing conditions, icing, stronger winds with gusts, reduce font size of less important information.
         # give ability to decode individual complex items.  
# POA: determine each item for typicality in the metar list form and put them all together in a seperate container.
    # Once that is done, sort the non-typical ones for typicality.
        # Repeat the process until exhaustion. sort these by most typical to the least typical.
        # The goal is to make use of the most typical metar items then color code by them

# Be careful these paths. Shortened path is only local to the vs code terminal but doesnt work on the main cmd terminal
metar_stack_pkl_path = r"C:\Users\ujasv\OneDrive\Desktop\codes\Cirrostrats\dj\dj_app\root\pkl\METAR_stack.pkl"
even_bulkier_metar_path = r"C:\Users\ujasv\OneDrive\Desktop\pickles\BULK_METAR_NOV_2023_.pkl"
with open(even_bulkier_metar_path, 'rb') as f:         
    met = pickle.load(f)

# This is for bulkier metar.
heavy_met_key = list(met.keys())[0]
heavy_metar = met[heavy_met_key]
shortened = heavy_metar[:5000]

# WIP
N = torch.zeros((3000,35),dtype=float)
P = torch.zeros((3000,35),dtype=float)
mm = heavy_metar
tots = {}
patt_stack = []
count = 0
for ind in range(len(mm)):
    each_metar = mm[ind]
    each_patt = []
    each_split = each_metar.split()
    for split_ind in range(len(each_split)):
        each_item = each_split[split_ind]
        
        digs = len(each_item)
        each_patt.append(digs)
        N[ind,split_ind] = digs # This one still needs to be tested. WIP

    if not each_patt in patt_stack:     # if each pattern is not in patt_stach then add it
        # patt_stack is declared and used as a bank of uniques
        patt_stack.append(each_patt)
        N[count,0] = mm.index(each_metar)      #add 0th column the index ofthat metar
        for i in range(len(each_patt)):         #1st column and on patt length
            N[count,i+1] = each_patt[i]
        count+= 1
    else:                               # if it is in patt_stack: add to its count
        
        # P[:,:]

        # add count to the unique patts.
        thing = str(each_patt)
        tots[thing] = tots.get(thing,0)+1       


"""
# unique visibilities and occourances. Caution. There are some that contains leading space before `SM`
ifr_frac_patt = r"(?<= )([1-2] \d/\d)?((0)?[0-2])?(SM)"  This will give you all SM with leading empty spaces
tots={}
for each_metar in heavy_metar:
    item = re.search(ifr_frac_patt,each_metar)
    if item:
        item = item.group()
        if item == 'SM':
            print(each_metar)
        tots[item] = tots.get(item,0)+1
"""
#pattern that leads with vervbghrtical vis, Auto and KT pattern
patt = r'(KT )?(\d\d )?(AUTO )?(\d \d/(\d)(\d)?)?(\d/\d)?(\d\d)?(\d)?SM '

kt_patt = r'KT (\d \d/(\d)(\d)?)?(\d/\d)?(\d\d)?(\d)?SM '
working_pattern = r"( [1-2] )?(\d/)?(\d)?(\d)(SM)"
ifr_frac_patt = r"(?<= )([1-2] \d/\d)?((0)?[0-2])?(SM)"
digit_and_fractional = r"(?<= )([1-2] \d/\dSM)(?= )"        # e.g: 2 1/2SM, 1 1/4SM
tots = {}
multiple_sm_item_metars = []
for each_metar in heavy_metar:
    vis_item = re.search(working_pattern,each_metar)
    if vis_item:
        vis_item = vis_item.group()
        tots[vis_item] = tots.get(vis_item,0) + 1
        
    else:
        SM_item = re.findall('SM',each_metar)
        if SM_item:
            if len(SM_item) == 2:
                multiple_sm_item_metars.append(each_metar)
                print('Multiple "SM" items in this metar')
            elif len(SM_item) == 1:
                SM_item_index = each_metar.index(SM_item)
                block_around_SM = each_metar[SM_item_index-7:SM_item_index+10]
            else:
                print('IMPOSSIBLE END', each_metar)
        else:
            'NO SM ITEM'

all_keys = list(tots.keys())

manageable_ones = []        # Keys that are only upto 200 max items.
for k,v in tots.items():
    if v<200:
        manageable_ones.append(k)



fancy_match = r"(?<= )(\d\dSM)(?= )"        # This matches preceding and next. essentially look forward and look back
odd_ball_matches = r"(?<! )(\d\dSM )(?!S)"  # This matches all that does not have a leading space and trailing S
odd_ball = "KASG 260148Z 13003KT FEW120SM CLR 08/03 A3000"
leading_space = r"(?<= )"
trailing_space = r"(?= )"
two_digit_sm_less_than_10 = r"((?<= )0\dSM(?= ))"


fractional_odd_balls = r"(?<! )\d \d/\dSM"       # This one matches all fractionals with space that has a leading digit
patt_dec_3_latest = r"((?<= )(\d\d)(?= ))?(\d \d/\d)?(\d/\d)?(\d\d)?(SM)"
# investigate odd looking visibilities
SM_PATTERN_fractions = r"( [0-2] )?(\d/\d{1,2})SM"          # maps fractional visibilities between 1 and 3
SM_PATTERN_two_digit = r"^[0-9]?[0-9]SM"          # valid 1 and 2 digit visibility
odd_ball = []
for each in all_keys:
    fractional_item = re.search(SM_PATTERN_fractions, each)
    if fractional_item:
        print('Fractional item:', fractional_item.group())
    else:
        item2 = re.search(SM_PATTERN_two_digit, each)
        if item2:
            print('Two digit SM:', each)
        else:
            print('odd_ball:', each)
            odd_ball.append(each)









# This is from the old lighter metar stack I suppose.
all_metar_list = [i.split() for i in met]       # List of lists: Bulk metar in the list form. Each metar is also a list of metar items.

typical_metar_item = []
for i in all_metar_list:
    item_index = 3
    typical_metar_item.append(i[item_index])

# The first prominent item is the 4 letter ICAO airport ID. It semes TAF got in there somehow.
# Removing the metar items that dont have first letter as 'K' or is not 4 letters long.
len(all_metar_list)             # printing len to compare before and after the loop to see what was popped
for individual_full_metar in all_metar_list:
    airport_id = individual_full_metar[0]
    first_leter_of_airport_id = airport_id[0]
    if len(airport_id) != 4 and first_leter_of_airport_id != 'K':
        outlaw_metar = individual_full_metar
        all_metar_list.pop(all_metar_list.index(outlaw_metar))

len(all_metar_list)             # comparing how many items were removed.

# second prominent item of the metar is date and time DDTTTTZ. seems like all of the second prominent item is always going to be zulu time.
for individual_full_metar in all_metar_list:
    datetime = individual_full_metar[1]
    z_in_datetime = individual_full_metar[1][-1]
    if len(datetime) != 7 and z_in_datetime != 'Z':    # conditions for it to be reliable:
        outlaw_metar = individual_full_metar
        outlaw_metar_index = all_metar_list.index(outlaw_metar)
        all_metar_list.pop(outlaw_metar_index)

"""
# Third prominent item is the AUTO or not item. if its not AUTO its usually winds with gust.
# Another significant BLUEPRINT!!!!
class Auto_or_not:
    auto_items = []
    not_auto = []
    others = []
    for individual_full_metar in all_metar_list:
        auto_as_third_item = individual_full_metar[2]
        if auto_as_third_item == 'AUTO':
            auto_items.append(auto_as_third_item)
        elif auto_as_third_item != 'AUTO':
            not_auto.append(auto_as_third_item)
        else:
            others.append(auto_as_third_item)
x = Auto_or_not()
len(x.auto_items)
len(x.not_auto)
len(x.others)
"""

class Auto:
    new_all_metar_list = []
    not_auto = []
    for individual_full_metar in all_metar_list:
        auto_as_third_item = individual_full_metar[2]
        if auto_as_third_item == 'AUTO':    # If 'AUTO' then remove it
            individual_full_metar.pop(2)
            new_all_metar_list.append(individual_full_metar)
        elif auto_as_third_item != 'AUTO':
            not_auto.append(auto_as_third_item)
            new_all_metar_list.append(individual_full_metar)

auto = Auto()

all_metar_list = auto.new_all_metar_list

new_aml = []
wind_index = 2
for each_metar in all_metar_list:
    wind_item = each_metar[wind_index]
    if 'KT' in wind_item:
        if len(wind_item) == 7 or 'G' in wind_item:
            each_metar.pop(wind_index)
            new_aml.append(each_metar)
        else:
            new_aml.append(each_metar)
    else:
        new_aml.append(each_metar)

all_metar_list = new_aml

# 5th prominent item is visibility.
new_aml = []
vis_index = 2
for each_metar in all_metar_list:
    visibility = each_metar[vis_index]
    if 'SM' in visibility:
        each_metar.pop(vis_index)
        new_aml.append(each_metar)
    else:
        new_aml.append(each_metar)
all_metar_list.append()

altimeter_setting = r"\w{1}\d{4})"

# Seperate Metar after Temp and altimeter

# The following will allow for extracting unique items and their count.

# counter = Counter(x.not_auto)
# unique = counter.keys()

"""
metar MakeMore version using Andrej's technique
mm= 0   # this is dummy replace with acgual metar data. 
N = torch.zeros((3000,35),dtype=float)
P = torch.zeros((3000,35),dtype=float)

tots = {}
patt_stack = []
count = 0
for ind in range(len(mm)):
    each_metar = mm[ind]
    each_patt = []
    each_split = each_metar.split()
    for split_ind in range(len(each_split)):
        each_item = each_split[split_ind]
        
        digs = len(each_item)
        each_patt.append(digs)
        # N[ind,split_ind] = digs # This one still needs to be tested.

    if not each_patt in patt_stack:     # if each pattern is not in patt_stach then add it
        # patt_stack is declared and used as a bank of uniques
        patt_stack.append(each_patt)
        N[count,0] = mm.index(each_metar)      #add 0th column the index ofthat metar
        for i in range(len(each_patt)):         #1st column and on patt length
            N[count,i+1] = each_patt[i]
        count+= 1
    else:                               # if it is in patt_stack: add to its count
        
        # P[:,:]

        # add count to the unique patts.
        thing = str(each_patt)
        tots[thing] = tots.get(thing,0)+1       
"""

# Seems unnecessary. 
class Typical_met:                          # analyzing the first metar in the bulk metar list
    typical_complete_metar = all_metar_list[0]         # First metar from the all metar bulk list
    id = all_metar_list[0][0]
    zulu_time = all_metar_list[0][1]
    z_in_time = zulu_time[-1]
    auto_or_not = all_metar_list[0][2]
    winds = all_metar_list[0][3]




















