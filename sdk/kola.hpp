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
class ScriptCommand;

extern void split(const std::string &s, std::string delim, std::vector< std::string > *ret);

enum PicType {
	PIC_LARGE,      // 大图片网址
	PIC_SMALL,      // 小图片网址
	PIC_LARGE_HOR,
	PIC_SMALL_HOR,
	PIC_LARGE_VER,
	PIC_SMALL_VER,
};

class StringList: public std::vector<std::string> {
	public:
		StringList() {}
		virtual ~StringList() {}
		virtual void Add(std::string v);
		virtual void Remove(std::string v);
		void operator<< (std::string v);
		void operator>> (std::string v);
		bool Find(std::string v);
		std::string ToString(std::string s = "", std::string e = "", std::string split = ",");
		std::string ToString(int offset, int count, std::string s = "", std::string e = "", std::string split = ",");
		void Split(const std::string items, std::string sp=",");
		bool SaveToFile(std::string fileName);
		bool LoadFromFile(std::string fileName);
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

		virtual void Run(void)     {}

		void Start();

		void Cancel();
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

class EPG {
	public:
		EPG() {
			startTime = 0;
			duration = 0;
		}
		time_t startTime;
		size_t duration;
		std::string title;
		std::string timeString;
};

class KolaEpg: public std::vector<EPG> {
	public:
		KolaEpg() {}
		bool LoadFromText(std::string text);
		bool LoadFromJson(json_t *js);
		bool GetCurrent(EPG &e);
		bool GetNext(EPG &e);
		bool Get(EPG &e, time_t time);
};

class KolaVideo {
	public:
		KolaVideo(json_t *js = NULL);
		~KolaVideo();

		bool LoadFromJson(json_t *js);

		void Clear();
		std::string GetVideoUrl(std::string res="");
		std::string GetSubtitle(const char *lang);
		std::string GetInfo();

		int    width;
		int    height;
		int    fps;
		double totalDuration;
		size_t totalBytes;
		int    totalBlocks;

		int         cid;
		std::string pid;
		std::string vid;
		std::string name;
		int order;
		int isHigh;
		int videoPlayCount;
		double videoScore;
		double playLength;

		std::string showName;
		std::string publishTime;
		std::string videoDesc;
		std::string smallPicUrl;
		std::string largePicUrl;
		StringList  resolution;
	private:
		std::string localVideoFile;
		std::string playlistid;
		std::string pageUrl;
		std::string playUrl;
		std::string directPlayUrl;
		ScriptCommand *info_js;
};

class Picture: public Task {
	public:
		Picture(std::string fileName);
		Picture();
		virtual ~Picture();

		void *data;
		size_t size;
		std::string fileName;
		bool inCache;
		virtual void Run();
		bool used;
};

class FilterValue: public StringList {
	public:
		FilterValue(const std::string items);
		FilterValue() {}
		~FilterValue() {}
		void Set(std::string v) { value = v; }
		std::string Get(void) { return value; }
	protected:
		std::string value;
};

class KolaFilter {
	public:
		KolaFilter() {}
		~KolaFilter() {}
		void KeyAdd(std::string key, std::string value);
		void KeyRemove(std::string key);
		std::string GetJsonStr(void);
		FilterValue& operator[] (std::string key);
		std::map<std::string, FilterValue> filterKey;
};

class KolaSort: public FilterValue {
	public:
		std::string GetJsonStr(void) {
			std::string ret = Get();
			if (ret != "") {
				ret = "\"sort\": \"" + ret + "," + sort +"\"";
			}

			return ret;
		}
		void Set(std::string v, std::string s) { value = v, sort = s;}
	private:
		std::string sort;
};

class KolaAlbum {
	public:
		KolaAlbum(json_t *js);
		~KolaAlbum();

		std::string vid;
		std::string albumName;
		std::string albumDesc;
		std::string area;            // 地区
		std::string categories;      // 类型
		std::string isHigh;          // 是否是高清
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
		std::string &GetPictureUrl(enum PicType type);
		KolaVideo *GetVideo(int id);
	private:
		void VideosClear();
		bool LoadFromJson(json_t *js);
		bool LowVideoGetPage(size_t pageNo, size_t pageSize);

		int cid;
		std::string pid;
		std::string playlistid;
		std::vector<KolaVideo*> videos;

