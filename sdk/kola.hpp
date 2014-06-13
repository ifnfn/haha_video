#ifndef _KOLATV_HPP__
#define _KOLATV_HPP__

#include <string>
#include <vector>
#include <map>
#include <list>
#include <deque>
#include <unistd.h>

#include <algorithm>
#include <pthread.h>
#include <jansson.h>
#include <semaphore.h>


#define KOLA_VERSION "1"

using namespace std;

#define foreach(container,i) \
	for(bool __foreach_ctrl__=true;__foreach_ctrl__;)\
		for(typedef typeof(container) __foreach_type__;__foreach_ctrl__;__foreach_ctrl__=false)\
			for(__foreach_type__::iterator i=container.begin();i!=container.end();i++)

#define DEFAULT_PAGE_SIZE 20
#define PAGE_CACHE 3

class IClient;
class KolaClient;
class KolaMenu;
class KolaAlbum;
class CustomMenu;
class KolaVideo;
class AlbumPage;
class ThreadPool;
class Task;
class Http;
class ScriptCommand;
class Resource;
class ResourceManager;
class ConditionVar;
class Thread;

enum PicType {
	PIC_LARGE,      // 大图片网址
	PIC_SMALL,      // 小图片网址
	PIC_LARGE_HOR,
	PIC_SMALL_HOR,
	PIC_LARGE_VER,
	PIC_SMALL_VER,
	PIC_AUTO,
	PIC_DISABLE
};

class Mutex {
public:
	Mutex()          {pthread_mutex_init(&_mutex, NULL);}
	virtual ~Mutex() {pthread_mutex_destroy(&_mutex);}
	bool lock()      {return static_cast<bool>(!pthread_mutex_lock(&_mutex));}
	bool unlock()    {return static_cast<bool>(!pthread_mutex_unlock(&_mutex));}
	bool tryLock()   {return static_cast<bool>(!pthread_mutex_trylock(&_mutex));}
protected:
	pthread_mutex_t _mutex;
};

class Semaphore {
public:
        Semaphore(int value) {
		if(value < 0)
			value = 1;
		sem_init(&semaphore, 0, value);
	}
        Semaphore()  { sem_init(&semaphore, 0, 1); }
        ~Semaphore() { sem_destroy(&semaphore); }
        void free()  { sem_post(&semaphore);}
        void wait()  { sem_wait(&semaphore); }
private:
        sem_t semaphore;
};

class IObject {
public:
	IObject();
	virtual ~IObject() {}
	virtual void Parser(json_t *js) = 0; // 从 json_t 中解析对象
protected:
	IClient *client;
};

class Task {
public:
	enum TaskStatus {
		StatusInit = 0,
		StatusDownloading = 1,
		StatusFinish = 2,
	};
	Task(ThreadPool *pool=NULL);
	virtual ~Task();
	virtual void Run(void) = 0;
	virtual void operator()();
	int  GetStatus() {return status; }

	void Start(bool priority=true);
	void Wait();
	void Reset();
	void Wakeup();
	void SetPool(ThreadPool *pool) {this->pool = pool;}
	enum TaskStatus status;
protected:
	ConditionVar *_condvar;
	ThreadPool *pool;
};

class ScriptCommand {
public:
	ScriptCommand(json_t *js=NULL);
	string Run();
	bool Exists() {return not script_name.empty(); }
	void AddParams(const char *arg);
	void AddParams(int arg);
	void DelParams(int count=1);
	virtual bool LoadFromJson(json_t *js);
protected:
	bool directText;
	string text;
	string script_name;
	string func_name;
	vector<string> args;
};

class Variant: public ScriptCommand {
public:
	Variant(json_t *js=NULL);
	string GetString();
	long GetInteger();
	double GetDouble();
	bool Empty();
	virtual bool LoadFromJson(json_t *js);
private:
	string valueStr;
	long valueInt;
	double valueDouble;
	int directValue;
};

class StringList: public vector<string> {
public:
	StringList() {}
	virtual ~StringList() {}
	virtual void Add(string v);
	virtual void Remove(string v);
	void operator<< (string v);
	void operator>> (string v);
	bool Find(string v);
	string ToString(string s = "", string e = "", string split = ",");
	string ToString(size_t offset, size_t count, string s = "", string e = "", string split = ",");
	void Split(const string items, string sp=",");
	bool SaveToFile(string fileName);
	bool LoadFromFile(string fileName);
};

