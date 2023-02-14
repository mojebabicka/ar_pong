from multiprocessing import Pool
from multiprocessing import Process
from multiprocessing import Value
import time


def countdown(n, process):
    while n > 0:
        n -= 1


def countup(n):
    while n.value > 0:
        n.value += 1


if __name__ == "__main__":
    counter = Value("i", 50_000)
    start = time.time()
    p1 = Process(target=countdown, args=(50_000_000, "1"))
    p2 = Process(target=countdown, args=(25_000_000, "2"))
    p1.start()
    # p2.start()
    p1.join()
    # p2.join()
    end = time.time()
    print("Time taken in seconds -", end - start)
