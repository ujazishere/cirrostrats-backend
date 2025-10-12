# routes/register.py
from routes import  search_routes, test_routes, weather_routes, notification_routes, gate_routes, flight_aggregator_routes, misc_route

def register_routes(app):
    app.include_router(search_routes.router)
    app.include_router(test_routes.router)
    app.include_router(weather_routes.router)
    app.include_router(notification_routes.router)
    app.include_router(gate_routes.router)
    app.include_router(flight_aggregator_routes.router)
    app.include_router(misc_route.router)

