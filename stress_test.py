import multiprocessing
import random
import time

import requests


# stree test function
def make_request(_: int) -> None:
    res = requests.post(
        "http://localhost:8000/api/orders",
        json={"order_total": random.uniform(1.0, 100.0)},
    )
    print(res.status_code)
    print(res.json())
    time.sleep(random.uniform(0.1, 1))
    return


if __name__ == "__main__":
    with multiprocessing.Pool(processes=8) as pool:
        pool.map(make_request, range(200))
