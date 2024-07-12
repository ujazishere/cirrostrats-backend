from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
import routes.route as route

app = FastAPI()

app.include_router(route.router)

origins = [
    "http://localhost:5173"
    "http://127.0.0.1:8000"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)


@app.get("/")
def root():
    return {"message": "Hello World"}
# @app.post('/items')
# async def create_item(item: Item):
#     items.append(item)
#     return items

# @app.get('/us-airports')
# async def us_airports():
#     response = await get_airports()
#     return response


# returns a defined item class


# @app.get('/items', response_model=list[Item])
# def list_items(limit: int = 10):
#     return items[0:limit]


# @app.get('/items')
# async def get_item():
#     return items


# @app.get('/items/{item_id}', response_model=Item)
# async def get_item(item_id: int) -> Item:
#     if item_id < len(items):
#         return items[item_id]
#     else:
#         raise HTTPException(status_code=404, detail=f"Item {
#                             item_id} not found")


# @app.get("/flight")
# def get_flight():


# @app.get("/")
# def get_flight_details():
#     # Loading the dummy data here. This is a deeply nested dictionary that gets fed into front end as a JSON deeply nested Object
#     # with open("dummy_flight_deet.pkl", 'rb') as f:
#     #     bulk_flight_deets = pickle.load(f)

#     # return bulk_flight_deets


# @app.get("/flight/{flight_id}")
# def get_flight(flight_id):
#     # Loading the dummy data here. This is a deeply nested dictionary that gets fed into front end as a JSON deeply nested Object
#     with open("dummy_flight_deet.pkl", 'rb') as f:
#         bulk_flight_deets = pickle.load(f)

#     return bulk_flight_deets


# @app.get("/us-airports")
# def all_airports():

#     print("Getting all US airports")
#     # Loading the dummy data here. This is a deeply nested dictionary that gets fed into front end as a JSON deeply nested Object
#     with open("all_US_airports_dict.pkl", 'rb') as f:
#         airports = pickle.load(f)

#     return airports


# @app.get("/gate-info")
# def all_airports():

#     # Loading the dummy data here. This is a deeply nested dictionary that gets fed into front end as a JSON deeply nested Object
#     with open("gate_info_data.pkl", 'rb') as f:
#         gate_info = pickle.load(f)
#         # print(gate_info.keys())
#         # gate_info = gate_info.keys()

#     return gate_info


# @app.get("/dep_dest")
# def root():

#     with open("dummy_flight_deet.pkl", 'rb') as f:
#         bulk_flight_deets = pickle.load(f)

#     return {'departure_ID': bulk_flight_deets['departure_ID'], 'destination_ID': bulk_flight_deets['destination_ID']}


# @app.get("/scheduled_times")
# def root():

#     with open("dummy_flight_deet.pkl", 'rb') as f:
#         bulk_flight_deets = pickle.load(f)

#     return {"scheduled_departure_time": bulk_flight_deets["scheduled_departure_time"],
#             "scheduled_arrival_time": bulk_flight_deets["scheduled_arrival_time"]}


# @app.get("/gates")
# def root():

#     with open("dummy_flight_deet.pkl", 'rb') as f:
#         bulk_flight_deets = pickle.load(f)

#     return {"departure_gate": bulk_flight_deets["departure_gate"],
#             "arrival_gate": bulk_flight_deets["arrival_gate"]}


# @app.get("/dep_weather")
# def root():

#     with open("dummy_flight_deet.pkl", 'rb') as f:
#         bulk_flight_deets = pickle.load(f)
#     dep_weather = bulk_flight_deets[dep_weather]
#     return dep_weather


# @app.get("/nas_departure_affected")
# def root():

#     with open("dummy_flight_deet.pkl", 'rb') as f:
#         bulk_flight_deets = pickle.load(f)
#     nas_departure_affected = bulk_flight_deets['nas_departure_affected']
#     return nas_departure_affected


# @app.get("/dest_weather")
# def root():

#     with open("dummy_flight_deet.pkl", 'rb') as f:
#         bulk_flight_deets = pickle.load(f)
#     dest_weather = bulk_flight_deets['dest_weather']
#     return dest_weather


# @app.get("/flight_aware_data")
# def root():

#     with open("dummy_flight_deet.pkl", 'rb') as f:
#         bulk_flight_deets = pickle.load(f)

#     flight_aware_data = {"origin": bulk_flight_deets["origin"],
#                          "destination": bulk_flight_deets["destination"],
#                          "registration": bulk_flight_deets["registration"],
#                          "scheduled_out": bulk_flight_deets["scheduled_out"],
#                          "estimated_out": bulk_flight_deets["estimated_out"],
#                          "scheduled_in": bulk_flight_deets["scheduled_in"],
#                          "estimated_in": bulk_flight_deets["estimated_in"],
#                          "route": bulk_flight_deets["route"],
#                          "filed_altitude": bulk_flight_deets["filed_altitude"],
#                          "filed_ete": bulk_flight_deets["filed_ete"],
#                          "sv": bulk_flight_deets["sv"], }

#     return flight_aware_data
