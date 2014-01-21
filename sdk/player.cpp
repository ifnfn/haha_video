#include <iostream>
#include <unistd.h>
#include <time.h>

#include "kola.hpp"
#include "json.hpp"
#include "base64.hpp"
#include "threadpool.hpp"

KolaPlayer::KolaPlayer()
{
	_condvar = new ConditionVar();
	thread = new Thread(this, &KolaPlayer::Run);
	thread->start();
}

KolaPlayer::~KolaPlayer()
{
	thread->cancel();
	_condvar->broadcast();
	thread->join();
	delete _condvar;
}

bool KolaPlayer::DoPlay(string &name, string &url)
{
	return Play(name, url);
}

void KolaPlayer::Run()
{
	while (thread->_state == true) {
		_condvar->lock();
		if (videoList.empty()) {
			_condvar->wait();
			_condvar->unlock();
		}
		else {
			VideoResolution resolution = this->videoList.front();
			videoList.clear();
			_condvar->unlock();

			string url = resolution.GetVideoUrl();
			DoPlay(resolution.defaultKey, url);
		}
	}
}

void KolaPlayer::AddVideo(IVideo *video)
{
	if (video) {
		_condvar->lock();
		videoList.clear();
		videoList.push_back(video->Resolution);
		_condvar->broadcast();
		_condvar->unlock();
	}
}
