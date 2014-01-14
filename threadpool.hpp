#ifndef THREADPOOL_HPP
#define THREADPOOL_HPP

#include <string>
#include <unistd.h>
#include <time.h>
#include <pthread.h>
#include <vector>
#include <list>
#include <map>
#include <deque>
#include <queue>
#include "kola.hpp"

class ConditionVar: public Mutex {
	public:
		ConditionVar(): Mutex() {
			pthread_cond_init(&_cond, 0);
		}
		~ConditionVar() {
			pthread_cond_destroy(&_cond);
		}
		bool signal() {
			return (static_cast<bool>(!pthread_cond_signal(&_cond)));
		}
		bool broadcast() {
			return (static_cast<bool>(!pthread_cond_broadcast(&_cond)));
		}
		bool uniqueWait() {
			bool ret;

			this->lock();
			ret = this->wait();
			return (ret);
		}
		bool wait() {
			return (static_cast<bool>(!pthread_cond_wait(&_cond, &this->_mutex)));
		}
	private:
		pthread_cond_t _cond;
};


class IThreadSubscriber {
	public:
		virtual ~IThreadSubscriber(){}
		virtual void call() = 0;
};

template <typename T>
class ThreadMemberFunc : public IThreadSubscriber {
	public:
		ThreadMemberFunc(T *obj, void (T::*func)()) : _obj(obj), _func(func)
	{}

		virtual ~ThreadMemberFunc(){};
		virtual void call()
		{
			(_obj->*_func)();
		}

	private:
		T     *_obj;
		void (T::*_func)();
};

template <typename T>
class ThreadFunctor : public IThreadSubscriber {
	public:
		ThreadFunctor(T &obj) : _call(obj){}
		virtual ~ThreadFunctor(){};
		virtual void call() {
			_call();
		}

	private:
		T &_call;
};

template <typename T, typename Arg>
class ThreadFunctorArg : public IThreadSubscriber {
	public:
		ThreadFunctorArg(T &obj, Arg arg) : _call(obj), _arg(arg) {}

		virtual ~ThreadFunctorArg(){};
		virtual void call() {
			_call(_arg);
		}

	private:
		T   &_call;
		Arg _arg;
};

class Thread {
	public:
		Thread(IThreadSubscriber &func);

		template <typename Functor>
			Thread(Functor &functor) : _func(new ThreadFunctor<Functor>(functor)), _state(false){}

		template <typename Functor, typename Arg>
			Thread(Functor &functor, Arg arg) : _func(new ThreadFunctorArg<Functor, Arg>(functor, arg)), _state(false){}

		template <typename Object>
			Thread(Object *obj, void (Object::*func)()) : _func(new ThreadMemberFunc<Object>(obj, func)), _state(false){}

		~Thread();

		bool start();
		bool cancel(void);
		bool join(void **exit_value = 0);
		void run();
		bool _state;

	private:
		IThreadSubscriber *_func;
		pthread_t _tid;
};

class ThreadPool {
	public:
		ThreadPool(int num=0);
		virtual ~ThreadPool();
		bool init(size_t nbThread);
		void addTask(Task *task, bool priority=false);
		bool removeTask(Task *task);
	private:
		void handleTask();

		list<Thread*> _threadsList;
		deque<Task*> _tasksList;
		ConditionVar _condvar;
		Mutex mutex;
};

#endif
