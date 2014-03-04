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

using namespace std;

#define foreach(container,i) \
	for(bool __foreach_ctrl__=true;__foreach_ctrl__;)\
		for(typedef typeof(container) __foreach_type__;__foreach_ctrl__;__foreach_ctrl__=false)\
			for(__foreach_type__::iterator i=container.begin();i!=container.end();i++)

#define DEFAULT_PAGE_SIZE 20
#define PAGE_CACHE 5

class IMenu;
class IAlbum;
class IVideo;
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

extern void split(const string& src, const string& separator, vector<string>& dest);

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

class Task {
public:
	enum TaskStatus {
		StatusInit = 0,
		StatusDownloading = 1,
		StatusFinish = 2,
	};
	Task();
	virtual ~Task();
	virtual void Run(void) = 0;
	virtual void operator()();
	int  GetStatus() {return status; }

	void Start(bool priority=true);
	void Wait();
	void Reset();
	void Wakeup();
	enum TaskStatus status;
protected:
	ConditionVar *_condvar;
};

class ScriptCommand {
public:
	ScriptCommand(json_t *js=NULL);
	~ScriptCommand();
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
	string ToString(int offset, int count, string s = "", string e = "", string split = ",");
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
};

class KolaEpg:public vector<EPG> {
public:
	KolaEpg() {}
	bool LoadFromText(string text);
	bool LoadFromJson(json_t *js);
	bool GetCurrent(EPG &e);
	bool GetNext(EPG &e);
	bool Get(EPG &e, time_t time);
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
	bool Empty();
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


class IObject {
public:
	virtual ~IObject() {}
	virtual void Parser(json_t *js) = 0; // 从 json_t 中解析对象
};

// 视频基类
class IVideo: public IObject {
public:
	IVideo() {
		width = height = fps = totalBytes = 0;
		order = 0;
		isHigh = 0;
		videoPlayCount = 0;
		videoScore = 0.0;
		playLength = 0.0;
	}

	int    width;
	int    height;
	int    fps;
	size_t totalBytes;

	int    cid;
	string pid;
	string vid;
	string name;
	int order;
	int isHigh;
	size_t videoPlayCount;
	double videoScore;
	double playLength;

	string showName;
	string publishTime;
	string videoDesc;
	string smallPicUrl;
	string largePicUrl;
	VideoResolution Resolution;

	virtual void GetResolution(StringList& res) = 0;
	virtual void SetResolution(string &res) = 0;
	virtual string GetVideoUrl() = 0;
	virtual string GetSubtitle(const char *lang) = 0;
	virtual bool GetEPG(KolaEpg &epg) = 0;
};

// 节目基类
class IAlbum: public IObject {
public:
	IAlbum() {
		menu = NULL;
		publishYear = 0;
		dailyPlayNum = 0;
		totalPlayNum = 0;
		Score = 0.0;
		order = 0;
		updateTime = 0;
	}

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

	IMenu *menu;

	virtual size_t GetTotalSet() = 0;
	virtual size_t GetVideoCount() = 0;
	virtual size_t GetSource(StringList &sources) = 0;   // 获取节目的节目来源列表
	virtual bool   SetSource(string source) = 0;         // 设置节目来源，为""时，使用默认来源
	virtual bool   GetPictureFile(FileResource& picture, enum PicType type) = 0;
	virtual string &GetPictureUrl(enum PicType type=PIC_AUTO) = 0;
	virtual IVideo *GetVideo(size_t id) = 0;
};

// 菜单基类
class IMenu: public IObject {
public:
	IMenu() {
		cid = -1;
		PictureCacheType = PIC_LARGE;
	}

	size_t     cid;
	string     name;
	enum PicType PictureCacheType;
	StringList quickFilters;
	KolaFilter Filter;
	KolaSort   Sort;

	virtual IAlbum* GetAlbum(size_t position) = 0;

	virtual void   FilterAdd(string key, string value) = 0;
	virtual void   FilterRemove(string key) = 0;
	virtual string GetQuickFilter() = 0;
	virtual bool   SetQuickFilter(string) = 0;
	virtual void   SetSort(string v, string s="1") = 0;

