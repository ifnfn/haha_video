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

static void *starter(void *arg)
{
	Thread *tmp = static_cast<Thread *>(arg);
	tmp->run();
	return (0);
}

Thread::Thread(IThreadSubscriber &func) :_func(&func), _state(false)
{

}

Thread::~Thread()
{
	if (_state) {
		this->cancel();
	}
	delete _func;
}

void Thread::run()
{
	_func->call();
}

bool Thread::start()
{
	if (this->_state == false) {
		this->_state = true;
		this->_state = static_cast<bool>(!pthread_create(&_tid, 0, &starter, static_cast<void*>(this)));
		pthread_detach(_tid);
	}

	return (this->_state);
}

bool Thread::cancel()
{
	bool ret;

	if (_state == true) {
		ret = static_cast<bool>(!pthread_cancel(_tid));
		if (ret)
			_state = false;
		return ret;
	}
	else
		return (false);
}

ThreadPool::ThreadPool(int num)
{
	if (num > 0)
		init(num);
}

ThreadPool::~ThreadPool()
{
	list<Thread*>::iterator it;

	for (it = _threadsList.begin(); it != _threadsList.end(); it++) {
		Thread* th = *it;
		th->cancel();
		delete th;
	}

	_threadsList.clear();
}

bool ThreadPool::init(size_t nbThread)
{
	for (; nbThread > 0; nbThread--) {
		Thread* thread = new Thread(this, &ThreadPool::handleTask);
		_threadsList.push_back(thread);
		if (!thread->start())
			return false;
	}
	return true;
}

void ThreadPool::addTask(Task *task, bool priority)
{
	if (task) {
		_condvar.lock();

		mutex.lock();
		if (priority)
			_tasksList.push_front(task);
		else
			_tasksList.push_back(task);
		mutex.unlock();

		_condvar.signal();
		_condvar.unlock();
	}
}

bool ThreadPool::removeTask(Task *task)
{
	bool ret = false;
	if (task) {
		mutex.lock();
		for (deque<Task*>::iterator it = _tasksList.begin(); it != _tasksList.end(); it++) {
			if (*it == task) {
				_tasksList.erase(it);
				pr_debug("cur_queue_size = %ld\n", _tasksList.size());
				ret = true;
				break;
			}
		}
		mutex.unlock();
	}

	return ret;
}

void ThreadPool::handleTask()
{
	Task *task;

	while (true) {
		this->_condvar.lock();
		if (this->_tasksList.empty()) {
			this->_condvar.wait();
			this->_condvar.unlock();
		}
		else {
			mutex.lock();
			task = this->_tasksList.front();
			if (task) {
				task->PrepareRun();
				this->_tasksList.pop_front();
			}

			mutex.unlock();
			this->_condvar.unlock();
			if (task)
				(*task)();
		}
	}
}

