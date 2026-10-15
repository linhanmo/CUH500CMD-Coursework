# ADVANCED ASSESSED TASK 3/3: Implement a Concurrent Headline Scraper

In the lecture this week there is an example of a concurrent application that reports the size of the data at different URLs.

You are given a non-concurrent Python program (in **ADVANCED-TASK-3-CODE**) that retrieves the first five headlines from several news websites using the `newspaper` module. Your task is to design and implement a **fully concurrent, fault-tolerant, scalable, and data-exporting** version of this program.

## Your requirements are

### 1. Implement a concurrent headline scraper

Use `concurrent.futures.ThreadPoolExecutor` to fetch headlines from all URLs **in parallel**, ensuring each URL is processed in its own worker thread and integrates correctly with the newspaper library.

### 2. Add robust error handling

Your program must gracefully handle:

- network timeouts,
- invalid URLs,
- parsing failures,
- missing article lists,
- and unexpected exceptions,

returning **structured error messages** instead of crashing.

### 3. Enforce a timeout per URL

Each site must be scraped under a strict time limit (e.g., **5 seconds**). If the timeout is exceeded, return a timeout result for that site.

### 4. Validate headline output

- Ensure each site returns **exactly five headlines** when possible.
- If fewer exist, return all available and **note the shortage**.
- Replace empty titles with `"Untitled Article"`.

### 5. Add performance benchmarking

Use `timeit` to measure the runtime of:

- the original non-concurrent version,
- your concurrent version (ThreadPoolExecutor),
- and a version using **ProcessPoolExecutor**.

Run **at least 10 iterations** and present a performance comparison.

### 6. Add scalability testing

Allow the user to supply a larger list of URLs (**20+ recommended**) and a **configurable number of worker threads**. Measure how performance changes as the number of URLs and threads increases.

### 7. Export results to JSON or CSV

After scraping all sites, export the results — including URLs, headlines, headline counts, errors, per-URL scrape times, and a timestamp — to either **JSON or CSV** format based on user selection, using Python's `json` or `csv` modules (or pandas if preferred).

## Additional functions

You should also implement **two additional advanced functions** that enhance robustness, analysis, or control of your concurrent scraper. This could include, but is not limited to:

- ⭕ per-domain **rate limiting**;
- ⭕ a **retry-with-backoff** mechanism;
- ⭕ cross-site **headline deduplication**;
- ⭕ detailed **per-URL profiling**;
- ⭕ dynamically **increase or decrease worker count** based on latency, error rates, or server response times;
- ⭕ temporarily **stop scraping a domain that repeatedly fails**, preventing resource waste and accidental DoS-like behaviour;
- ⭕ **detect duplicate articles** across different URLs.

## Environment setup

Select certified Python Codio stack, then run:

```bash
sudo apt update
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade Pillow
pip3 install newspaper3k
```

## REQUIRED CODE

```python
import newspaper
from newspaper import Article

def get_headlines():

    URLs = ['http://www.foxnews.com/',
            'http://www.cnn.com/',
            'http://www.derspiegel.de/',
            'http://www.bbc.co.uk/',
            'https://theguardian.com',]

    for url in URLs:
        result = newspaper.build(url, memoize_articles=False)
        print('\n''The headlines from %s are' % url, '\n')
        for i in range(1,6):
            art = result.articles[i]
            art.download()
            art.parse()
            print(art.title)

if __name__ == '__main__':
    import timeit
    elapsed_time = timeit.timeit("get_headlines()", setup="from __main__ import get_headlines", number=2)/2             
    print(elapsed_time)
```