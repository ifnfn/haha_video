#ifndef RESOURCE_HPP
#define RESOURCE_HPP

#include <unistd.h>
#include <assert.h>
#include <list>
#include <string>

#include "http.hpp"
#include "kola.hpp"

class ResourceManager;

class RefCountable {
public:
	virtual int IncRefCount() {  return ++miRefCount; }
	virtual int DecRefCount() {
		miRefCount--;
		int iRet = miRefCount;

		return iRet;
	}
	virtual int GetRefCount() const {
		return miRefCount;
	}
protected:
	RefCountable(): miRefCount(1) { }
	virtual ~RefCountable() {assert(miRefCount == 0);}

	int miRefCount;
};

class Resource: public virtual RefCountable, public Task {
public:
	virtual ~Resource();
	static Resource* Create(ResourceManager *manage) {
		return dynamic_cast<Resource*>(new Resource(manage));
	}
	void Load(const string &url);
	virtual void Run(void);

	void Cancel();

	const string &GetName() {return resName;}
	const string &GetFileName() {return md5Name;}
	size_t GetSize() const { return miDataSize; }
	string ToString();
	void UpdateTime() {
		time(&updateTime);
	}

	time_t updateTime;
	bool overdue;
protected:
	Resource(ResourceManager *manage=NULL);
	size_t miDataSize;
	string resName;
	string md5Name;
	ResourceManager *manager;
private:
	Http http;
};

class ResourceManager {
public:
	ResourceManager(int thread_num = 1, size_t memory = 1024 * 1024 * 2);
	virtual ~ResourceManager();

	Resource* GetResource(const string &url);
	bool RemoveResource(const string &url);

	void Clear();
	bool GC(size_t mem);                // 收回指定大小的内存
	void MemoryInc(size_t size);
	void MemoryDec(size_t size);
	void Lock();
	void Unlock();
	void SetCacheSize(size_t size) {
		MaxMemory = size;
	}
protected:
	void ResIncRef(Resource *res) {
		Lock();
		res->IncRefCount();
		Unlock();
	}

	void ResDecRef(Resource *res) {
		Lock();
		res->DecRefCount();
		Unlock();
	}
	void RemoveResource(Resource* res);
	Resource* FindResource(const string &url);
	list<Resource*> mResources;
	size_t MaxMemory;
	size_t UseMemory;
	pthread_mutex_t lock;
	ThreadPool *threadPool;
	friend class Resource;
};

#endif
