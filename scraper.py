#!/usr/bin/env python3
"""
DuckDuckGo URL Scraper - Extracts first search result URL for each query.
"""

import csv
import os
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

INPUT_FILE = "/app/inputs.txt"
OUTPUT_FILE = "/app/output.csv"
DELAY_BETWEEN_REQUESTS = 2  # seconds
LIMIT = int(os.environ.get("LIMIT", 0))  # 0 = no limit


def create_driver():
    """Create a headless Chrome driver."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    return driver


def search_duckduckgo(driver, query):
    """Search DuckDuckGo and return the first result URL."""
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://duckduckgo.com/?q={encoded_query}"

    driver.get(url)

    try:
        # Wait for search results to load
        # DuckDuckGo uses data-testid="result" for result containers
        wait = WebDriverWait(driver, 10)

        # Try to find the first organic result link
        # DuckDuckGo structure: article[data-testid="result"] contains the result
        # The actual link is in a[data-testid="result-title-a"]
        first_result = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="result"] a[data-testid="result-title-a"]'))
        )

        href = first_result.get_attribute("href")
        return href

    except TimeoutException:
        print(f"  Timeout waiting for results for: {query}")
        return ""
    except NoSuchElementException:
        print(f"  No results found for: {query}")
        return ""


def read_inputs(filepath):
    """Read queries from input file, skipping header row."""
    queries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            # Skip empty lines and header row
            if not line or i == 0 or line == "Text Search":
                continue
            queries.append(line)
    return queries


def main():
    print("Starting DuckDuckGo URL scraper...")

    # Read input queries
    queries = read_inputs(INPUT_FILE)
    if LIMIT > 0:
        queries = queries[:LIMIT]
        print(f"Limited to {len(queries)} queries (LIMIT={LIMIT})")
    else:
        print(f"Loaded {len(queries)} queries from {INPUT_FILE}")

    # Create driver
    driver = create_driver()
    print("Chrome driver initialized")

    results = []

    try:
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] Searching: {query}")

            url = search_duckduckgo(driver, query)
            results.append((query, url))

            if url:
                print(f"  Found: {url}")

            # Delay between requests to avoid rate limiting
            if i < len(queries):
                time.sleep(DELAY_BETWEEN_REQUESTS)

    finally:
        driver.quit()
        print("Chrome driver closed")

    # Write results to CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["query", "url"])
        writer.writerows(results)

    print(f"Results written to {OUTPUT_FILE}")
    print(f"Successfully scraped {sum(1 for _, url in results if url)}/{len(results)} URLs")


if __name__ == "__main__":
    main()
