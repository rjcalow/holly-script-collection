import requests
from datetime import datetime
import pytz

def get_octopus_agile_rate(gsp_group_id):
    """
    Checks the current Octopus Energy Agile rate for a given GSP Group ID.

    Args:
        gsp_group_id (str): Your regional GSP Group ID (e.g., 'A' for Eastern England).

    Returns:
        float: The current electricity rate in p/kWh, or None if an error occurs.
    """
    # The current product code for the Agile tariff.
    product_code = "AGILE-23-12-06"  
    
    # Construct the tariff code with the GSP Group ID.
    tariff_code = f"E-1R-{product_code}-{gsp_group_id}"

    # Get the current time in UTC, which is what the API uses.
    utc_now = datetime.now(pytz.utc)
    
    # Format the time for the API request (ISO 8601 format).
    period_from = utc_now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Construct the API URL to get the latest standard unit rates.
    url = f"https://api.octopus.energy/v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/?period_from={period_from}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        
        # The API returns rates in reverse chronological order, so the first
        # element is the current half-hour's rate.
        if data['results']:
            current_rate = data['results'][0]['value_inc_vat']
            # The rate is in pence per kilowatt-hour (p/kWh)
            return current_rate
        else:
            print("No rate data found for the current time.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching data: {e}")
        return None

# --- Usage Example ---
# The GSP Group ID for ...., which is in the East Midlands, is B.
# your_gsp_group_id = "B" 
# current_rate_pkwh = get_octopus_agile_rate(your_gsp_group_id)

# if current_rate_pkwh is not None:
#     print(f"The current Octopus Agile rate is: {current_rate_pkwh:.2f} p/kWh")
# else:
#     print("Could not retrieve the current rate.")