import requests
from datetime import datetime, timedelta
import pytz

def get_current_agile_product_code():
    """Fetches the current Agile tariff product code from the API."""
    url = "https://api.octopus.energy/v1/products/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        products = response.json().get('results', [])
        
        # Find the product that is Agile and is active
        for product in products:
            if product['code'].startswith('AGILE') and product['is_active']:
                return product['code']
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching product code: {e}")
        return None

def get_octopus_agile_daily_rates(gsp_group_id):
    """
    Fetches all Octopus Energy Agile rates for the entire day.

    Args:
        gsp_group_id (str): Your regional GSP Group ID (e.g., 'B' for East Midlands).

    Returns:
        dict: A dictionary of rates keyed by the start time, or None if an error occurs.
    """
    product_code = get_current_agile_product_code()
    if not product_code:
        print("Could not find a valid Agile product code.")
        return None

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
            rates[result['valid_from']] = result['value_inc_vat']
        return rates

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching data: {e}")
        return None