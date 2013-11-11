#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <assert.h>
#include <errno.h>
#include <unistd.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <pthread.h>
#include <iostream>

#include "kola.hpp"
#include "threadpool.hpp"

//#define DBG_TPOOL

#if defined(DBG_TPOOL)
#define pr_debug(fmt, ...) \
	printf("[%s][%d]" fmt, __func__, __LINE__, ##__VA_ARGS__)
#else
#define pr_debug(fmt, ...) \
	do {} while(0)
#endif

void *thread_routine(void *arg)
{
	Thread *thread = (Thread*)arg;
	ThreadPool *pool = thread->pool;

	pool->ExecuteThread(thread);
	pthread_exit(NULL);
}

Thread::Thread(ThreadPool *pool)
{
	task = NULL;
	this->pool = pool;
	pthread_create(&tid, NULL, thread_routine, (void*)this);
}

Thread::~Thread()
{
	pthread_join(tid, NULL);
}

void Thread::Execute() {
	if (task)
		task->lowRun();
}

void ThreadPool::ExecuteThread(Thread *thread)
{
	while (true) {
		pthread_mutex_lock(&queue_lock);

		while (taskList.empty() && !need_destroy) {
			pr_debug("thread 0x%lx is waiting\n", pthread_self());
			pthread_cond_wait(&queue_ready, &queue_lock);
		}

		if (need_destroy) {
			pthread_mutex_unlock(&queue_lock);
			pr_debug("thread 0x%lx will exit\n", pthread_self());
			break;
		}
		pr_debug("thread 0x%lx is starting to work\n", pthread_self());

		/*等待队列长度减去1，并取出链表中的头元素*/
		Task *task = taskList.front();
		if (task) {
			taskList.pop_front();
			task->SetStatus(Task::StatusDownloading);
			thread->SetTask(task);
			pr_debug("thread 0x%lx is starting to work, task=%p\n", pthread_self(), task);
			pthread_mutex_unlock(&queue_lock);
			thread->Execute();
		}
	}
}

ThreadPool::ThreadPool(int count)
{
	int i = 0;

	pthread_mutex_init(&queue_lock, NULL);
	pthread_cond_init(&queue_ready, NULL);

	thread_num = count;

	need_destroy = false;

	for (i = 0; i < thread_num; i++) {
		m_threads.push_back(new Thread(this));
	}
}

ThreadPool::~ThreadPool()
{
	need_destroy = true;

	pthread_mutex_lock(&queue_lock);
	/*唤醒所有等待线程，线程池要销毁了*/
	pthread_cond_broadcast(&queue_ready);
	pthread_mutex_unlock(&queue_lock);

	for (int i = 0; i < thread_num; i++) {
		delete m_threads[i];
		pthread_cond_broadcast(&queue_ready);
	}

	/*条件变量和互斥量也别忘了销毁*/
	pthread_mutex_destroy(&queue_lock);
	pthread_cond_destroy(&queue_ready);
}

bool ThreadPool::AddTask(Task *task)
{
	pthread_mutex_lock(&queue_lock);
	taskList.push_back(task);
	pr_debug("cur_queue_size = %d, task=%p\n", taskList.size(), task);

	pthread_cond_signal(&queue_ready);
	pthread_mutex_unlock(&queue_lock);

	return true;
}

bool ThreadPool::RemoveTask(Task *task)
{
	pthread_mutex_lock(&queue_lock);
	task->SetStatus(Task::StatusFree);
	for (std::deque<Task*>::iterator it = taskList.begin(); it != taskList.end(); it++) {
		if (*it == task) {
			taskList.erase(it);
			pr_debug("cur_queue_size = %d\n", taskList.size());
			pthread_mutex_unlock(&queue_lock);
			return true;
		}
	}
	pthread_mutex_unlock(&queue_lock);

	return false;
}
