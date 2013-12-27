#ifndef _KOLATV_HPP__
#define _KOLATV_HPP__

#include <string>
#include <vector>
#include <map>
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
class CResource;
class CResourceManager;

extern void split(const string &s, string delim, vector< string > *ret);

enum PicType {
	PIC_LARGE,      // 大图片网址
	PIC_SMALL,      // 小图片网址
	PIC_LARGE_HOR,
	PIC_SMALL_HOR,
	PIC_LARGE_VER,
	PIC_SMALL_VER,
};

class ScriptCommand {
	public:
		ScriptCommand(json_t *js=NULL);
		~ScriptCommand();
		string Run();
		bool Exists() {return not script_name.empty(); }
		void AddParams(const char *arg);
		void AddParams(int arg);
		virtual bool LoadFromJson(json_t *js);
	protected:
		bool directText;
		string text;
		string script_name;
		string func_name;
		char **argv;
		int argc;
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

class Task {
	public:
		enum {
			StatusInit = 0,
			StatusFree = 1,
			StatusWait = 2,
			StatusDownloading = 3,
			StatusFinish = 4,
			StatusCancel = 5
		};
		Task(void);
		virtual ~Task();

		void Start();

		virtual void Cancel();
		virtual void Run(void)     {}

		void SetStatus(int st) { status = st; }
		int  GetStatus() {return status; }
		void Wait(int msec = 0);
	private:
		int status;
		bool cancel;
		pthread_mutex_t mutex;
		pthread_cond_t ready;
		inline void lock()      { pthread_mutex_lock(&mutex);        }
		inline void unlock()    { pthread_mutex_unlock(&mutex);      }
		inline int wait(struct timespec *time = NULL) {
			if (time)
				return pthread_cond_timedwait(&ready, &mutex, time);
			else
				return pthread_cond_wait(&ready, &mutex);
		}

		inline void signal()    { pthread_cond_signal(&ready);       }
		inline void broadcast() { pthread_cond_broadcast(&ready);    }
		void lowRun();
		friend class Thread;
};

class CFileResource {
	public:
		CFileResource() : res(NULL), used(false) {}
		~CFileResource();

		CResource *GetResource(CResourceManager *manage, const string &url);
		std::string& GetName();
		size_t GetSize();
		void Clear();
		bool used;
	private:
		CResource *res;
		std::string FileName;
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

class KolaEpg: public vector<EPG> {
	public:
		KolaEpg() {}
		bool LoadFromText(string text);
		bool LoadFromJson(json_t *js);
		bool GetCurrent(EPG &e);
		bool GetNext(EPG &e);
		bool Get(EPG &e, time_t time);
};

class VideoUrls {
	public:
		VideoUrls(string text);
		~VideoUrls();
		void GetResolution(StringList& res);
		string Get(string &key);
		Variant *GetVariant(string &key);
	private:
		map<string, Variant*> urls;
		string defaultKey;
};

class KolaVideo {
	public:
		KolaVideo(json_t *js = NULL);
		~KolaVideo();

		bool LoadFromJson(json_t *js);

		void Clear();
		void GetResolution(StringList& res);
		string GetVideoUrl(string res="");
		string GetSubtitle(const char *lang);
		string GetInfo();

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
	private:
		string localVideoFile;
		string pageUrl;
		string playUrl;
		string directPlayUrl;

		Variant sc_info;
		Variant sc_resolution;
		VideoUrls *urls;
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

class KolaAlbum {
	public:
		KolaAlbum(json_t *js);
		~KolaAlbum();

		string vid;
		string albumName;
		string albumDesc;
		string area;                 // 地区
		string categories;           // 类型
		string isHigh;               // 是否是高清
		int publishYear;             // 发布年份
		int dailyPlayNum;            // 每日播放次数
		int weeklyPlayNum;           // 每周播放次数
		int monthlyPlayNum;          // 每月播放次数
		int totalPlayNum;            // 总播放资料
		double dailyIndexScore;      // 每日指数
		StringList mainActors;
		StringList directors;

		size_t GetTotalSet();
		size_t GetVideoCount();
		bool GetPictureFile(CFileResource& picture, enum PicType type);
		string &GetPictureUrl(enum PicType type);
		KolaVideo *GetVideo(size_t id);
	private:
		void VideosClear();
		bool LoadFromJson(json_t *js);
		bool LowVideoGetPage(size_t pageNo, size_t pageSize);

		int cid;
		string pid;
		string playlistid;
		vector<KolaVideo*> videos;

