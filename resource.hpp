#ifndef RESOURCE_HPP
#define RESOURCE_HPP

#include <unistd.h>
#include <assert.h>
#include <list>
#include <string>

#include "http.hpp"
#include "kola.hpp"

class ResourceManager;

class IDestructable {
public:
	virtual void Destroy() = 0;
};

class RefCountable {
public:
	RefCountable(): miRefCount(1){}
	virtual ~RefCountable() {assert(miRefCount == 0);}

	virtual int IncRefCount() {  return ++miRefCount; }
	virtual int DecRefCount() {
		miRefCount--;
		int iRet = miRefCount;
		if (miRefCount == 0) {
			OnRefCountZero();
		}

		return iRet;
	}
	virtual int GetRefCount() const {
		return miRefCount;
	}
	virtual void OnRefCountZero() {
		(dynamic_cast<IDestructable*>(this))->Destroy();
	}
protected:
	int miRefCount;
};

class Resource : public virtual RefCountable, public virtual IDestructable, public Task {
public:
	Resource(ResourceManager *manage=NULL);
	virtual ~Resource();
	static Resource* Create(ResourceManager *manage) {
		return dynamic_cast<Resource*>(new Resource(manage));
	}
	virtual void Destroy() {
		delete dynamic_cast<Resource*>(this);
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

	time_t ExpiryTime;
	time_t updateTime;
protected:
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

	bool GetFile(FileResource& picture, const string &url);
	Resource* GetResource(const string &url);
	bool RemoveResource(const string &url);

	void Clear();
	bool GC(size_t mem); // 收回指定大小的内存
	void MemoryInc(size_t size);
	void MemoryDec(size_t size);
	void Lock();
	void Unlock();
	void SetCacheSize(size_t size) {
		MaxMemory = size;
	}
protected:
	Resource* AddResource(const string &url);
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
