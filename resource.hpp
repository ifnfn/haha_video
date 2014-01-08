//
//  cref.hpp
//  kolatv
//
//  Created by Silicon on 13-12-27.
//  Copyright (c) 2013年 Silicon. All rights reserved.
//

#ifndef kolatv_cref_hpp
#define kolatv_cref_hpp

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
		Resource(ResourceManager *manage=NULL) {
			manager = manage;
			miDataSize = 0;
			score = 0;
		}
		virtual ~Resource();
		static Resource* Create(ResourceManager *manage) {
			return dynamic_cast<Resource*>(new Resource(manage));
		}
		virtual void Destroy() {
			delete dynamic_cast<Resource*>(this);
		}

		void Load(const string &url);
		virtual void Run(void);

		const std::string &GetName() {return resName;}
		const std::string &GetFileName() {return md5Name;}
		size_t GetSize() const { return miDataSize; }

		int score;
	protected:
		size_t miDataSize;
		std::string resName;
		std::string md5Name;
		ResourceManager *manager;
};

class ResourceManager {
	public:
		ResourceManager(size_t memory = 1024 * 1024 * 10);
		virtual ~ResourceManager();

		bool GetFile(FileResource& picture, const string &url);
		Resource* AddResource(const string &url);
		Resource* GetResource(const string &url);
		Resource* FindResource(const string &url);
		void RemoveResource(Resource* res);

		bool GC(size_t mem); // 收回指定大小的内存
		void MemoryInc(size_t size);
		void MemoryDec(size_t size);
		void Lock();
		void Unlock();
		void SetCacheSize(size_t size) {
			MaxMemory = size;
		}
	protected:
		std::list<Resource*> mResources;
		size_t MaxMemory;
		size_t UseMemory;
		pthread_mutex_t lock;
};

#endif