		int totalSet;                // 总集数
		int updateSet;               // 当前更新集
		std::string videoPlayUrl;
		std::string largePicUrl;      // 大图片网址
		std::string smallPicUrl;      // 小图片网址
		std::string largeHorPicUrl;
		std::string smallHorPicUrl;
		std::string largeVerPicUrl;
		std::string smallVerPicUrl;

		std::string videoScore;

		std::string defaultPageUrl;  // 当前播放集
		bool directVideos;
		size_t videoPageSize;
		size_t videoPageId;

		friend class CustomMenu;
};

class AlbumPage {
	public:
		AlbumPage();
		~AlbumPage(void);
		void CachePicture(enum PicType type);             // 将图片加至线程队列，后台下载
		KolaAlbum* GetAlbum(int index);

		void PutAlbum(KolaAlbum *album);
		void PutPicture(std::string picFileName);

		size_t Count() { return albumList.size();}
		size_t PictureCount() { return pictureList.size(); }

		Picture* GetPicture(std::string fileName);
		void Clear();
		int pageId;
	private:
		std::vector<KolaAlbum*> albumList;
		std::map<std::string, Picture*> pictureList;
};

class KolaMenu {
	public:
		KolaMenu(void);
		KolaMenu(json_t *js);
		virtual ~KolaMenu(void) {}

		int         cid;
		std::string name;
		StringList  quickFilters;
		KolaFilter  Filter;
		KolaSort    Sort;
		std::string Language;

		void   SetLanguage(std::string lang);
		int    GetPage(AlbumPage &page, int pageNo = -1);
		bool   SetQuickFilter(std:: string);
		void   SetPageSize(int size) {PageSize = size;}
		size_t GetPageSize() { return PageSize;}
		int    SeekByAlbumId(std::string vid);
		int    SeekByAlbumName(std::string name);
		std::string GetQuickFilter() { return quickFilter; }
		virtual int GetAlbumCount();
		KolaAlbum* GetAlbum(int position);
	protected:
		KolaClient *client;
		int PageSize;
		int PageId;
		int albumCount;
		std::string quickFilter;
		virtual int LowGetPage(AlbumPage *page, int pageId, int pageSize);
		virtual int LowGetPage(AlbumPage *page, std::string key, std::string value, int pageSize);
		int ParserJson(AlbumPage *page, std::string &jsonstr);
		std::string GetPostData();
		void CleanPage();
	private:
		AlbumPage page[3];
		AlbumPage *prev, *cur, *next;
};

class CustomMenu: public KolaMenu {
	public:
		CustomMenu(std::string fileName);
		void AlbumAdd(KolaAlbum *album);
		void AlbumAdd(std::string vid);
		void AlbumRemove(KolaAlbum *album);
		void AlbumRemove(std::string vid);
		bool SaveToFile(std::string otherFile = "");
		virtual int GetAlbumCount();
	protected:
		virtual int LowGetPage(AlbumPage *page, int pageId, int pageSize);
	private:
		StringList albumIdList;
		std::string fileName;
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
		int MenuCount() { return menuMap.size(); };
		KolaMenu* operator[] (const char *name);
		KolaMenu* operator[] (int inx);
		bool haveCommand() { return havecmd; }
		inline std::string GetFullUrl(std::string url) { return baseUrl + url; }
		bool UrlGet(void **http_resp, std::string url, const char *home_url, const char *referer = NULL, int times = 0);
		bool UrlGet(std::string url, std::string &ret, const char *home_url = NULL, const char *referer = NULL);
		bool UrlGetCache(std::string url, std::string &ret, const char *home_url = NULL, const char *referer = NULL);
		bool UrlPost(std::string url, const char *body, std::string &ret, const char *home_url = NULL, const char *referer = NULL, int times = 0);
		std::string& GetServer() { return baseUrl; }
		std::string GetArea();
		time_t GetTime();
		int debug;
	private:
		KolaClient(void);
		std::string baseUrl;
		std::map<std::string, KolaMenu*> menuMap;

		int nextLoginSec;
		ThreadPool *threadPool;

		bool Login(bool quick=false);
		char *Run(const char *cmd);
		bool ProcessCommand(json_t *cmd, const char *dest);
		bool running;
		pthread_t thread;
		pthread_mutex_t lock;
		bool havecmd;

		friend void *kola_login_thread(void *arg);
		friend class KolaMenu;
		friend class KolaVideo;
		friend class KolaAlbum;
		friend class CustomMenu;
		friend class Picture;
		friend class Task;
};

#endif

