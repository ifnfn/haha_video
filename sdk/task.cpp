#include "kola.hpp"
#include "threadpool.hpp"

static void *task_thread(void *arg) {
	Task *t = (Task*)arg;
	t->Lock();
	t->Run();
	t->SetStatus(Task::StatusFinish);
	t->Unlock();
	t->signal();

	return NULL;
}

Task::Task() {
	pthread_mutex_init(&lock, NULL);
	pthread_cond_init(&ready, NULL);

	status = Task::StatusFree;
}

Task::~Task() {
	Lock();
	pthread_cond_broadcast(&ready);
	if (status != Task::StatusFree) // downloading
		Wait();

	Destroy();
	Unlock();

	pthread_mutex_destroy(&lock);
	pthread_cond_destroy(&ready);
}

void Task::Start() {
	KolaClient *client = &KolaClient::Instance();

	Lock();
	SetStatus(Task::StatusDownloading);
	pool_add_worker((thread_pool_t)client->threadPool, task_thread, this);
	Unlock();
}

