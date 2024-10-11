
from dj.dj_app.root.weather_parse import Weather_parse
from dj.dj_app.root.dep_des import Pull_flight_info


wp = Weather_parse()
flt_info = Pull_flight_info()

a = wp.processed_weather('KEWR')
b = flt_info.flight_view_gate_info('4433','KEWR')
c = flt_info.fs_dep_arr_timezone_pull('4433')
d = flt_info.nas_final_packet('KLAS','KEWR')