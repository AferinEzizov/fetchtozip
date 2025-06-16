import httpx
import logging
import polars as pl

def fetch_data(
    base_url: str,
    rate_limit: int = 10,
    page_limit: int = 10
) -> pl.LazyFrame:
    """
    Fetch paginated data from an API and return the combined records as a Polars LazyFrame.

    Args:
        base_url (str): Base API URL without query params.
        rate_limit (int): Max number of pages to fetch.
        page_limit (int): Number of records per page.

    Returns:
        pl.LazyFrame: A Polars LazyFrame containing all combined records.
    """
    all_records = []

    for page in range(1, 10 + 1):
        url = f"{base_url}?page={page}&limit={page_limit}"
        logging.debug(f"Fetching {url}")
        response = httpx.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        if not data:
            logging.info(f"No more data at page {page}, stopping fetch.")
            break

        if not isinstance(data, list):
            raise ValueError("Expected list of records per page.")

        all_records.extend(data)
        logging.info(f"Fetched {len(data)} records from page {page}")

    logging.info(f"Total records fetched: {len(all_records)}")

    # Convert to Polars DataFrame and then to LazyFrame
    df = pl.DataFrame(all_records)
    lazy_df = df.lazy()
    return lazy_df
