import requests
from datetime import datetime, timedelta
import pytz

def get_octopus_agile_daily_rates(gsp_group_id):
    """
    Fetches all Octopus Energy Agile rates for the entire day.

    Args:
        gsp_group_id (str): Your regional GSP Group ID (e.g., 'B' for East Midlands).

    Returns:
        dict: A dictionary of rates keyed by the start time, or None if an error occurs.
    """
    product_code = "AGILE-23-12-06"
    tariff_code = f"E-1R-{product_code}-{gsp_group_id}"
    
    # Get the start of the current day in UTC
    utc_today = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    period_from = utc_today.isoformat()
    period_to = (utc_today + timedelta(days=1)).isoformat()

    url = f"https://api.octopus.energy/v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/?period_from={period_from}&period_to={period_to}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        rates = {}
        for result in data.get('results', []):
            start_time_str = result['valid_from']
            rate_value = result['value_inc_vat']
            rates[start_time_str] = rate_value
            
        return rates

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching data: {e}")
        return None

# This allows you to test the script on its own if needed.
if __name__ == "__main__":
    your_gsp_group_id = "B"
    all_rates = get_octopus_agile_daily_rates(your_gsp_group_id)
    if all_rates:
        print("Daily rates fetched successfully:")
        for time, rate in all_rates.items():
            print(f"  {time}: {rate:.2f} p/kWh")
    else:
        print("Failed to retrieve daily rates.")