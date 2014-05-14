#include <iostream>
#include <unistd.h>
#include <time.h>

#include "kola.hpp"
#include "json.hpp"
#include "base64.hpp"
#include "threadpool.hpp"

KolaPlayer::KolaPlayer()
{
	videoCount = 0;
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
			size_t count; 
			albumList.clear();
			_condvar->unlock();

			Lock.lock();
			KolaEpg *tmp_epg = epg;
			epg = NULL;
			curVideo = NULL;
			videoCount = 0;
			Lock.unlock();

			if (tmp_epg) {
				delete tmp_epg;
				epg = NULL;
			}

			count = album.GetVideoCount();
			printf("[%s] %s: Video Count %ld\n", album.vid.c_str(), album.albumName.c_str(), count);

			KolaVideo *video = NULL;
			int index = album.GetPlayIndex();

			if (index < count)
				video = album.GetVideo(index);

			if (video) {
				Lock.lock();
				tmpCurrentVideo = *video;
				curVideo = &tmpCurrentVideo;
				videoCount = count;
				Lock.unlock();
			}

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
	KolaEpg *tmp = NULL;

	Lock.lock();
	if (epg == NULL && curVideo) {
		epg = curVideo->NewEPG();
	}
	if (epg) {
		if (sync) {
			epg->Update();
			epg->Wait();
		}
		if (epg->UpdateFinish())
			tmp = epg;
	}
	Lock.unlock();

	return tmp;
}