class FileResource {
public:
	FileResource() : res(NULL) {}
	~FileResource();

	Resource *GetResource(ResourceManager *manage, const string &url);
	string& GetName();
	size_t GetSize();
	bool isCached();
	void Wait();
	void Clear();
private:
	Resource *res;
	string FileName;
};

class EPG {
public:
	EPG() {
		startTime = 0;
		duration = 0;
	}
	time_t startTime;
	size_t duration;
	string title;
	string timeString;
	bool empty() {
		return startTime == 0 && title == "" && timeString == "";
	}
};

class KolaEpg: public Task, public IObject {
public:
	KolaEpg();
	KolaEpg(Variant epg);
	virtual ~KolaEpg() {
		Wait();
	}

	void Set(Variant epg) {
		scInfo = epg;
	}

	bool GetCurrent(EPG &e);
	bool GetNext(EPG &e);
	bool Get(EPG &e, time_t time);
	void Clear();
	void Update();
	bool UpdateFinish();
	vector<EPG> epgList;
private:
	virtual void Run(void);

	bool LoadFromText(string text);
	virtual void Parser(json_t *js); // 从 json_t 中解析对象

	Mutex mutex;
	Variant scInfo;
	bool finished;
};

class CacheUrl {
public:
	void operator =(string url) {
		this->url = url;
		t = time(&t);
	}
	string url;
	time_t t;
};

class UrlCache {
public:
	UrlCache();
	void SetTimeout(size_t sec);
	bool FindByVid(string &vid, string &url);
	void Set(string&vid, string &url);
	void Remove(string &vid);
	void Update();
private:
	map<string, CacheUrl> mapList;
	Mutex mutex;
	size_t timeout;
};

class VideoResolution: public Variant {
public:
	void Clear();
	void GetResolution(StringList& res);
	void SetResolution(string &res);
	string GetVideoUrl();
	string defaultKey;
	string vid;
private:
	void Calc();
	map<string, Variant> urls;
	bool GetVariant(string &key, Variant &var);
};

class FilterValue: public StringList {
public:
	FilterValue(const string items);
	FilterValue() {}
	~FilterValue() {}
	void Set(string v) { value = v; }
	string Get(void) { return value; }
protected:
	string value;
};

class KolaFilter {
public:
	KolaFilter() {}
	~KolaFilter() {}
	string GetJsonStr(void);
	FilterValue& operator[] (string key);
	map<string, FilterValue> filterKey;
protected:
	void KeyAdd(string key, string value);
	void KeyRemove(string key);
	friend class KolaMenu;
};

class KolaSort: public FilterValue {
public:
	string GetJsonStr(void) {
		string ret = Get();
		if (not ret.empty()) {
			ret = "\"sort\": \"" + ret + "," + sort +"\"";
		}

		return ret;
	}
protected:
	void Set(string v, string s) { value = v, sort = s;}
private:
	string sort;
	friend class KolaMenu;
};


// 视频基类
class KolaVideo: public IObject {
public:
	KolaVideo();
	~KolaVideo();

	int    width;          // 宽
	int    height;         // 高
	int    fps;            // 帧率
	size_t totalBytes;     // 字节数

	int    cid;
	string pid;
	string vid;
	string name;
	int    order;
	int    isHigh;
	size_t videoPlayCount;
	double videoScore;
	double playLength;

	Variant EpgInfo;

	string showName;
	string publishTime;
	string videoDesc;
	string smallPicUrl;
	string largePicUrl;
	VideoResolution Resolution;

	virtual void Parser(json_t *js);

	void GetResolution(StringList& res);
	void SetResolution(string &res);
	string GetVideoUrl();
	string GetSubtitle(const char *lang) {return "";}

	KolaEpg *NewEPG();
private:
	string directPlayUrl;
};

// 节目基类
class KolaAlbum: public IObject {
public:
	KolaAlbum();
	~KolaAlbum();

	string vid;                  // Album ID
	string albumName;            // 名称
	string albumDesc;            // 节目介绍
	string area;                 // 地区
	string categories;           // 类型
	string isHigh;               // 是否是高清
	int publishYear;             // 发布年份
	StringList mainActors;       // 主演
	StringList directors;        // 导演
	int order;                   // 编号

	time_t updateTime;           // 更新时间
	int dailyPlayNum;            // 日播放次数
	int totalPlayNum;            // 总播放次数
	double Score;                // 得分

