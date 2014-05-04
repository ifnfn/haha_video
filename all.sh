#! /bin/sh

URL="http://127.0.0.1:9992"

UpdateAlbum() {
    curl "$URL/manage/update?cmd=list&engine=$1Engine" && ./super_client.py
}

UpdateScore() {
    curl "$URL/manage/update?cmd=score&engine=$1Engine" && ./super_client.py
}


Update() {
    #UpdateAlbum Livetv
    UpdateAlbum Qiyi
    #UpdateAlbum QQ
    #UpdateAlbum Sohu
    #UpdateAlbum PPtv
    #UpdateAlbum Letv
}

Score() {
    #UpdateScore Livetv
    UpdateScore Qiyi
    UpdateScore QQ
    UpdateScore Sohu
}

Update
#Score
