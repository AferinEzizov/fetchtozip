import httpx
import logging
import polars as pl
import asyncio

# Limit concurrency to avoid exhausting httpx connection pool (prevents PoolTimeout)
CONCURRENCY_LIMIT = 3

async def fetch_page(client: httpx.AsyncClient, url: str, page: int, page_limit: int, semaphore: asyncio.Semaphore) -> list:
    fetch_url = f"{url}?page={page}&limit={page_limit}"
    async with semaphore:
        logging.debug(f"Fetching {fetch_url}")
        try:
            resp = await client.get(fetch_url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                logging.info(f"No more data at page {page}, stopping fetch.")
                return []
            if not isinstance(data, list):
                raise ValueError("Expected list of records per page.")
            logging.info(f"Fetched {len(data)} records from page {page}")
            return data
        except httpx.TimeoutException as e:
            logging.warning(f"Timeout while fetching {fetch_url}: {e}")
            return []
        except Exception as e:
            logging.error(f"Error while fetching {fetch_url}: {e}")
            return []

async def fetch_data_async(
    base_url: str,
    rate_limit: int = 10,
    page_limit: int = 10
) -> pl.LazyFrame:
    """
    Asynchronously fetch paginated data from an API and return the combined records as a Polars LazyFrame.

    Args:
        base_url (str): Base API URL without query params.
        rate_limit (int): Max number of pages to fetch.
        page_limit (int): Number of records per page.

    Returns:
        pl.LazyFrame: A Polars LazyFrame containing all combined records.
    """
    all_records = []
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=CONCURRENCY_LIMIT)) as client:
        tasks = [
            fetch_page(client, base_url, page, page_limit, semaphore)
            for page in range(1, rate_limit + 1)
        ]
        results = await asyncio.gather(*tasks)
        for data in results:
            all_records.extend(data)

    logging.info(f"Total records fetched: {len(all_records)}")
    df = pl.DataFrame(all_records)
    lazy_df = df.lazy()
    return lazy_df

def fetch_data(
    base_url: str,
    rate_limit: int = 10,
    page_limit: int = 10
) -> pl.LazyFrame:
    """
    Synchronous wrapper for fetch_data_async.
    """
    return asyncio.run(fetch_data_async(base_url, rate_limit, page_limit))
