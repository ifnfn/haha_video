#!env python3
# -*- coding: utf-8 -*-

import sys
import time

from engine.kolaclient import KolaClient
from kola.ThreadPool import ThreadPool


def main_one():
    haha = KolaClient(len(sys.argv) > 1)
    haha.Login()

def main():
    haha = KolaClient(len(sys.argv) > 1)
    while True:
        if haha.Login() == False:
            break

def main_loop():
    haha = KolaClient(len(sys.argv) > 1)
    while True:
        while True:
            if haha.Login() == False:
                break
        time.sleep(10)
        print("Loop")

def main_thread():
    thread_pool = ThreadPool(32)
    for _ in range(32):
        thread_pool.add_job(main)

if __name__ == "__main__":
    main_thread()
    #main_one()
    #main()
    #main_loop()
