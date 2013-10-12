#include "kola.hpp"
#include "threadpool.hpp"

static void *task_thread(void *arg) {
	Task *t = (Task*)arg;
	t->Lock();
	t->Run();
	t->SetStatus(Task::StatusFinish);
	t->Unlock();
	t->post();

	return NULL;
}

Task::Task() {
	pthread_mutex_init(&lock, NULL);
	sem_init(&sem, 0, 0);
	status = Task::StatusFree;
}

Task::~Task() {
	Lock();
	if (status == 1) // downloading
		sem_wait(&sem);

	Destroy();
	Unlock();
	sem_destroy(&sem);
}

void Task::Start() {
	KolaClient *client = &KolaClient::Instance();
	SetStatus(Task::StatusDownloading);
	pool_add_worker((thread_pool_t)client->threadPool, task_thread, this);
}

