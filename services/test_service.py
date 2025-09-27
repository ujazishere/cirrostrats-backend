from core.tests.mock_test_data import Mock_data

async def test_flight_deet_data_service(airportLookup: str = None):
    md = Mock_data()
    if not airportLookup:
        # Sends compolete test flight data
        md.flight_data_init()
        md.weather_data_init(html_injected_weather=True)
        return md.collective()
    else:
        # Sends for test data for airport lookups only -- returns test weather and nas data.
        md.flight_data_init()
        md.weather_data_init(html_injected_weather=True)
        return {'weather': md.weather, 'NAS': md.nas_singular_mock}