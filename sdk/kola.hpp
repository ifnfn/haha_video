#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <jansson.h>
#include <string>

#if ENABLE_SSL
#include <openssl/rsa.h>
#endif

#include "httplib.h"
#include "json.h"
#include "base64.h"


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
	private:

};

class KolaMenu {
	public:
		KolaMenu() {}
		~KolaMenu() {}
		int GetCount();
		void NextPage();
	private:
		int PageSize;
		int PageCount;
};

class KolaClient {
	public:
		KolaClient(void);
		~KolaClient(void) {
#if ENABLE_SSL
			if (rsa)
				RSA_free(rsa);
#endif
			if (host_url)
				delete host;
		}
		bool Login(void);
		KolaMenu *GetMenuByName(const char *name);
		void GetKey(void);
	private:
		std::string publicKey;
		std::string baseUrl;
		int nextLoginSec;
		char *host_url;
#if ENABLE_SSL
		RSA *rsa;
		int Decrypt(int flen, const unsigned char *from, unsigned char *to);
		int Encrypt(int flen, const unsigned char *from, unsigned char *to);
#endif
		char *Run(const char *cmd);
		bool ProcessCommand(json_t *cmd);
		void GetMenu();
};
