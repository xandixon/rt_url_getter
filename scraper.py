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


def load_completed_queries(filepath):
    """Load already-completed queries from existing output file."""
    completed = set()
    if not os.path.exists(filepath):
        return completed

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if row:
                    completed.add(row[0])
    except Exception as e:
        print(f"Warning: Could not read existing output file: {e}")

    return completed


def main():
    print("Starting DuckDuckGo URL scraper...")

    # Read input queries
    all_queries = read_inputs(INPUT_FILE)
    if LIMIT > 0:
        all_queries = all_queries[:LIMIT]
        print(f"Limited to {len(all_queries)} queries (LIMIT={LIMIT})")
    else:
        print(f"Loaded {len(all_queries)} queries from {INPUT_FILE}")

    # Check for existing progress and resume
    completed_queries = load_completed_queries(OUTPUT_FILE)
    if completed_queries:
        print(f"Found {len(completed_queries)} already completed queries, resuming...")

    # Filter out already-completed queries
    queries = [q for q in all_queries if q not in completed_queries]
    if not queries:
        print("All queries already completed!")
        return

    print(f"Processing {len(queries)} remaining queries...")

    # Ensure output file exists with header
    if not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["query", "url"])

    # Create driver
    driver = create_driver()
    print("Chrome driver initialized")

    successful = 0
    processed = 0

    try:
        for i, query in enumerate(queries, 1):
            total_progress = len(completed_queries) + i
            print(f"[{total_progress}/{len(all_queries)}] Searching: {query}", flush=True)

            url = search_duckduckgo(driver, query)
            processed += 1

            if url:
                print(f"  Found: {url}", flush=True)
                successful += 1

            # Write result immediately to CSV (append mode)
            with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([query, url])

            # Delay between requests to avoid rate limiting
            if i < len(queries):
                time.sleep(DELAY_BETWEEN_REQUESTS)

    finally:
        driver.quit()
        print("Chrome driver closed")

    print(f"Session complete: scraped {successful}/{processed} URLs successfully")
    print(f"Total progress: {len(completed_queries) + processed}/{len(all_queries)} queries completed")


if __name__ == "__main__":
    main()
