#! /bin/sh

URL="http://127.0.0.1:9991"

curl "$URL/manage/update?cmd=list"
#./super_client.py

curl "$URL/manage/update?cmd=home"
#./super_client.py

curl "$URL/manage/update?cmd=fullinfo"
#./super_client.py

curl "$URL/manage/update?cmd=score"
#./super_client.py
