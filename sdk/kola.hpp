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

class KolaVideo {
	public:
		KolaVideo() {}
		~KolaVideo() {}

	private:
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

		KolaAlbum(KolaMenu *m, json_t *js) {
			menu = m;
			LoadFromJson(js);
		}
		~KolaAlbum() {}

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
		bool GetPicture(enum PicType type, void **data, int *size); // 得到图片
		bool GetPlayUrl(void **data, int *size);                    // 得到播放列表
	private:
		KolaMenu *menu;
		bool LoadFromJson(json_t *js);

		std::string pid;
		std::string vid;
		std::string playlistid;

		std::string largePicUrl;      // 大图片网址
		std::string smallPicUrl;      // 小图片网址
		std::string largeHorPicUrl;
		std::string smallHorPicUrl;
		std::string largeVerPicUrl;
		std::string smallVerPicUrl;

		std::string videoScore;

		std::string defaultPageUrl;  // 当前播放集

		std::vector<KolaVideo> videos;
};

class ValueArray: public std::vector<std::string> {
	public:
		ValueArray() {}
		~ValueArray() {}
		void Add(std::string v) {
			std::vector<std::string>::iterator iter = find(begin(), end(), v);
			if (iter == end())
				push_back(v);
		}
		void Remove(std:: string v) {
			std::vector<std::string>::iterator iter = find(begin(), end(), v);
			if (iter != end())
				erase(iter);
		}
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

class KolaMenu :public std::vector<KolaAlbum> {
	public:
		KolaMenu(KolaClient *parent, std::string name) {}
		KolaMenu(KolaClient *parent, json_t *js);
		~KolaMenu() {}

		std::string name;
		int cid;
		bool GetPage(int page = -1);
	private:
		KolaClient *client;
		KolaFilter filter;
		int PageSize;
		int PageId;
};

class KolaClient {
	public:
		KolaClient(void);
		~KolaClient(void);

		void Quit(void);
		KolaMenu *GetMenuByName(const char *name);
		KolaMenu *GetMenuByCid(int cid);

		bool UpdateMenu(void);
		bool UrlGet(const char *url, char **ret, const char *home = NULL);
		bool UrlPost(const char *url, const char *body, char **ret, const char *home = NULL);
	private:
		std::string baseUrl;
		std::map<std::string, KolaMenu> menuMap;
		int nextLoginSec;

		void GetKey(void);
		bool Login(void);
		char *Run(const char *cmd);
		bool ProcessCommand(json_t *cmd);
		bool running;
		pthread_t thread;
		pthread_mutex_t lock;
		friend void *kola_login_thread(void *arg);
};
