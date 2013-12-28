#include <string>
#include <unistd.h>
#include <time.h>
#include <pthread.h>
#include <vector>
#include <list>
#include <map>
#include <deque>
#include <queue>

class Mutex
{
public:
    Mutex() {
        pthread_mutex_init(&_mutex, NULL);
    }
    virtual ~Mutex() {
        pthread_mutex_destroy(&_mutex);
    }
    bool lock() {
        return static_cast<bool>(!pthread_mutex_lock(&_mutex));
    }
    bool unlock() {
        return static_cast<bool>(!pthread_mutex_unlock(&_mutex));
    }
    bool tryLock() {
        return static_cast<bool>(!pthread_mutex_trylock(&_mutex));
    }
protected:
    pthread_mutex_t _mutex;
};


class ConditionVar : public Mutex
{
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
        bool        ret;
        
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

class IThreadSubscriber
{
public:
    virtual ~IThreadSubscriber(){}
    virtual void call() = 0;
};

template <typename T>
class ThreadMemberFunc : public IThreadSubscriber
{
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
class ThreadFunctor : public IThreadSubscriber
{
public:
    ThreadFunctor(T &obj) : _call(obj)
    {}
    
    virtual ~ThreadFunctor(){};
    virtual void call()
    {
        _call();
    }
    
private:
    T &_call;
};

template <typename T, typename Arg>
class ThreadFunctorArg : public IThreadSubscriber
{
public:
    ThreadFunctorArg(T &obj, Arg arg) : _call(obj), _arg(arg)
    {}
    
    virtual ~ThreadFunctorArg(){};
    virtual void call()
    {
        _call(_arg);
    }
    
private:
    T    &_call;
    Arg _arg;
};

class CThread {
public:
    CThread(IThreadSubscriber &func);
    
    template <typename Functor>
    CThread(Functor &functor) : _func(new ThreadFunctor<Functor>(functor)), _state(false)
    {}
    
    template <typename Functor, typename Arg>
    CThread(Functor &functor, Arg arg) : _func(new ThreadFunctorArg<Functor, Arg>(functor, arg)), _state(false)
    {}
    
    template <typename Object>
    CThread(Object *obj, void (Object::*func)()) : _func(new ThreadMemberFunc<Object>(obj, func)), _state(false)
    {}
    
    ~CThread();
    
    bool start();
    bool cancel(void);
    bool join(void **exit_value = 0);
    void run();
    
private:
    IThreadSubscriber *_func;
    bool _state;
    pthread_t _tid;
};

class CTask {
public:
    CTask(){}
    virtual ~CTask(){}
    virtual void Exectue() = 0;
    virtual void operator()() = 0;
private:
    Mutex mutex;
};

class CThreadPool
{
public:
    CThreadPool();
    virtual ~CThreadPool();
    bool init(size_t nbThread);
    void pushTask(CTask &task);
    
private:
    void handleTask();
    
    std::list<CThread*> _threadsList;
    std::deque<CTask*> _tasksList;
    ConditionVar _condvar;
};

class Thread {
	public:
		Thread(ThreadPool *pool);
		~Thread();
		void SetTask(Task *task) {this->task = task;}
		void Execute();
	private:
		pthread_t tid;
		Task *task;
		ThreadPool *pool;
		friend void *thread_routine(void *arg);
};

class ThreadPool {
	public:
		ThreadPool(int size);
		~ThreadPool();
		bool AddTask(Task *task);
		bool RemoveTask(Task *task);
		void ExecuteThread(Thread *thread);
	private:
		pthread_mutex_t queue_lock;
		pthread_cond_t queue_ready;
		std::deque<Task*> taskList;
		std::vector<Thread *> m_threads;
		bool need_destroy;
		int thread_num;
};

