#include <time.h>
#include <pthread.h>
#include <errno.h>

#include "kola.hpp"
#include "threadpool.hpp"

Task::Task()
{
	_condvar = new ConditionVar();
	status = StatusInit;
}

Task::~Task()
{
	delete _condvar;
}

void Task::Wait()
{
	_condvar->lock();

	if (status != Task::StatusFinish && status == Task::StatusDownloading)
		_condvar->wait();

	_condvar->unlock();
}

void Task::Wakeup()
{
	_condvar->lock();
	_condvar->broadcast();
	_condvar->unlock();
}

void Task::operator()()
{
	Run();
	status = Task::StatusFinish;
	Wakeup();
}

void Task::Start(bool priority)
{
	if (status == Task::StatusInit) {
		status = Task::StatusDownloading;
		KolaClient &client = KolaClient::Instance();
		client.threadPool->addTask(this, priority);
	}
}

void Task::Reset()
{
	Wait();
	status = StatusInit;
}
