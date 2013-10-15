#include "kola.hpp"
#include "threadpool.hpp"

void *task_thread(void *arg) {
	Task *t = (Task*)arg;
	t->lock();
	t->Run();
	t->SetStatus(Task::StatusFinish);
	t->unlock();
	t->signal();

	return NULL;
}

Task::Task() {
	pthread_mutex_init(&mutex, NULL);
	pthread_cond_init(&ready, NULL);

	status = Task::StatusFree;
}

Task::~Task() {
	lock();
	pthread_cond_broadcast(&ready);
	if (status != Task::StatusFree) // downloading
		Wait();

	Destroy();
	unlock();

	pthread_mutex_destroy(&mutex);
	pthread_cond_destroy(&ready);
}

void Task::Start() {
	KolaClient *client = &KolaClient::Instance();

	lock();
	SetStatus(Task::StatusDownloading);
	pool_add_worker((thread_pool_t)client->threadPool, task_thread, this);
	unlock();
}

