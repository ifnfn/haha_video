#include "resource.hpp"

extern string MD5STR(const char *data);

CResource::~CResource()
{
	if (manager && miDataSize > 0)
		manager->MemoryDec(miDataSize);

	unlink(md5Name.c_str());
}

void CResource::Load(const string &url)
{
	resName = url;
	md5Name = "/tmp/" + MD5STR(resName.c_str()) + ".jpg";
}

void CResource::Run(void)
{
	if (status == CTask::StatusCancel)
		return;

	Http http;
	if (http.Get(resName.c_str()) != NULL) {
		miDataSize = http.buffer.size;
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

CFileResource::~CFileResource()
{
	Clear();
}

void CFileResource::Clear()
{
	if (res) {
		res->DecRefCount();
		res = NULL;
	}
}

size_t CFileResource::GetSize() {
	if (res)
		return res->GetSize();
	else
		return 0;
}

CResource *CFileResource::GetResource(CResourceManager *manage, const string &url)
{
	Clear();
	res = manage->GetResource(url);
	res->Wait();

	FileName = res->GetFileName();

	return res;
}

std::string& CFileResource::GetName() {
	return FileName;
}

CResourceManager::CResourceManager(size_t memory) : MaxMemory(memory), UseMemory(0)
{
	pthread_mutex_init(&lock, NULL);
}

CResourceManager::~CResourceManager()
{
	std::list<CResource*>::iterator it;
	Lock();
	for (it = mResources.begin(); it != mResources.end(); it++) {
		CResource* pRes = *it;
		pRes->DecRefCount();
	}
	mResources.clear();
	Unlock();
	pthread_mutex_destroy(&lock);
}

void CResourceManager::Lock()
{
	pthread_mutex_lock(&lock);
}

void CResourceManager::Unlock()
{
	pthread_mutex_unlock(&lock);
}

bool CResourceManager::GetFile(CFileResource& picture, const string &url)
{
	picture.Clear();
	picture.GetResource(this, url);

	return true;
}

CResource* CResourceManager::AddResource(const string &url)
{
	CResource* pResource = CResource::Create(this);
	pResource->Load(url);
	Lock();
	mResources.insert(mResources.end(), pResource);
	Unlock();
	pResource->Start();

	return pResource;
}

CResource* CResourceManager::GetResource(const string &url)
{
	CResource* pResource = dynamic_cast<CResource*>(FindResource(url));
	if (pResource == NULL)
		pResource = AddResource(url);

	pResource->IncRefCount();

	return pResource;
}

CResource* CResourceManager::FindResource(const string &url)
{
	CResource* pRet = NULL;
	std::list<CResource*>::iterator it;
	Lock();
	for (it = mResources.begin(); (it != mResources.end()) && (pRet == NULL); it++) {
		if ((*it)->GetName() == url) {
			pRet = (*it);
		}
	}

	Unlock();

	return pRet;
}

void CResourceManager::MemoryInc(size_t size) {
	UseMemory += size;
}

void CResourceManager::MemoryDec(size_t size) {
	UseMemory -= size;
}

static bool compare_nocase (const CResource* first, const CResource* second)
{
	int x = first->GetRefCount() - second->GetRefCount();
	if (x == 0)
		x = first->score - second->score;
	if (x == 0)
		return second->GetSize() - first->GetSize();

	return x;
}

bool CResourceManager::GC(size_t memsize) // 收回指定大小的内存
{
	CResource* pRet = NULL;
	bool ret = true;

	Lock();

	if (UseMemory + memsize <= MaxMemory) {
		Unlock();
		return ret;
	}

	mResources.sort(compare_nocase);
	std::list<CResource*>::iterator it = mResources.begin();
	for (; it != mResources.end() && UseMemory + memsize > MaxMemory;) {
		pRet = (*it);

		if (pRet->GetRefCount() == 1 && pRet->GetStatus() == CTask::StatusFinish) {// 无人使用
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
