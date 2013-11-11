#include <time.h>
#include <pthread.h>
#include <errno.h>

#include "kola.hpp"
#include "threadpool.hpp"

void Task::lowRun() {
	lock();
	if (not cancel)
		Run();
	SetStatus(Task::StatusFinish);
	broadcast();
	unlock();
}

Task::Task() {
	cancel = false;
	pthread_mutex_init(&mutex, NULL);
	pthread_cond_init(&ready, NULL);

	status = Task::StatusInit;
}

Task::~Task()
{
	if (status != Task::StatusInit) {
		Wait();
		pthread_mutex_destroy(&mutex);
		pthread_cond_destroy(&ready);
	}
}

void Task::Start() {
	KolaClient *client = &KolaClient::Instance();

	if (status == Task::StatusInit) {
		pthread_mutex_init(&mutex, NULL);
		pthread_cond_init(&ready, NULL);
	}

	SetStatus(Task::StatusWait);
	client->threadPool->AddTask(this);
}

void Task::Cancel() {
	cancel = true;
	KolaClient *client = &KolaClient::Instance();
	client->threadPool->RemoveTask(this);
}

void Task::Wait(int msec)
{
	struct timespec timeout;
	int ret = 0;

	timeout.tv_sec = msec / 1000;
	timeout.tv_nsec = (msec % 1000) * 1000;
	lock();
	while (status == Task::StatusDownloading || status == Task::StatusWait) {
		if (msec == 0)
			ret = wait();
		else
			ret = wait(&timeout);
		if (ret == ETIMEDOUT)
			break;
	}
	unlock();
}
