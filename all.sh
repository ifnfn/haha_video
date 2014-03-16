#! /bin/sh

URL="http://127.0.0.1:9992"

UpdateAlbum() {
    curl "$URL/manage/update?cmd=list&engine=$1Engine" && ./super_client.py
}

UpdateAlbum Livetv
UpdateAlbum Qiyi
UpdateAlbum QQ
UpdateAlbum Sohu
#UpdateAlbum PPtv
#UpdateAlbum Letv

curl "$URL/manage/update?cmd=score" && ./super_client.py

