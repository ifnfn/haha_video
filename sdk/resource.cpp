#include <ctype.h>
#include <time.h>

#include "resource.hpp"
#include "common.hpp"
#include "threadpool.hpp"

Resource::Resource(ResourceManager *manage)
{
	manager = manage;
	miDataSize = 0;
	UpdateTime();
	SetPool(manager->threadPool);
}

Resource::~Resource()
{
	if (manager && miDataSize > 0)
		manager->MemoryDec(miDataSize);

	printf("Remove %s -> %s\n", md5Name.c_str(), resName.c_str());
	unlink(md5Name.c_str());
}

static string StringGetFileExt(string path)
{
	if (path.rfind('/') != string::npos)
		path = path.substr(path.rfind("/") + 1);

	string::size_type start = path.rfind('.') == string::npos ? path.length() : path.rfind('.');

	string ret;
	while (start < path.size() && (isalpha(path[start]) || path[start] == '.'))
		ret = ret + path[start++];

	return ret;
}

void Resource::Load(const string &url)
{
	resName = url;
	string extname = StringGetFileExt(url);
	md5Name = "";
	md5Name.assign(MD5(resName.c_str(), resName.size()), 0, 15);

	md5Name = "/tmp/" + md5Name + extname;
}

void Resource::Cancel()
{
	if (status != Task::StatusFinish) {
		http.Cancel();
		//Wait();
	}
}

void Resource::Run(void)
{
	manager->ResIncRef(this);

	if (http.Get(resName.c_str()) != NULL) {
		miDataSize = http.buffer.size;
		time(&this->updateTime);
		if (miDataSize > 0 && manager) {
			manager->GC(miDataSize);
			manager->MemoryInc(miDataSize);

			FILE *fp = fopen(md5Name.c_str(), "wb");
			if (fp){
				fwrite(http.buffer.mem, 1, http.buffer.size, fp);
				fclose(fp);
			}
		}
	}

	manager->ResDecRef(this);
}

string Resource::ToString()
{
	string ret;

	manager->Lock();
	time(&this->updateTime);
	FILE *fp = fopen(md5Name.c_str(), "r");
	if (fp) {
		char buffer[1024];
		while (!feof(fp)) {
			char *p = fgets(buffer, 1023, fp);
			if (p)
				ret.append(p);
		}
		fclose(fp);
	}
	manager->Unlock();

	return ret;
}


FileResource::~FileResource()
{
	Clear();
}

void FileResource::Clear()
{
	if (res) {
		KolaClient &kola = KolaClient::Instance();
		kola.resManager->ResDecRef(res);
		res = NULL;
	}
}

size_t FileResource::GetSize() {
	if (res)
		return res->GetSize();
	else
		return 0;
}

Resource *FileResource::GetResource(ResourceManager *manage, const string &url)
{
	Clear();
	res = manage->GetResource(url);
	if (res)
		FileName = res->GetFileName();

	return res;
}

string& FileResource::GetName()
{
	return FileName;
}

bool FileResource::isCached()
{
	if (res)
		return res->GetStatus() == Task::StatusFinish;

	return false;
}

void FileResource::Wait()
{
	if (res)
		res->Wait();
}

ResourceManager::ResourceManager(int thread_num, size_t memory) : MaxMemory(memory), UseMemory(0)
{
	pthread_mutex_init(&lock, NULL);
	threadPool = new ThreadPool(thread_num);
}

ResourceManager::~ResourceManager()
{
	list<Resource*>::iterator it;
	Lock();
	for (it = mResources.begin(); it != mResources.end(); it++) {
		Resource* pRes = *it;
		pRes->DecRefCount();
	}
	mResources.clear();
	Unlock();
	delete threadPool;
	pthread_mutex_destroy(&lock);
}

void ResourceManager::Lock()
{
	pthread_mutex_lock(&lock);
}

void ResourceManager::Unlock()
{
	pthread_mutex_unlock(&lock);
}

Resource* ResourceManager::GetResource(const string &url)
{
	Resource* pResource = NULL;

	Lock();
	pResource = dynamic_cast<Resource*>(FindResource(url));
	if (pResource == NULL) {
		pResource = Resource::Create(this);
		pResource->Load(url);
		mResources.insert(mResources.end(), pResource);
		pResource->IncRefCount();
		pResource->Start(false);
	}
	Unlock();

	return pResource;
}

bool ResourceManager::RemoveResource(const string &url)
{
	Resource *res = NULL;
	bool ret = false;

	Lock();
	res = FindResource(url);
	Unlock();
	if (res) {
		if (!threadPool->removeTask(res))
			res->Cancel();

		RemoveResource(res);
		res->DecRefCount();

		ret = true;
	}

	return ret;
}

Resource* ResourceManager::FindResource(const string &url)
{
	Resource* pRet = NULL;
	list<Resource*>::iterator it;

	for (it = mResources.begin(); (it != mResources.end()); it++) {
		pRet = (*it);

		if (pRet->GetName() == url) {
			pRet->UpdateTime();

			return  pRet;
		}
	}

	return NULL;
}

void ResourceManager::MemoryInc(size_t size)
{
	UseMemory += size;
}

void ResourceManager::MemoryDec(size_t size)
{
	UseMemory -= size;
}

void ResourceManager::RemoveResource(Resource* res)
{
	Lock();

	for (list<Resource*>::iterator it = mResources.begin(); it != mResources.end(); it++) {
		if (*it == res) {
			mResources.erase(it++);
			res->DecRefCount();
			break;
		}
	}

	Unlock();
}

void ResourceManager::Clear()
{
	Lock();

	for (list<Resource*>::iterator it = mResources.begin(); it != mResources.end();) {
		Resource* pRet = (*it);

		mResources.erase(it++);
		pRet->DecRefCount();
	}

	Unlock();
}

static bool compare_resource(const Resource* first, const Resource* second)
{
	return first->updateTime < second->updateTime;
}

bool ResourceManager::GC(size_t memsize) // 收回指定大小的内存
{
	bool ret = true;

	Lock();

	if (UseMemory + memsize <= MaxMemory) {
		Unlock();

		return ret;
	}

	mResources.sort(compare_resource);

	list<Resource*>::iterator it;
	for (it = mResources.begin(); it != mResources.end() && UseMemory + memsize > MaxMemory;) {
		Resource* pRet = (*it);

		if (pRet->GetRefCount() == 1 && pRet->GetStatus() == Task::StatusFinish) {// 无人使用
			mResources.erase(it++);
			pRet->DecRefCount();
		}
		else
			it++;
	}

	ret = UseMemory + memsize <= MaxMemory;

	Unlock();

	return ret;
}
