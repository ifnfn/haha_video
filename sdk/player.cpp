#include <iostream>
#include <unistd.h>
#include <time.h>

#include "kola.hpp"
#include "json.hpp"
#include "base64.hpp"
#include "threadpool.hpp"

KolaPlayer::KolaPlayer()
{
	curVideo = NULL;
	epg = NULL;
	_condvar = new ConditionVar();
	thread = new Thread(this, &KolaPlayer::Run);
	thread->start();
}

KolaPlayer::~KolaPlayer()
{
	thread->cancel();
	_condvar->broadcast();
	delete _condvar;
}

void KolaPlayer::Run()
{
	while (thread->_state == true) {
		_condvar->lock();
		if (albumList.empty()) {
			_condvar->wait();
			_condvar->unlock();
		}
		else {
			KolaAlbum album = this->albumList.front();
			albumList.clear();
			_condvar->unlock();

			Lock.lock();
			KolaEpg *tmp_epg = epg;
			epg = NULL;
			curVideo = NULL;
			Lock.unlock();

			if (tmp_epg) {
				delete tmp_epg;
				epg = NULL;
			}

			size_t video_count = album.GetVideoCount();
			printf("[%s] %s: Video Count %ld\n", album.vid.c_str(), album.albumName.c_str(), video_count);

			KolaVideo *video = NULL;
			int index = album.GetPlayIndex();

			if (index < video_count)
				video = album.GetVideo(index);
			Lock.lock();
			curVideo = video;
			Lock.unlock();
			Play(curVideo);
		}
	}
}

void KolaPlayer::AddAlbum(KolaAlbum album)
{
	_condvar->lock();
	albumList.clear();
	albumList.push_back(album);
	_condvar->broadcast();
	_condvar->unlock();
}

KolaEpg *KolaPlayer::GetEPG(bool sync)
{
	Lock.lock();
	if (epg == NULL &&curVideo)
		epg = curVideo->NewEPG(sync);
	Lock.unlock();

	return epg;
}

