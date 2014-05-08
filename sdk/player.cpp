#include <iostream>
#include <unistd.h>
#include <time.h>

#include "kola.hpp"
#include "json.hpp"
#include "base64.hpp"
#include "threadpool.hpp"

KolaPlayer::KolaPlayer()
{
	epg = NULL;
	doNext = false;
	_condvar = new ConditionVar();
	thread = new Thread(this, &KolaPlayer::Run);
	thread->start();
}

KolaPlayer::~KolaPlayer()
{
	thread->cancel();
	_condvar->broadcast();
	NextSem.free();
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

			size_t video_count = album.GetVideoCount();
			printf("[%s] %s: Video Count %ld\n", album.vid.c_str(), album.albumName.c_str(), video_count);

			doNext = false;
			for (size_t i = 0; i < video_count; i++) {
				string player_url;
				KolaVideo *video = album.GetVideo(i);
				if (video) {
					Lock.lock();
					curVideo = *video;
					Lock.unlock();
					Play(curVideo);
					NextSem.wait();
					if (not doNext)
						break;
				}
			}
		}
	}
}

void KolaPlayer::PlayNext(bool doNext)
{
	this->doNext = doNext;
	NextSem.free();
}

void KolaPlayer::AddAlbum(KolaAlbum album)
{
	_condvar->lock();
	albumList.clear();
	albumList.push_back(album);
	_condvar->broadcast();
	_condvar->unlock();
}
