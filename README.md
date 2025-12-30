# RT URL Getter

A lightweight utility that searches DuckDuckGo for a list of queries and extracts the first result URL for each. Uses headless Chrome/Selenium in a Docker container.

## Use Case

Given a list of search queries (e.g., movie titles), this tool will:
1. Search each query on DuckDuckGo
2. Extract the first organic result URL
3. Output a CSV with the original query and corresponding URL

## Prerequisites

- Docker

## Quick Start

```bash
# Build the Docker image
docker build -t rt_url_selenium .

# Run the scraper
docker run --rm -v $(pwd):/app rt_url_selenium
```

### Running in Background (Detached Mode)

For long-running jobs or SSH sessions that may disconnect:

```bash
# Run detached
docker run -d --name rt_scraper -v $(pwd):/app rt_url_selenium

# Check progress (follow live)
docker logs -f rt_scraper

# Check progress (one-time snapshot)
docker logs rt_scraper

# When done, remove the container
docker rm rt_scraper
```

## Input Format

Create an `inputs.txt` file with one search query per line:

```
Text Search
Rotten Tomatoes Going My Way 1944
Rotten Tomatoes American Beauty 1999
Rotten Tomatoes Casablanca 1943
```

The first line is treated as a header and skipped. Empty lines are also ignored.

## Output Format

Results are written to `output.csv`:

```csv
query,url
Rotten Tomatoes Going My Way 1944,https://www.rottentomatoes.com/m/going_my_way
Rotten Tomatoes American Beauty 1999,https://www.rottentomatoes.com/m/american_beauty
Rotten Tomatoes Casablanca 1943,https://www.rottentomatoes.com/m/casablanca
```

## Configuration

### Limit Number of Queries (for testing)

Use the `LIMIT` environment variable to process only the first N queries:

```bash
docker run --rm -v $(pwd):/app -e LIMIT=5 rt_url_selenium
```

### Delay Between Requests

The default delay is 2 seconds between requests to avoid rate limiting. This can be modified in `scraper.py` by changing the `DELAY_BETWEEN_REQUESTS` constant.

## Progress Output

The scraper shows real-time progress:

```
Starting DuckDuckGo URL scraper...
Loaded 602 queries from /app/inputs.txt
Chrome driver initialized
[1/602] Searching: Rotten Tomatoes Going My Way 1944
  Found: https://www.rottentomatoes.com/m/going_my_way
[2/602] Searching: Rotten Tomatoes American Beauty 1999
  Found: https://www.rottentomatoes.com/m/american_beauty
...
Chrome driver closed
Results written to /app/output.csv
Successfully scraped 600/602 URLs
```

## Files

| File | Description |
|------|-------------|
| `Dockerfile` | Builds container with Python, Chrome, and ChromeDriver |
| `scraper.py` | Main scraping script |
| `requirements.txt` | Python dependencies (selenium) |
| `inputs.txt` | Input queries (one per line) |
| `output.csv` | Generated output with query-URL pairs |

## How It Works

1. Launches headless Chrome inside Docker
2. For each query in `inputs.txt`:
   - Navigates to DuckDuckGo search
   - Waits for results to load
   - Extracts the href from the first result link
3. Writes all results to `output.csv`

## Troubleshooting

### No output appearing
Make sure you're mounting the current directory: `-v $(pwd):/app`

### Rate limiting
If searches start failing, increase `DELAY_BETWEEN_REQUESTS` in `scraper.py`

### Timeout errors
DuckDuckGo's page structure may have changed. Check the CSS selectors in `search_duckduckgo()`.
