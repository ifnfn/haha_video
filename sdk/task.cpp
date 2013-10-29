#include "kola.hpp"

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

	status = Task::StatusFree;
}

Task::~Task() {
	Wait();
	Destroy();

	pthread_mutex_destroy(&mutex);
	pthread_cond_destroy(&ready);
}

void Task::Start() {
	KolaClient *client = &KolaClient::Instance();

	SetStatus(Task::StatusWait);
	client->threadPool->AddTask(this);
}

void Task::Cancel() {
	cancel = true;
	KolaClient *client = &KolaClient::Instance();
	client->threadPool->RemoveTask(this);
}

void Task::Wait()
{
	lock();
	while (status == Task::StatusDownloading || status == Task::StatusWait)
		wait();
	unlock();
}
