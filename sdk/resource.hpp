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

class CResourceManager;

class IDestructable {
	public:
		virtual void Destroy() = 0;
};

class CRefCountable {
	public:
		CRefCountable(): miRefCount(1){}
		virtual ~CRefCountable() {assert(miRefCount == 0);}

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

class CResource : public virtual CRefCountable, public virtual IDestructable, public CTask {
	public:
		CResource(CResourceManager *manage=NULL) {
			manager = manage;
			miDataSize = 0;
			score = 0;
		}
		virtual ~CResource();
		static CResource* Create(CResourceManager *manage) {
			return dynamic_cast<CResource*>(new CResource(manage));
		}
		virtual void Destroy() {
			delete dynamic_cast<CResource*>(this);
		}

		void Load(const string &url);
		virtual void Run(void);

		const std::string &GetName() {return resName;}
		const std::string &GetFileName() {return md5Name;}
		size_t GetSize() const { return miDataSize; }

		virtual void Cancel() {
			status = CTask::StatusCancel;
		}

		int score;
	protected:
		size_t miDataSize;
		std::string resName;
		std::string md5Name;
		CResourceManager *manager;
};

class CResourceManager {
	public:
		CResourceManager(size_t memory = 1024 * 1024 * 10);
		virtual ~CResourceManager();

		bool GetFile(CFileResource& picture, const string &url);
		CResource* AddResource(const string &url);
		CResource* GetResource(const string &url);
		CResource* FindResource(const string &url);
		void RemoveResource(CResource* res);

		bool GC(size_t mem); // 收回指定大小的内存
		void MemoryInc(size_t size);
		void MemoryDec(size_t size);
		void Lock();
		void Unlock();
		void SetCacheSize(size_t size) {
			MaxMemory = size;
		}
	protected:
		std::list<CResource*> mResources;
		size_t MaxMemory;
		size_t UseMemory;
		pthread_mutex_t lock;
};

#endif