	virtual AlbumPage &GetPage(int pageNo = -1) = 0;
	virtual void   SetPageSize(int size) = 0;
	virtual size_t GetPageSize() = 0;
	virtual int    SeekByAlbumId(string vid) = 0;
	virtual int    SeekByAlbumName(string name) = 0;
	virtual size_t GetAlbumCount() = 0;
	virtual int LowGetPage(AlbumPage *page, size_t pageId, size_t pageSize) = 0;
	virtual int LowGetPage(AlbumPage *page, string key, string value, size_t pageSize) = 0;
};

class KolaVideo: public IVideo {
public:
	virtual void Parser(json_t *js);

	virtual void GetResolution(StringList& res);
	virtual void SetResolution(string &res);
	virtual string GetVideoUrl();
	virtual string GetSubtitle(const char *lang) {return "";}
	virtual bool GetEPG(KolaEpg &epg);
private:
	string directPlayUrl;
	Variant sc_info;
};

class KolaAlbum: public IAlbum {
public:
	KolaAlbum();
	virtual ~KolaAlbum();

	virtual void Parser(json_t *js);

	virtual size_t GetTotalSet();
	virtual size_t GetVideoCount();
	virtual size_t GetSource(StringList &sources); // 获取节目的节目来源列表
	virtual bool SetSource(string source);         // 设置节目来源，为""时，使用默认来源
	virtual bool GetPictureFile(FileResource& picture, enum PicType type);
	virtual string &GetPictureUrl(enum PicType type=PIC_AUTO);
	virtual IVideo *GetVideo(size_t id);
private:
	void VideosClear();
	bool LowVideoGetPage(size_t pageNo, size_t pageSize);

	int cid;
	vector<IVideo*> videoList;

	size_t totalSet;         // 总集数
	size_t updateSet;        // 当前更新集
	string videoPlayUrl;
	string largePicUrl;      // 大图片网址
	string smallPicUrl;      // 小图片网址
	string largeHorPicUrl;
	string smallHorPicUrl;
	string largeVerPicUrl;
	string smallVerPicUrl;

	string defaultPageUrl;   // 当前播放集
	bool   directVideos;
	size_t videoPageSize;
	size_t videoPageId;
	map<string, Variant> SourceList;
	string CurrentSource;   // 设置节目来源

	friend class CustomMenu;
};

class AlbumPage: public Task {
public:
	AlbumPage();
	~AlbumPage(void);
	size_t Count() { return albumList.size();}
	size_t PictureCount() { return pictureCount; }

	void SetMenu(IMenu *m) {
		menu = m;
	}
	size_t CachePicture(enum PicType type); // 将图片加至线程队列，后台下载
	IAlbum* GetAlbum(size_t index);

	void PutAlbum(IAlbum *album);
	virtual void Run(void);

	void Clear();
	int pageId;
	void UpdateCache();
	int score;
private:
	Mutex mutex;
	vector<IAlbum*> albumList;
	size_t pictureCount;
	IMenu *menu;
};

class KolaMenu: public IMenu {
public:
	KolaMenu();
	virtual ~KolaMenu(void) {}

	virtual void Parser(json_t *js);

	void CleanPage();

	virtual IAlbum* GetAlbum(size_t position);
	virtual void   FilterAdd(string key, string value);
	virtual void   FilterRemove(string key);
	virtual string GetQuickFilter() { return quickFilter; }
	virtual bool   SetQuickFilter(string);
	virtual void   SetSort(string v, string s);

	virtual AlbumPage &GetPage(int pageNo = -1);
	virtual void   SetPageSize(int size);
	virtual size_t GetPageSize() { return PageSize;}
	virtual int    SeekByAlbumId(string vid);
	virtual int    SeekByAlbumName(string name);
	virtual size_t GetAlbumCount();
protected:
	KolaClient *client;
	int         PageSize;
	int         PageId;
	size_t      albumCount;
	string      quickFilter;

	int ParserFromUrl(AlbumPage *page, string &jsonstr);

