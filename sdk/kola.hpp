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
		VideoSegment() {}
		VideoSegment(json_t *js) {
			LoadFromJson(js);
		}
		VideoSegment(std::string u, std::string n, double d, size_t s) {
			url = url;
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
		KolaVideo() {}
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
		bool GetPlayerUrl(int index, std::string &url);
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
			LoadFromJson(js);
		}
		~KolaAlbum() {
//			printf("~KolaAlbum %s\n", albumName.c_str());
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

		bool GetVideo(void);
		bool GetPicture(enum PicType type, void **data, int *size); // 得到图片
		bool GetPlayUrl(void **data, int *size);                    // 得到播放列表
	private:
		bool LoadFromJson(json_t *js);

		std::string pid;
		std::string vid;
		std::string playlistid;

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

class ValueArray: public StringList {
	public:
		ValueArray() {}
		~ValueArray() {}
		virtual void Add(std::string v) {
//			if (values.Find(v))
				StringList::Add(v);
		}
		virtual void Remove(std:: string v) {
			StringList::Remove(v);
		}
	private:
		StringList values;
};

class KolaFilter {
	public:
		KolaFilter() {}
		~KolaFilter() {}
		void KeyAdd(std::string key, std::string value);
		void KeyRemove(std::string key, std::string value);
		std::string GetJsonStr(void);
		ValueArray& operator[] (std::string key);
	private:
		std::map<std::string, ValueArray> filterKey;
};

class KolaSort: public ValueArray {
	public:
		virtual void Add(std::string v) {
			clear();
			ValueArray::Add(v);
		}
		virtual void Remove(std:: string v) {
			clear();
		}
		std::string GetJsonStr(void) {
			std::string ret = ToString();
			if (ret != "")
				ret = "\"filter\": \"" + ret + "\"";

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

		KolaFilter filter;
		KolaSort   sort;
	private:
		KolaClient *client;
		int PageSize;
		int PageId;
};

class KolaClient {
	public:
		static KolaClient& Instance(void) {
			static KolaClient m_kola;

			return m_kola;
		}
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
		int nextLoginSec;

		bool UrlGet(const char *url, std::string &ret, const char *home_url = NULL, int times = 0);
		bool UrlPost(const char *url, const char *body, std::string &ret, const char *home_url = NULL, int times = 0);
		void GetKey(void);
		bool Login(void);
		char *Run(const char *cmd);
		bool ProcessCommand(json_t *cmd);
		bool running;
		pthread_t thread;
		pthread_mutex_t lock;

		friend void *kola_login_thread(void *arg);
		friend KolaMenu;
		friend KolaAlbum;
		friend KolaVideo;
};
