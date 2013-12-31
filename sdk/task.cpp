#include <time.h>
#include <pthread.h>
#include <errno.h>

#include "kola.hpp"
#include "threadpool.hpp"

CTask::CTask()
{
	_condvar = new ConditionVar();
}

CTask::~CTask()
{
	delete _condvar;
}

void CTask::Wait() {
	_condvar->lock();
	if (status != StatusFinish) {
		_condvar->wait();
		_condvar->unlock();
	}
	else {
		_condvar->unlock();
	}
}

void CTask::Wakeup() {
	_condvar->lock();
	_condvar->broadcast();
	_condvar->unlock();
}

void CTask::operator()()
{
	Run();
	status = CTask::StatusFinish;
	Wakeup();
}

void CTask::Start()
{
	status = StatusDownloading;
	KolaClient &client = KolaClient::Instance();
	client.threadPool->addTask(this);
}

