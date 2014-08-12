#! /bin/sh
ab -n 1000 -c 128 'http://127.0.0.1:9991/video/list?full=0&page=1&size=20&cid=200&chipid=00000000&serial=000002&cache=1'
ab -n 1000 -c 128 'http://127.0.0.1:9991/video/list?full=0&page=1&size=20&cid=200&chipid=00000000&serial=000002&cache=0'
ab -n 1000 -c 128 'http://127.0.0.1:9991/video/getmenu?chipid=00000000&serial=000002&cache=1'
ab -n 1000 -c 128 'http://127.0.0.1:9991/video/getmenu?chipid=00000000&serial=000002&cache=0'
ab -n 1000 -c 128 'http://127.0.0.1:9991/video/getvideo?full=0&pid=000028efd764cf&page=0&size=10&chipid=00000000&serial=000002&cache=1'
ab -n 1000 -c 128 'http://127.0.0.1:9991/video/getvideo?full=0&pid=000028efd764cf&page=0&size=10&chipid=00000000&serial=000002&cache=0'