	string Number;               // 节目号

	KolaMenu *menu;
	Variant EpgInfo;             // EPG
public:
	virtual void Parser(json_t *js);

	size_t GetTotalSet();
	size_t GetVideoCount();
	size_t GetSource(StringList &sources); // 获取节目的节目来源列表
	bool SetSource(string source);         // 设置节目来源，为""时，使用默认来源
	void SetPlayIndex(int index) { playIndex = index; }
	int  GetPlayIndex()          { return playIndex; }
	bool GetPictureFile(FileResource& picture, enum PicType type);
	KolaVideo *GetVideo(size_t id);
	string &GetPictureUrl(enum PicType type=PIC_AUTO);
	KolaEpg *NewEPG();
private:
	void VideosClear();
	bool LowVideoGetPage(size_t pageNo, size_t pageSize);

	int cid;
	vector<KolaVideo> videoList;

	size_t totalSet;         // 总集数
	size_t updateSet;        // 当前更新集
	string videoPlayUrl;

	string largePicUrl;      // 大图片网址
	string smallPicUrl;      // 小图片网址
	string largeHorPicUrl;
	string smallHorPicUrl;
	string largeVerPicUrl;
	string smallVerPicUrl;

	bool   directVideos;
	size_t videoPageSize;
	size_t videoPageId;
	map<string, Variant> SourceList;
	string CurrentSource;   // 设置节目来源

	int playIndex;
};

class AlbumPage: public Task {
public:
	AlbumPage();
	~AlbumPage(void);
	size_t Count() { return albumList.size();}
	size_t PictureCount() { return pictureCount; }

	void SetMenu(KolaMenu *m) {
		menu = m;
	}
	KolaAlbum* GetAlbum(size_t index);

	void PutAlbum(KolaAlbum album);
	virtual void Run(void);

	void Clear();
	int pageId;
	void UpdateCache();
	int score;
private:
	IClient *client;
	Mutex mutex;
	vector<KolaAlbum> albumList;
	size_t pictureCount;
	KolaMenu *menu;
	size_t CachePicture(enum PicType type); // 将图片加至线程队列，后台下载
};

class KolaMenu: public IObject {
public:
	KolaMenu();
	virtual ~KolaMenu(void);

	size_t     cid;
	string     name;
	PicType    PictureCacheType;
	StringList quickFilters;
	KolaFilter Filter;
	KolaSort   Sort;
	virtual void Parser(json_t *js);

	void CleanPage();

	KolaAlbum* GetAlbum(size_t position);
	void   FilterAdd(string key, string value);
	void   FilterRemove(string key);
	string GetQuickFilter() { return quickFilter; }
	bool   SetQuickFilter(string);
	void   SetSort(string v, string s="1");

	AlbumPage &GetPage(int pageNo = -1);
	void   SetPageSize(int size);
	size_t GetPageSize() { return PageSize;}

	virtual int    SeekByAlbumId(string vid);
	virtual int    SeekByAlbumName(string name);
	virtual int    SeekByAlbumNumber(string number);

	virtual size_t GetAlbumCount();
protected:
	int         PageSize;
	int         PageId;
	size_t      albumCount;
	string      quickFilter;
	string      basePosData;

	int ParserFromUrl(AlbumPage *page, string &jsonstr);

	string GetPostData();
	virtual int LowGetPage(AlbumPage *page, size_t pageId, size_t pageSize);
	virtual int SeekGetPage(AlbumPage *page, string key, string value, size_t pageSize);
private:
	void init();
	AlbumPage* updateCache(int pos);
	AlbumPage  pageCache[PAGE_CACHE];
	AlbumPage *cur;

	friend class AlbumPage;
};

class CustomMenu: public KolaMenu {
public:
	CustomMenu(string fileName, bool CheckFailure=true);
	void RemoveFailure();         // 移除失效的节目
	void AlbumAdd(KolaAlbum *album);
	void AlbumAdd(string vid);
	void AlbumRemove(KolaAlbum *album,bool sync=false);
	void AlbumRemove(string vid, bool sync=false);
	bool SaveToFile(string otherFile = "");
	virtual size_t GetAlbumCount();
protected:
	virtual int LowGetPage(AlbumPage *page, size_t pageId, size_t pageSize);
	virtual int SeekGetPage(AlbumPage *page, string key, string value, size_t pageSize);
private:
	StringList albumIdList;
	string fileName;
};

