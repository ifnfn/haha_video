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
	CThread *tmp = static_cast<CThread *>(arg);
	tmp->run();
	return (0);
}

CThread::CThread(IThreadSubscriber &func) :_func(&func), _state(false)
{

}

CThread::~CThread()
{
	if (_state)
		this->cancel();
	delete _func;
}

void CThread::run()
{
	_func->call();
}

bool CThread::start()
{
	if (this->_state == false)
	{
		this->_state = static_cast<bool>(!pthread_create(&_tid, 0, &starter, static_cast<void*>(this)));
	}
	return (this->_state);
}

bool CThread::cancel()
{
	bool ret;

	if (_state == true)
	{
		ret = static_cast<bool>(!pthread_cancel(_tid));
		if (ret)
			_state = false;
		return (ret);
	}
	else
		return (false);
}

bool CThread::join(void **exit_value)
{
	bool ret;

	if (_state != false)
	{
		ret = static_cast<bool>(!pthread_join(_tid, exit_value));
		_state = false;
		return (ret);
	}
	else
		return false;
}

CThreadPool::CThreadPool(int num)
{
	if (num > 0)
		init(num);
}

CThreadPool::~CThreadPool()
{

}

bool CThreadPool::init(size_t nbThread)
{
	CThread *thread;

	for (; nbThread > 0; nbThread--)
	{
		thread = new CThread(this, &CThreadPool::handleTask);
		_threadsList.push_back(thread);
		if (!thread->start())
			return false;
	}
	return true;
}

void CThreadPool::addTask(CTask *task, bool priority)
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

bool CThreadPool::removeTask(CTask *task)
{
	bool ret = false;
	if (task) {
		mutex.lock();
		for (deque<CTask*>::iterator it = _tasksList.begin(); it != _tasksList.end(); it++) {
			if (*it == task) {
				_tasksList.erase(it);
				pr_debug("cur_queue_size = %d\n", taskList.size());
				ret = true;
				break;
			}
		}
		mutex.unlock();
	}

	return ret;
}

void CThreadPool::handleTask()
{
	CTask *task;

	while (true) {
		this->_condvar.lock();
		if (this->_tasksList.empty()) {
			this->_condvar.wait();
			this->_condvar.unlock();
		}
		else {
			mutex.lock();
			task = this->_tasksList.front();
			this->_tasksList.pop_front();
			mutex.unlock();
			this->_condvar.unlock();
			(*task)();
		}
	}
}