	virtual string GetPostData();
	virtual int LowGetPage(AlbumPage *page, size_t pageId, size_t pageSize);
	virtual int LowGetPage(AlbumPage *page, string key, string value, size_t pageSize);
private:
	void init();
	AlbumPage* updateCache(int pos);
	AlbumPage pageCache[PAGE_CACHE];
	AlbumPage *cur;
	friend class AlbumPage;
};

class CustomMenu: public KolaMenu {
public:
	CustomMenu(string fileName, bool CheckFailure=true);
	void RemoveFailure(); // 移除失效的节目
	void AlbumAdd(IAlbum *album);
	void AlbumAdd(string vid);
	void AlbumRemove(IAlbum *album);
	void AlbumRemove(string vid);
	bool SaveToFile(string otherFile = "");
	virtual size_t GetAlbumCount();
protected:
	virtual int LowGetPage(AlbumPage *page, size_t pageId, size_t pageSize);
	virtual int LowGetPage(AlbumPage *page, string key, string value, size_t pageSize);
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
	list<IAlbum*> albums;
};

class KolaPlayer {
public:
	KolaPlayer();
	~KolaPlayer();
	virtual void Run();
	virtual bool Play(string name, string url) = 0;
	void AddVideo(IVideo *video);
	bool DoPlay(string &name, string &url);
private:
	list<VideoResolution> videoList;
	ConditionVar *_condvar;
	Thread* thread;
};

class KolaInfo {
public:
	StringList VideoSource;
	StringList Resolution;
	bool Empty() {
		return VideoSource.size() == 0 || Resolution.size() == 0;
	}
private:
	friend class KolaClient;
};

class KolaArea {
public:
	string ip;
	string isp;
	string country;
	string province;
	string city;

	bool Empty() {
		return ip.empty() && province.empty() && city.empty();
	}
	string toJson() {
		string ret = "\"area\" : {";
		ret = ret + "\"country\" : \"" + country + "\", ";
		ret = ret + "\"province\" : \"" + province + "\", ";
		ret = ret + "\"city\" : \"" + city + "\"}";

		return ret;
	}
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

class IClient {
protected:
	virtual ~IClient() {}
	virtual IVideo* NewVideo() = 0;
	virtual IAlbum* NewAlbum() = 0;
	virtual IMenu* NewMenu() = 0;
};

class KolaClient: public IClient {
public:
	static KolaClient& Instance(const char *serial = NULL);
	virtual ~KolaClient(void);

	void Quit(void);
	void ClearMenu();
	bool UpdateMenu(void);

	IMenu* GetMenuByName(const char *name);
	IMenu* GetMenuByCid(int cid);
	inline size_t MenuCount() { return menuMap.size(); };
	IMenu* operator[] (const char *name);
	IMenu* operator[] (int inx);
	bool haveCommand() { return havecmd; }
	inline string GetFullUrl(string url);
	bool UrlGet(string url, string &ret);
	bool UrlPost(string url, const char *body, string &ret);
	string& GetServer();
	string GetArea();
	bool GetArea(KolaArea &area);
	time_t GetTime();
	bool GetInfo(KolaInfo &info);
	void SetPicutureCacheSize(size_t size);
	bool InternetReady();
	void CleanResource();
	int debug;
	ResourceManager *resManager;
	ThreadPool *threadPool;
	KolaWeather weather;
	UrlCache cache;
protected:
	virtual IVideo* NewVideo() {
		return new KolaVideo();
	}
	virtual IAlbum* NewAlbum() {
		return new KolaAlbum();
	}
	virtual IMenu* NewMenu() {
		return new KolaMenu();
	}

private:
	KolaClient(void);
	void Login();

	string base_url;
	map<string, IMenu*> menuMap;

	int nextLoginSec;

	bool LoginOne(bool quick=false);
	char *Run(const char *cmd);
	bool ProcessCommand(json_t *cmd, const char *dest);
	bool running;
	Thread* thread;
	Mutex mutex;
	bool havecmd;
	KolaInfo Info;

	friend class KolaMenu;
	friend class KolaVideo;
	friend class KolaAlbum;
	friend class CustomMenu;
	friend class Picture;
	friend class Task;
};

#endif