class PictureIterator {
public:
	PictureIterator(AlbumPage *page, enum PicType type);
	int Get(FileResource &picture);
	size_t size();
private:
	AlbumPage *page;
	enum PicType type;
	list<KolaAlbum*> albums;
};

class KolaPlayer {
public:
	KolaPlayer();
	~KolaPlayer();
	virtual bool Play(KolaVideo *video) = 0;

	void AddAlbum(KolaAlbum album);
	KolaEpg *GetEPG(bool sync=false);
	KolaVideo *GetCurrentVideo();
	KolaEpg Epg;
protected:
	Mutex Lock;
private:
	virtual void Run();

	ConditionVar *_condvar;
	Thread* thread;
	KolaVideo tmpCurrentVideo;
	KolaVideo *curVideo;

	list<KolaAlbum> albumList;
};

class KolaInfo {
public:
	StringList VideoSource;
	StringList Resolution;
	bool Empty() {
		return VideoSource.size() == 0 || Resolution.size() == 0;
	}
};

class KolaArea {
public:
	string ip;
	string isp;
	string country;
	string province;
	string city;

	bool Empty();
	string toJson();

	string toString();
};

class WeatherData {
public:
	string picture;
	string code;
	string weather;
	string temp;
	string windDirection;
	string windPower;
};

class Weather {
public:
	string date;
	StringList city;
	WeatherData day, night;
};

class KolaWeather: public Task {
public:
	virtual ~KolaWeather();
	void GetProvince(StringList &value);
	void GetCity(string province, StringList &area);
	void GetCounty(string province, string area, StringList &county);
	void Update();
	bool UpdateFinish();
	Weather *Today();
	Weather *Tomorrow();
	vector<Weather*> weatherList;
	string PM25;
	virtual void Run(void);
	void SetArea(string province, string area, string county);
	void SetArea(string area);
	string Area;
protected:
	virtual bool ParserWeatherData(WeatherData& data, json_t *js);
	void Get(string name, StringList &value);
private:
	Mutex mutex;
	void Clear();
};

class UpdateSegment {
public:
	string name;
	string md5;
	string href;
};

class KolaUpdate {
public:
	string Version;

	bool CheckVersion(const string ProjectName, const string oldVersion);

	bool GetSegment(const string name, UpdateSegment &segment);
	bool Download(const string name, const string filename);
	virtual bool VersionCompr(const string newVersion, const string oldVersion);
	virtual void Progress(int64_t dltotal, int64_t dlnow) {
		//printf("%lld / %lld (%g %%)\n", dlnow, dltotal, dlnow * 100.0 / dltotal);
	}
private:
	vector<UpdateSegment> Segments;
};

class IClient {
public:
	ResourceManager *resManager;
	ThreadPool *threadPool;
	string DefaultResolution;
	string DefaultVideoSource;

	virtual bool UrlGet(string url, string &ret) = 0;
	virtual bool UrlPost(string url, const char *body, string &ret) = 0;
	virtual bool GetArea(KolaArea &area) = 0;
};

class KolaClient: public IClient {
public:
	static KolaClient& Instance(const char *serial = NULL, size_t cache_size=0, int thread_num=0);
	virtual ~KolaClient(void);
	bool Verify(const char *serial=NULL);

	void Quit(void);
	void ClearMenu();
	bool UpdateMenu(void);

	KolaMenu* Index(int idx);
	KolaMenu* GetMenu(const char *name);
	KolaMenu* GetMenu(int cid);
	inline size_t MenuCount() { return menuMap.size(); };
	string GetFullUrl(string url);
	time_t GetTime();
	bool GetInfo(KolaInfo &info);
	void SetPicutureCacheSize(size_t size);
	bool KolaReady();
	bool InternetReady();
	void CleanResource();
	int debug;
	KolaWeather weather;
	UrlCache cache;

	virtual bool GetArea(KolaArea &area);
	virtual bool UrlGet(string url, string &ret);
	virtual bool UrlPost(string url, const char *body, string &ret);
private:
	KolaClient(void);
	void Login();

	string BaseUrl;
	map<string, KolaMenu*> menuMap;

	bool LoginOne();

	string GetServer(); // 过期的
	void SetServer(string server);

	Thread*  thread;
	Mutex    mutex;
	KolaInfo Info;
	bool     authorized;
	int      nextLoginSec;
};

#endif

