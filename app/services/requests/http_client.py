import httpx
import polars as pl
import logging

def fetch_data(
    base_url: str,
    max_pages: int=10,
    page_size: int=10
) -> pl.LazyFrame:
    """
    Fetch all pages from a paginated API and combine results into one Polars LazyFrame.

    Args:
        base_url (str): API endpoint without query params, e.g. "http://localhost:3000/api/data"
        max_pages (int): Maximum number of pages to fetch to avoid infinite loops.
        page_size (int): Number of records per page.

    Returns:
        pl.LazyFrame: Combined lazy dataframe of all fetched pages.
    """
    lazy_frames = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}&limit={page_size}"
        logging.debug(f"Fetching {url}")
        response = httpx.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        if not data:
            logging.info(f"No more data at page {page}, stopping fetch.")
            break

        if not isinstance(data, list):
            raise ValueError("Expected list of records per page.")

        # Convert current page data to eager DataFrame
        df = pl.DataFrame(data)
        # Convert to lazy and append
        lazy_frames.append(df.lazy())
        logging.info(f"Fetched {len(data)} records from page {page}")

    if not lazy_frames:
        logging.warning("No data fetched from API.")
        return pl.LazyFrame([])

    # Concatenate all lazy frames (like vertical stack)
    combined_lazy = pl.concat(lazy_frames, how="vertical")
    logging.info(f"Total rows (lazy): {combined_lazy.collect().shape[0]}")

    return combined_lazy
