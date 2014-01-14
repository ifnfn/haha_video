#include <ctype.h>

#include "resource.hpp"

extern string MD5STR(const char *data);

Resource::~Resource()
{
	if (manager && miDataSize > 0)
		manager->MemoryDec(miDataSize);

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

	md5Name = "/tmp/" + MD5STR(resName.c_str()) + extname;
}

void Resource::Run(void)
{
	Http http;
	if (http.Get(resName.c_str()) != NULL) {
		miDataSize = http.buffer.size;
		this->ExpiryTime = http.Headers.GetExpiryTime();
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
	pResource->Start();

	return pResource;
}

Resource* ResourceManager::GetResource(const string &url)
{
	Resource* pResource = dynamic_cast<Resource*>(FindResource(url));
	if (pResource == NULL)
		pResource = AddResource(url);
	else
		printf("Cached in: %s\n", url.c_str());

	pResource->IncRefCount();

	return pResource;
}

Resource* ResourceManager::FindResource(const string &url)
{
	Resource* pRet = NULL;
	list<Resource*>::iterator it;

	Lock();
	for (it = mResources.begin(); (it != mResources.end()) && (pRet == NULL); it++) {
		if ((*it)->GetName() == url) {
			pRet = (*it);
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
			res->DecRefCount();
			mResources.erase(it++);
			break;
		}
	}
	Unlock();
}

static bool compare_nocase(const Resource* first, const Resource* second)
{
	if (first->score == second->score)
		return first->GetSize() > second->GetSize();
	else
		return first->score > second->score;
}

bool ResourceManager::GC(size_t memsize) // 收回指定大小的内存
{
	Resource* pRet = NULL;
	bool ret = true;
	time_t now;

	Lock();

	if (UseMemory + memsize <= MaxMemory) {
		Unlock();
		return ret;
	}

	mResources.sort(compare_nocase);

#if 1
	// 清除所有过期的文件
	now = time(&now);

	list<Resource*>::iterator it;
	for (it = mResources.begin(); it != mResources.end() && UseMemory + memsize > MaxMemory;) {
		pRet = (*it);
		if (pRet->ExpiryTime != 0 && pRet->ExpiryTime < now)
			mResources.erase(it++);
		else
			it++;
	}
#endif
	for (it = mResources.begin(); it != mResources.end() && UseMemory + memsize > MaxMemory;) {
		pRet = (*it);

		if (pRet->GetRefCount() == 1 && pRet->GetStatus() == Task::StatusFinish) {// 无人使用
			pRet->DecRefCount();
			mResources.erase(it++);
		}
		else
			it++;
	}

	ret = UseMemory + memsize <= MaxMemory;
	Unlock();

	return ret;
}
