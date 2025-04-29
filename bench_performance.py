import time
import statistics
import gc
from typing import List, Callable, Tuple

from blacksheep.url import URL as NewURL  # Your new implementation
from blacksheep.urlb import URL as LastUrl
# URLs to test (include a variety of case scenarios)



TEST_URLS = [
    b"https://example.com/path/to/resource?query=value&another=123#fragment",
    b"http://localhost:8080/api/v1/users",
    b"https://user:password@example.org:8443/admin?filter=active",
    b"/relative/path/to/resource?sort=desc",
    b"https://very-long-subdomain.another-subdomain.example.com/path/with/many/segments/and/a/very/long/path?with=many&query=parameters&that=are&quite=long&as=well#and-fragment",

    b"https://192.168.1.1:8080/network/path",
    b"https://example.com",
    b"https://example.com/",
    b"https://example.com:443"
]


def run_new_url_parse(urls: List[bytes]) -> List[NewURL]:
    """Parse URLs using the new implementation."""
    results = []
    for url in urls:
        try:
            parsed = NewURL(url)
            results.append(parsed)
        except Exception as ex:
            results.append(ex)
    return results
def run_httptools_parse(urls: List[bytes]) -> List[object]:
        """Parse URLs using the original httptools implementation."""
        results = []
        for url in urls:
            try:
                parsed =  LastUrl(url)
                results.append(parsed)
            except Exception as ex:
                results.append(ex)
        return results

def benchmark_function(func: Callable, args: Tuple, iterations: int = 10000) -> float:
    """Benchmark a function by running it multiple times and measuring execution time."""
    # Warm up
    for _ in range(min(100, iterations // 10)):
        func(*args)

    # Collect garbage to ensure fair comparison
    gc.collect()

    # Time the actual runs
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args)
        end = time.perf_counter()
        times.append(end - start)

    return statistics.mean(times)

def main():
    # Number of iterations for each benchmark
    iterations = 10000000

    print(f"Benchmarking URL parsing with {iterations} iterations per URL...")
    print(f"Testing {len(TEST_URLS)} different URLs\n")

    total_old = 0
    total_new = 0

    # Run benchmarks for each URL
    for i, url in enumerate(TEST_URLS):
        print(f"URL {i+1}: {url.decode()[:60]}{'...' if len(url) > 60 else ''}")

        # Test old implementation
        old_time = benchmark_function(LastUrl, (url,), iterations)
        total_old += old_time

        # Test new implementation
        new_time = benchmark_function(NewURL, (url,), iterations)
        total_new += new_time

        # Calculate improvement
        improvement = (old_time - new_time) / old_time * 100

        print(f"  Old implementation: {old_time:.8f} seconds per iteration")
        print(f"  New implementation: {new_time:.8f} seconds per iteration")
        print(f"  Improvement: {improvement:.2f}%")
        print()

    # Overall statistics
    overall_improvement = (total_old - total_new) / total_old * 100
    print("Overall Results:")
    print(f"  Old implementation total: {total_old:.8f} seconds")
    print(f"  New implementation total: {total_new:.8f} seconds")
    print(f"  Overall improvement: {overall_improvement:.2f}%")

if __name__ == "__main__":
    main()
