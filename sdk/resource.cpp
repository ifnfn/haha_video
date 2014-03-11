#include <ctype.h>
#include <time.h>

#include "resource.hpp"

extern string MD5STR(const char *data);

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
	md5Name.assign(MD5STR(resName.c_str()), 0, 15);

	md5Name = "/tmp/" + md5Name + extname;
}

void Resource::Cancel()
{
	if (status != Task::StatusFinish) {
		http.Cancel();
		Wait();
	}
}

void Resource::Run(void)
{
	if (http.Get(resName.c_str()) != NULL) {
		miDataSize = http.buffer.size;
		this->ExpiryTime = http.Headers.GetExpiryTime();
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
		res->DecRefCount();
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

ResourceManager::ResourceManager(size_t memory) : MaxMemory(memory), UseMemory(0)
{
	pthread_mutex_init(&lock, NULL);
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

bool ResourceManager::GetFile(FileResource& picture, const string &url)
{
	picture.Clear();
	picture.GetResource(this, url);

	return true;
}

Resource* ResourceManager::AddResource(const string &url)
{
	Resource* pResource = Resource::Create(this);
	pResource->Load(url);
	Lock();
	mResources.insert(mResources.end(), pResource);
	Unlock();
	pResource->Start(false);

	return pResource;
}

Resource* ResourceManager::GetResource(const string &url)
{
	Resource* pResource = dynamic_cast<Resource*>(FindResource(url));
	if (pResource == NULL)
		pResource = AddResource(url);

	if (pResource)
		pResource->IncRefCount();

	return pResource;
}

Resource* ResourceManager::FindResource(const string &url)
{
	Resource* pRet = NULL;
	list<Resource*>::iterator it;

	Lock();
	for (it = mResources.begin(); (it != mResources.end()); it++) {
		pRet = (*it);

		if (pRet->GetName() == url) {
			pRet->UpdateTime();
			break;
		}
	}

	Unlock();

	return pRet;
}

void ResourceManager::MemoryInc(size_t size) {
	UseMemory += size;
}

void ResourceManager::MemoryDec(size_t size) {
	UseMemory -= size;
}

void ResourceManager::RemoveResource(Resource* res)
{
	Lock();
	list<Resource*>::iterator it = mResources.begin();
	for (; it != mResources.end(); it++) {
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
	list<Resource*>::iterator it;
	Lock();
	for (it = mResources.begin(); it != mResources.end();) {
		Resource* pRet = (*it);

		mResources.erase(it++);
		pRet->DecRefCount();
	}
	Unlock();
}

static bool compare_nocase(const Resource* first, const Resource* second)
{
	return first->updateTime < second->updateTime;
}

bool ResourceManager::GC(size_t memsize) // 收回指定大小的内存
{
	Resource* pRet = NULL;
	bool ret = true;

	Lock();

	if (UseMemory + memsize <= MaxMemory) {
		Unlock();
		return ret;
	}

	mResources.sort(compare_nocase);

	list<Resource*>::iterator it;
#if 0
	// 清除所有过期的文件
	time_t now = time(&now);

	for (it = mResources.begin(); it != mResources.end() && UseMemory + memsize > MaxMemory;) {
		pRet = (*it);
		if (pRet->ExpiryTime != 0 && pRet->ExpiryTime < now && pRet->GetStatus() == Task::StatusFinish) {
			mResources.erase(it++);
			pRet->DecRefCount();
		}
		else
			it++;
	}
#endif
	for (it = mResources.begin(); it != mResources.end() && UseMemory + memsize > MaxMemory;) {
		pRet = (*it);

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
