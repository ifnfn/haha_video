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
			curVideo = NULL;
			Lock.unlock();

			Epg.Set(album.EpgInfo);

			size_t video_count = album.GetVideoCount();
			printf("[%s] %s: Video Count %lu\n", album.vid.c_str(), album.albumName.c_str(), video_count);

			KolaVideo *video = NULL;
			int index = album.GetPlayIndex();

			if (index < video_count)
				video = album.GetVideo(index);

			if (video) {
				Lock.lock();
				tmpCurrentVideo = *video;
				curVideo = &tmpCurrentVideo;
				if (Epg.scInfo.Empty())
					Epg.Set(curVideo->EpgInfo);

				Lock.unlock();
			}

			Play(curVideo);
		}
	}
}

void KolaPlayer::AddAlbum(KolaAlbum album)
{
	_condvar->lock();
	Epg.Clear();
	albumList.clear();
	albumList.push_back(album);
	_condvar->broadcast();
	_condvar->unlock();
}

KolaEpg *KolaPlayer::GetEPG(bool sync)
{
	KolaEpg *tmp = &Epg;

	Lock.lock();

	Epg.Update();
	if (sync)
		Epg.Wait();
	if (not Epg.UpdateFinish())
		tmp = NULL;

	Lock.unlock();

	return tmp;
}

KolaVideo *KolaPlayer::GetCurrentVideo()
{
	KolaVideo *p;
	Lock.lock();
	p = curVideo;
	Lock.unlock();

	return p;
}

