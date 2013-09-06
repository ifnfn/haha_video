#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <jansson.h>

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
		KolaClient(void) {}
		~KolaClient(void) {}
		bool Login(void);
		KolaMenu *GetMenuByName(const char *name);
	private:
		char *Run(const char *cmd);
		bool ProcessCommand(json_t *cmd);
		void GetMenu();
};
