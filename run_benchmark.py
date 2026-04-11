import asyncio
import time
import sqlite3
import pandas as pd
import os
import sys
from scraper import GrandmasterScraper

async def run_benchmark(niche, location, count):
    print(f"🚀 Starting benchmark for {count} leads in {niche} ({location})...")
    start_time = time.time()
    
    scraper = GrandmasterScraper(niche, location, count)
    results = await scraper.run()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n--- 🏁 Benchmark Finished 🏁 ---")
    print(f"Total Leads Secured: {len(results)}")
    print(f"Total Time Taken: {duration:.2f} seconds")
    if len(results) > 0:
        print(f"Average Time per Lead: {duration/len(results):.2f} seconds")
    
    # Save to a specific benchmark file


    df = pd.DataFrame(results)
    df.to_csv("benchmark_results.csv", index=False, encoding='utf-8-sig')
    print(f"Results saved to benchmark_results.csv")

if __name__ == "__main__":
    niche = "Real Estate"
    location = "London"
    count = 50
    asyncio.run(run_benchmark(niche, location, count))
