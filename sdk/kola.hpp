#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <jansson.h>
#include <string>
#include <list>
#include <vector>
#include <map>
#include <algorithm>
#include <assert.h>

#define ENABLE_SSL 0

#if ENABLE_SSL
#include <openssl/pem.h>
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <openssl/bio.h>
#include <openssl/rsa.h>
#endif

#include "httplib.h"
#include "json.h"
#include "base64.h"

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
	enum PicType {
		PIC_LARGE,      // 大图片网址
		PIC_SMALL,      // 小图片网址
		PIC_LARGE_HOR,
		PIC_SMALL_HOR,
		PIC_LARGE_VER,
		PIC_SMALL_VER,
	};
	public:
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
	int publishYear;     // 发布年份
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
	bool LoadFromJson(json_t *js) {
		albumName      = json_gets(js, "albumName", "");
		albumDesc      = json_gets(js, "albumDesc", "");
		vid            = json_gets(js, "vid", "");
		pid            = json_gets(js, "pid", "");
		isHigh         = json_geti(js, "isHigh", 0);
		publishYear    = json_geti(js, "publishYear", 0);
		totalSet       = json_geti(js, "totalSet", 0);
		area           = json_gets(js, "area", "");

		largePicUrl    = json_gets(js, "largePicUrl", "");
		smallPicUrl    = json_gets(js, "smallPicUrl", "");
		largeHorPicUrl = json_gets(js, "largeHorPicUrl", "");
		smallHorPicUrl = json_gets(js, "smallHorPicUrl", "");
		largeVerPicUrl = json_gets(js, "largeVerPicUrl", "");
		smallVerPicUrl = json_gets(js, "smallVerPicUrl", "");

		//			directors = json_gets(js, "directors", "");
		//			actors = json_gets(js, "actors", "");
		//			mainActors = json_gets(js, "mainActors", "");
		//			categories = json_gets(js, "categories", "");


		//			std::cout << albumName << std::endl;

	}

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
		//		std::vector<KolaAlbum> pageList;
		int PageSize;
		int PageId;
};

class KolaClient {
	public:
		KolaClient(void);
		~KolaClient(void) {
#if ENABLE_SSL
			if (rsa)
				RSA_free(rsa);
#endif
		}
		bool Login(void);
		KolaMenu *GetMenuByName(const char *name);
		KolaMenu *GetMenuByCid(int cid);
		void GetKey(void);

		bool UpdateMenu(void);
		bool GetUrl(const char *url, char **ret, const char *home = NULL);
		bool PostUrl(const char *url, const char *body, char **ret, const char *home = NULL);
	private:
		std::string publicKey;
		std::string baseUrl;
		std::map<std::string, KolaMenu> menuMap;
		int nextLoginSec;

#if ENABLE_SSL
		RSA *rsa;
		int Decrypt(int flen, const unsigned char *from, unsigned char *to);
		int Encrypt(int flen, const unsigned char *in, int in_size, unsigned char *out, int out_size);
#endif
		char *Run(const char *cmd);
		bool ProcessCommand(json_t *cmd);
		void GetMenu();
};
