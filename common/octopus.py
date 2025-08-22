import requests
from datetime import datetime, timedelta, timezone
import pytz

def fetch_all_products():
    """Fetch all Octopus products with pagination."""
    products = []
    page = 1
    while True:
        try:
            resp = requests.get("https://api.octopus.energy/v1/products/", params={"page": page})
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching products: {e}")
            return []
        
        data = resp.json()
        results = data.get("results", [])
        if not results:
            break

        products.extend(results)

        if not data.get("next"):
            break
        page += 1

    return products


def get_current_agile_product_code():
    """Return the most recent Agile tariff product code."""
    products = fetch_all_products()
    agile_products = [p for p in products if p["code"].startswith("AGILE")]

    if not agile_products:
        return None

    # Parse available_from safely
    for p in agile_products:
        af = p.get("available_from")
        if af:
            # Handle trailing Z for UTC
            if af.endswith("Z"):
                af = af.replace("Z", "+00:00")
            try:
                p["_af_dt"] = datetime.fromisoformat(af)
            except ValueError:
                p["_af_dt"] = datetime.min
        else:
            p["_af_dt"] = datetime.min

    agile_products.sort(key=lambda p: p["_af_dt"], reverse=True)
    return agile_products[0]["code"]


def get_octopus_agile_daily_rates(gsp_group_id: str):
    """
    Fetch all Agile rates for today (UTC day).

    Args:
        gsp_group_id (str): Regional GSP Group ID (e.g., 'B', 'M').

    Returns:
        dict: {timestamp: rate_inc_vat} or None on failure.
    """
    product_code = get_current_agile_product_code()
    if not product_code:
        print("No Agile product code found.")
        return None

    tariff_code = f"E-1R-{product_code}-{gsp_group_id}"

    # Define today's period in UTC with explicit Z
    utc_today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    period_from = utc_today.isoformat().replace("+00:00", "Z")
    period_to = (utc_today + timedelta(days=1)).isoformat().replace("+00:00", "Z")

    url = (
        f"https://api.octopus.energy/v1/products/{product_code}"
        f"/electricity-tariffs/{tariff_code}/standard-unit-rates/"
        f"?period_from={period_from}&period_to={period_to}"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Agile rates: {e}")
        return None

    results = data.get("results", [])
    if not results:
        print("No Agile rates returned (maybe too early in the day?).")
        return None

    rates = {r["valid_from"]: r["value_inc_vat"] for r in results}
    return rates


if __name__ == "__main__":
    # Example: Yorkshire (Worksop S81) uses GSP = "M"
    your_gsp_group_id = "M"
    all_rates = get_octopus_agile_daily_rates(your_gsp_group_id)

    if all_rates:
        london_tz = pytz.timezone("Europe/London")
        print("✅ Agile daily rates fetched successfully:")
        for time_str, rate in sorted(all_rates.items()):
            # Convert UTC → UK local time
            utc_time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            local_time = utc_time.astimezone(london_tz)
            print(f"  {local_time.strftime('%H:%M')} → {rate:.2f} p/kWh")
    else:
        print("❌ Failed to retrieve daily rates.")
