#include <string>
#include <unistd.h>
#include <vector>
#include <map>
#include <deque>

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

