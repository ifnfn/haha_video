#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <pthread.h>
#include <jansson.h>

#define ENABLE_SSL 0

#define foreach(container,i) \
	for(bool __foreach_ctrl__=true;__foreach_ctrl__;)\
	for(typedef typeof(container) __foreach_type__;__foreach_ctrl__;__foreach_ctrl__=false)\
	for(__foreach_type__::iterator i=container.begin();i!=container.end();i++)

class KolaClient;
class KolaMenu;
class KolaAlbum;

class VideoSegment {
	public:
		VideoSegment() {
			duration = 0;
			size = 0;

		}
		VideoSegment(json_t *js) {
			LoadFromJson(js);
		}
		VideoSegment(std::string u, std::string n, double d, size_t s) {
			url = u;
			newfile = n;
			duration = d;
			size = s;
		}
		~VideoSegment() {

		}
		std::string url;
		std::string newfile;
		double duration;
		size_t size;
		std::string realUrl;
		bool LoadFromJson(json_t *js);

		std::string GetJsonStr(std::string *newUrl);
		void Print(void) {
			printf("%s, %s, %f, %d\n", url.c_str(), newfile.c_str(), duration, size);
		}
};

class KolaVideo: public std::vector<VideoSegment> {
	public:
		KolaVideo() {
			width = height = fps = totalBytes = totalBlocks = 0;
			totalDuration = 0.0;
		}
		~KolaVideo() {}

		int width;
		int height;
		int fps;
		double totalDuration;
		size_t totalBytes;
		int totalBlocks;

		bool LoadFromJson(json_t *js);

		std::string GetM3U8(void);
		std::string GetSubtitle(const char *lang);
		bool GetPlayerUrl(size_t index, std::string &url);
};

class Picture {
	public:
		Picture(std::string fileName);
		Picture();
		virtual ~Picture();
		void *data;
		size_t size;
		std::string fileName;
		bool inCache;
		void Caching(void);
		bool wget();
		virtual void finish(void);
	private:
};

class PictureCache: public std::map<std::string, Picture*> {
	public:
		PictureCache(int size) {
			maxCount = size;
		}
		bool AddPicture(std::string fileName);
	private:
		int maxCount;
};

class KolaAlbum {
	public:
		enum PicType {
			PIC_LARGE,      // 大图片网址
			PIC_SMALL,      // 小图片网址
			PIC_LARGE_HOR,
			PIC_SMALL_HOR,
			PIC_LARGE_VER,
			PIC_SMALL_VER,
		};

		KolaAlbum(json_t *js) {
			largePic    = NULL;
			smallPic    = NULL;
			largeHorPic = NULL;
			smallHorPic = NULL;
			largeVerPic = NULL;
			smallVerPic = NULL;

			LoadFromJson(js);
		}

		~KolaAlbum() {
			//printf("~KolaAlbum %s\n", albumName.c_str());
			if (largePic)
				delete largePic;

			if (smallPic)
				delete smallPic;

			if (largeHorPic)
				delete largeHorPic;

			if (smallHorPic)
				delete smallHorPic;

			if (largeVerPic)
				delete largeVerPic;

			if (smallVerPic)
				delete smallVerPic;
		}

		std::string albumName;
		std::string albumDesc;
		std::string area;            // 地区
		std::string categories;      // 类型
		std::string isHigh;          // 是否是高清
		int publishYear;             // 发布年份
		int totalSet;                // 总集数
		int updateSet;               // 当前更新集
		int dailyPlayNum;            // 每日播放次数
		int weeklyPlayNum;           // 每周播放次数
		int monthlyPlayNum;          // 每月播放次数
		int totalPlayNum;            // 总播放资料
		double dailyIndexScore;      // 每日指数
		std::string mainActors;
		std::string actors;
		std::string directors;
		KolaVideo video;
		std::vector<KolaAlbum> subAlbum; // 子集
		int playlistid;

		bool GetVideo(void);
		void CachePicture(enum PicType type);             // 将图片加至线程队列，后台下载
		bool GetPicture(enum PicType type, Picture &pic); // 得到图片
		bool GetPlayUrl(void **data, int *size);          // 得到播放列表
	private:
		bool LoadFromJson(json_t *js);

		int pid;
		int vid;

