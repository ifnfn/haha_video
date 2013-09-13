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

#define foreach(container,i) for(bool __foreach_ctrl__=true;__foreach_ctrl__;)\
	for(typedef typeof(container) __foreach_type__;__foreach_ctrl__;__foreach_ctrl__=false)\
	for(__foreach_type__::iterator i=container.begin();i!=container.end();i++)

class KolaClient;

class KolaVideo {
	public:
		KolaVideo() {}
		~KolaVideo() {}
	private:
};

class KolaAlbum {
	public:
		KolaAlbum() {}
		~KolaAlbum() {}
		int GetCount();
	private:
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

class KolaMenu {
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
		std::list<KolaAlbum> pageList;
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
