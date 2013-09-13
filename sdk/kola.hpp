#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <jansson.h>
#include <string>
#include <list>
#include <vector>
#include <map>

#if ENABLE_SSL
#include <openssl/rsa.h>
#endif

#include "httplib.h"
#include "json.h"
#include "base64.h"

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

class Filter {
	public:
		Filter() {}
		~Filter() {}
	private:
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
		std::map<std::string, KolaMenu*> menuMap;
		int nextLoginSec;

#if ENABLE_SSL
		RSA *rsa;
		int Decrypt(int flen, const unsigned char *from, unsigned char *to);
		int Encrypt(int flen, const unsigned char *from, unsigned char *to);
#endif
		char *Run(const char *cmd);
		bool ProcessCommand(json_t *cmd);
		void GetMenu();
};
