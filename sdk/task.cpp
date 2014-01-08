#include <time.h>
#include <pthread.h>
#include <errno.h>

#include "kola.hpp"
#include "threadpool.hpp"

CTask::CTask()
{
	_condvar = new ConditionVar();
	status = StatusInit;
}

CTask::~CTask()
{
	delete _condvar;
}

void CTask::Wait()
{
	_condvar->lock();

	if (status != CTask::StatusFinish && status == CTask::StatusDownloading) {
		_condvar->wait();
		_condvar->unlock();
	}
	else
		_condvar->unlock();
}

void CTask::Wakeup()
{
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

void CTask::Start(bool priority)
{
	if (status == CTask::StatusInit) {
		status = StatusDownloading;
		KolaClient &client = KolaClient::Instance();
		client.threadPool->addTask(this, priority);
	}
}

void CTask::Reset()
{
	Wait();
	status = StatusInit;
}