		size_t totalSet;         // 总集数
		size_t updateSet;        // 当前更新集
		string videoPlayUrl;
		string largePicUrl;      // 大图片网址
		string smallPicUrl;      // 小图片网址
		string largeHorPicUrl;
		string smallHorPicUrl;
		string largeVerPicUrl;
		string smallVerPicUrl;

		string videoScore;

		string defaultPageUrl;  // 当前播放集
		bool directVideos;
		size_t videoPageSize;
		size_t videoPageId;
		json_t *videoListUrl;

		friend class CustomMenu;
};

class AlbumPage {
	public:
		AlbumPage();
		~AlbumPage(void);
		size_t CachePicture(enum PicType type);             // 将图片加至线程队列，后台下载
		KolaAlbum* GetAlbum(size_t index);

		void PutAlbum(KolaAlbum *album);

		size_t Count() { return albumList.size();}
		size_t PictureCount() { return pictureCount; }

		void Clear();
		int pageId;
	private:
		vector<KolaAlbum*> albumList;
		size_t pictureCount;
};

class KolaMenu {
	public:
		KolaMenu(void);
		KolaMenu(json_t *js);
		virtual ~KolaMenu(void) {}

		size_t     cid;
		string     name;
		string     Language;
		StringList quickFilters;
		KolaFilter Filter;
		KolaSort   Sort;

		void   FilterAdd(string key, string value);
		void   FilterRemove(string key);
		void   SetSort(string v, string s);

		void   SetLanguage(string lang);
		int    GetPage(AlbumPage &page, int pageNo = -1);
		bool   SetQuickFilter(string);
		void   SetPageSize(int size);
		size_t GetPageSize() { return PageSize;}
		int    SeekByAlbumId(string vid);
		int    SeekByAlbumName(string name);
		string GetQuickFilter() { return quickFilter; }
		KolaAlbum* GetAlbum(size_t position);

		virtual size_t GetAlbumCount();
	protected:
		KolaClient *client;
		int         PageSize;
		int         PageId;
		size_t      albumCount;
		string      quickFilter;

		int ParserJson(AlbumPage *page, string &jsonstr);
		string GetPostData();
		void CleanPage();

		virtual int LowGetPage(AlbumPage *page, int pageId, int pageSize);
		virtual int LowGetPage(AlbumPage *page, string key, string value, int pageSize);
	private:
		AlbumPage page[3];
		AlbumPage *prev, *cur, *next;
};

class CustomMenu: public KolaMenu {
	public:
		CustomMenu(string fileName);
		void AlbumAdd(KolaAlbum *album);
		void AlbumAdd(string vid);
		void AlbumRemove(KolaAlbum *album);
		void AlbumRemove(string vid);
		bool SaveToFile(string otherFile = "");
		virtual size_t GetAlbumCount();
	protected:
		virtual int LowGetPage(AlbumPage *page, int pageId, int pageSize);
	private:
		StringList albumIdList;
		string fileName;
};

class KolaInfo {
	public:
		KolaInfo() : update(false) {}
		StringList VideoSource;
		StringList Resolution;
	private:
		bool update;
		friend class KolaClient;
};

class KolaClient {
	public:
		static KolaClient& Instance(const char *user_id = NULL);
		~KolaClient(void);

		void Quit(void);
		void ClearMenu();
		bool UpdateMenu(void);

		KolaMenu* GetMenuByName(const char *name);
		KolaMenu* GetMenuByCid(int cid);
		inline size_t MenuCount() { return menuMap.size(); };
		KolaMenu* operator[] (const char *name);
		KolaMenu* operator[] (int inx);
		bool haveCommand() { return havecmd; }
		inline string GetFullUrl(string url);
		bool UrlGet(string url, string &ret);
		bool UrlPost(string url, const char *body, string &ret);
		string& GetServer() { return baseUrl; }
		string GetArea();
		time_t GetTime();
		KolaInfo& GetInfo();
		int debug;
		CResourceManager *resManager;
	private:
		KolaClient(void);
		string baseUrl;
		map<string, KolaMenu*> menuMap;

		int nextLoginSec;
		ThreadPool *threadPool;

		bool Login(bool quick=false);
		char *Run(const char *cmd);
		bool ProcessCommand(json_t *cmd, const char *dest);
		bool running;
		pthread_t thread;
		pthread_mutex_t lock;
		bool havecmd;
		KolaInfo info;

		friend void *kola_login_thread(void *arg);
		friend class KolaMenu;
		friend class KolaVideo;
		friend class KolaAlbum;
		friend class CustomMenu;
		friend class Picture;
		friend class Task;
};

#endif
