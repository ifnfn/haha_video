#! /bin/sh

URL="http://127.0.0.1:9992"

UpdateAlbum() {
    curl "$URL/manage/update?cmd=list&engine=$1Engine" && python3 ./super_client.py
}

UpdateScore() {
    curl "$URL/manage/update?cmd=score&engine=$1Engine" && python3 ./super_client.py
}


Update() {
    UpdateAlbum Qiyi
    UpdateAlbum QQ
    UpdateAlbum Sohu
    UpdateAlbum PPtv
    UpdateAlbum Letv
}

Score() {
    UpdateScore Qiyi
    UpdateScore QQ
    UpdateScore Sohu
}

UpdateTV() {
    mongo kola --eval 'db.album.remove({"cid":200}); db.videos.remove({"cid":200})'
    UpdateAlbum Livetv
}

UpdateTV
#Update
#Score