		Picture *largePic;
		Picture *smallPic;
		Picture *largeHorPic;
		Picture *smallHorPic;
		Picture *largeVerPic;
		Picture *smallVerPic;

		std::string videoPlayUrl;
		std::string largePicUrl;      // 大图片网址
		std::string smallPicUrl;      // 小图片网址
		std::string largeHorPicUrl;
		std::string smallHorPicUrl;
		std::string largeVerPicUrl;
		std::string smallVerPicUrl;

		std::string videoScore;

		std::string defaultPageUrl;  // 当前播放集
};

class StringList: public std::vector<std::string> {
	public:
		StringList() {}
		virtual ~StringList() {}
		virtual void Add(std::string v) {
			StringList::iterator iter = find(begin(), end(), v);
			if (iter == end())
				push_back(v);
		}
		virtual void Remove(std::string v) {
			StringList::iterator iter = find(begin(), end(), v);
			if (iter != end())
				erase(iter);
		}

		void operator<< (std::string v) {
			Add(v);
		}
		void operator>> (std::string v) {
			Remove(v);
		}

		bool Find(std::string v) {
			StringList::iterator iter = find(begin(), end(), v);
			return iter != end();
		}

		std::string ToString(std::string s = "", std::string e = "", std::string split = ",") {
			std::string ret;
			int count = size();

			if (count > 0) {
				ret = s;
				for (int i = 0; i < count - 1; i++)
					ret += at(i) + split;

				ret += at(count - 1) + e;
			}
			return ret;
		}
};

class FilterValue: public StringList {
	public:
		FilterValue(const std::string items);
		FilterValue() {}
		~FilterValue() {}
		void Set(std::string v) {
			value = v;
		}
		std::string Get(void) {
			return value;
		}
	private:
		std::string value;
};

class KolaFilter {
	public:
		KolaFilter() {}
		~KolaFilter() {}
		void LoadFromJson(json_t *js);
		void KeyAdd(std::string key, std::string value);
		void KeyRemove(std::string key, std::string value);
		std::string GetJsonStr(void);
		FilterValue& operator[] (std::string key);
//	private:
		std::map<std::string, FilterValue> filterKey;
};

class KolaSort: public FilterValue {
	public:
		std::string GetJsonStr(void) {
			std::string ret = Get();
			if (ret != "")
				ret = "\"sort\": \"" + ret + "\"";

			return ret;
		}
};

class KolaMenu :public std::vector<KolaAlbum> {
	public:
		KolaMenu(void);
		KolaMenu(const KolaMenu& m);
		KolaMenu(json_t *js);
		~KolaMenu(void) {}

		std::string name;
		int cid;
		bool GetPage(int page = -1);

		KolaFilter Filter;
		KolaSort   Sort;
	private:
		KolaClient *client;
		int PageSize;
		int PageId;
};

class KolaClient {
	public:
		static KolaClient& Instance(void);
		~KolaClient(void);

		void Quit(void);
		KolaMenu GetMenuByName(const char *name);
		KolaMenu GetMenuByCid(int cid);

		bool UpdateMenu(void);
		KolaMenu operator[] (const char *name);
		KolaMenu operator[] (int inx);
		int MenuCount() {
			return menuMap.size();
		};
	private:
		KolaClient(void);
		std::string baseUrl;
		std::map<std::string, KolaMenu> menuMap;
		std::map<std::string, Picture> picCache;
		int nextLoginSec;
		void *threadPool;

		bool UrlGet(std::string url, const char *home_url, void **http_resp, int times = 0);
		bool UrlGet(std::string url, std::string &ret, const char *home_url = NULL);
		bool UrlGetCache(std::string url, std::string &ret, const char *home_url = NULL);
		bool UrlPost(std::string url, const char *body, std::string &ret, const char *home_url = NULL, int times = 0);
		void GetKey(void);
		bool Login(bool quick=false);
		char *Run(const char *cmd);
		bool ProcessCommand(json_t *cmd, const char *dest);
		bool running;
		pthread_t thread;
		pthread_mutex_t lock;

		friend void *kola_login_thread(void *arg);
		friend class KolaMenu;
		friend class KolaAlbum;
		friend class KolaVideo;
		friend class Picture;
};

void split(const std::string &s, std::string delim, std::vector< std::string > *ret);
