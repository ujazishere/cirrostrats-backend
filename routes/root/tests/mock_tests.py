import pickle
from routes.route import aws_jms

with open('mock_ajms_data.pkl','rb') as f:
    data = pickle.load(f)

for each_flight_data in data:
    await aws_jms(flight_number=None, mock=True)
