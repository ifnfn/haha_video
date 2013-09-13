#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <jansson.h>
#include <pcre.h>
#include <iostream>
#include <sys/socket.h>
#include <sys/time.h>
#include <arpa/inet.h>
#include <netdb.h>

#if ENABLE_SSL
#include <openssl/pem.h>
#include <openssl/bio.h>
#endif

#include "httplib.h"
#include "json.h"
#include "base64.h"
#include "kola.hpp"
#include "pcre.hpp"

//#define SERVER_HOST "127.0.0.1"
//#define SERVER_HOST "121.199.20.175"
#define SERVER_HOST "www.kolatv.com"
#define PORT 80


#define foreach(container,i) for(bool __foreach_ctrl__=true;__foreach_ctrl__;)\
	for(typedef typeof(container) __foreach_type__;__foreach_ctrl__;__foreach_ctrl__=false)\
	for(__foreach_type__::iterator i=container.begin();i!=container.end();i++)

static char *GetIP(const char *hostp)
{
	char str[32];
	struct hostent *host = gethostbyname(hostp);

	if (host == NULL)
		return NULL;

	inet_ntop(host->h_addrtype, host->h_addr, str, sizeof(str));

	return strdup(str);
}

static char *ReadStringFile(FILE *fp)
{
#define LEN 2048
	char *s = NULL;

	if (fp) {
		long size = 0;
		int len;
		while (1) {
			s = (char *)realloc(s, size + LEN);
			len = fread(s + size, 1, LEN, fp);
			if (len > 0)
				size += len;
			else
				break;
		}
	}

	return s;
}

KolaMenu::KolaMenu(KolaClient *parent, json_t *js)
{
	PageSize = 10;
	PageId   = -1;
	name = json_gets(js, "name", "");
	cid = json_geti(js, "cid" , -1);
	client = parent;
	printf("cid = %d, name = %s\n", cid, name.c_str());
}

bool KolaMenu::GetPage(int page)
{
	char url[256];

	const char *body = NULL; //"{\"filter\": {}}";
	char *res;

	if (page == -1)
		PageId++;
	else
		PageId = page;

	sprintf(url, "/video/list?page=%d&size=%d&menu=%s", PageId, PageSize, name.c_str());
	if (client->PostUrl(url, body, &res) == true) {
		printf("%s\n", res);
		delete res;
	}
}

KolaClient::KolaClient(void)
{
	char buffer[512];
	char *p = GetIP(SERVER_HOST);

	if (p) {
		sprintf(buffer, "http://%s:%d", p, PORT);
		baseUrl = buffer;
		delete p;
	}

	nextLoginSec = 3;
#if ENABLE_SSL
	rsa = NULL;
#endif
}

#if ENABLE_SSL
int KolaClient::Decrypt(int flen, const unsigned char *from, unsigned char *to)
{
	return RSA_public_decrypt(flen, from, to, rsa, RSA_PKCS1_PADDING);
}

int KolaClient::Encrypt(int flen, const unsigned char *from, unsigned char *to)
{
	return RSA_public_encrypt(flen, from, to, rsa, RSA_PKCS1_PADDING);
}
#endif

bool KolaClient::GetUrl(const char *url, char **ret, const char *home)
{
	bool ok = false;
	http_client_t *http_client;
	http_resp_t *http_resp = NULL;

	if (home == NULL)
		home = baseUrl.c_str();

	http_client = http_init_connection(home);
	if (http_client == NULL) {
		printf("no client: %s\n", url);
		return false;
	}
	int rc = http_get(http_client, url, &http_resp);
	if (rc && ret != NULL && http_resp && http_resp->body) {
		*ret = strdup(http_resp->body);
		ok = true;
	}

	http_resp_free(http_resp);
	http_free_connection(http_client);

	return ok;
}

bool KolaClient::PostUrl(const char *url, const char *body, char **ret, const char *home)
{
	bool ok = false;
	http_client_t *http_client;
	http_resp_t *http_resp = NULL;

	if (home == NULL)
		home = baseUrl.c_str();

	http_client = http_init_connection(home);
	if (http_client == NULL) {
		printf("no client: %s\n", url);
		return false;
	}

	int rc = http_post(http_client, url, &http_resp, body);
	if (rc && ret != NULL && http_resp && http_resp->body) {
		*ret = strdup(http_resp->body);
		ok = true;
	}

	http_resp_free(http_resp);
	http_free_connection(http_client);

	return ok;
}

void KolaClient::GetKey(void)
{
	char *t = NULL;
	if (GetUrl("/key", &t) == true) {
		publicKey = t;
//		std::cout << publicKey << std::endl;
#if ENABLE_SSL
		BIO *key= BIO_new_mem_buf((void*)t, strlen(t));
		rsa = PEM_read_bio_RSA_PUBKEY(key, NULL, NULL, NULL);
		BIO_free_all(key);
#endif
		delete t;
	}
}

char *KolaClient::Run(const char *cmd)
{
	FILE *fp = popen(cmd, "r");
	char *s = ReadStringFile(fp);

	fclose(fp);

	return s;
}

bool KolaClient::ProcessCommand(json_t *cmd)
{
	int ret = -1;
	char *html;
	string regular_result;
	Pcre pcre;
	const char *name = json_gets(cmd, "name", "");
	const char *source = json_gets(cmd, "source", "");
	const char *dest = json_gets(cmd, "dest", "");

	printf("%s --> %s\n", source, dest);

	if (GetUrl("", &html, source) == false)
		return false;

	if (strlen(html) == 0) {
		delete html;
		return false;
	}

	json_t *regular = json_object_get(cmd, "regular");
	if (json_is_array(regular)) {
		int count = json_array_size(regular);
		for (int i = 0; i < count; i++) {
			json_t *p = json_array_get(regular, i);
			const char *r = json_string_value(p);
			pcre.AddRule(r);
		}
		regular_result = pcre.MatchAll(html);
	}
	else
		regular_result = html;

	int in_size = regular_result.size();
	int out_size = BASE64_SIZE(in_size);

	char *out_buffer = (char *)malloc(out_size);
	base64encode((unsigned char *)regular_result.c_str(), in_size, (unsigned char*)out_buffer, out_size);
	json_sets(cmd, "data", out_buffer);
	char *body = json_dumps(cmd, 2);

	PostUrl("", body, NULL, dest);
out:
	delete body;
	delete out_buffer;
	delete html;

	return 0;
}

bool KolaClient::Login(void)
{
	json_error_t error;
	char *body = NULL;

	if (GetUrl("/login?user_id=123123", &body) == false)
		return false;

	json_t *js = json_loads(body, JSON_REJECT_DUPLICATES, &error);
	delete body;

	if (js) {
		const char *v = json_gets(js, "key", "");
		//baseUrl = json_gets(js, "server", baseUrl.c_str());
		json_t *cmd = json_geto(js, "command");
		if (cmd && json_is_array(cmd)) {
			int count = json_array_size(cmd);
			for (int i = 0; i < count; i++) {
				json_t *p = json_array_get(cmd, i);
				if (p)
					ProcessCommand(p);
			}
		}

		nextLoginSec = json_geti(js, "next", nextLoginSec);
	}

	return 0;
}

bool KolaClient::UpdateMenu(void)
{
	json_error_t error;
	json_t *js;
	int count;
	char *html = NULL;

	if ( GetUrl("/video/getmenu", &html) == false)
		return false;

	if (strlen(html) == 0) {
		delete html;
		return false;
	}

	menuMap.clear();
	js = json_loads(html, JSON_REJECT_DUPLICATES, &error);
	delete html;
	count = json_array_size(js);
	for (int i = 0; i < count; i++) {
		json_t *p = json_array_get(js, i);
		if (p) {
			const char *name = json_gets(p, "name", "");

			KolaMenu* menu = new KolaMenu(this, p);
			menuMap.insert(pair<std::string, KolaMenu*>(name, menu));
		}
	}

	return true;
}

KolaMenu *KolaClient::GetMenuByCid(int cid)
{
	foreach(menuMap, i) {
		if (i->second->cid == cid)
			return i->second;
	}

	return NULL;
}

KolaMenu *KolaClient::GetMenuByName(const char *menuName)
{
	json_error_t error;
	json_t *js;
	int count;
	const char *html;
	KolaMenu *ret = NULL;

	if (menuName == NULL)
		return NULL;

	std::map<std::string, KolaMenu*>::iterator it = menuMap.find(menuName);

	if (it != menuMap.end())
		ret = it->second;

	if (ret == NULL) {
		UpdateMenu();
		std::map<std::string, KolaMenu*>::iterator it = menuMap.find(menuName);

		if (it != menuMap.end())
			ret = it->second;
	}

	return ret;
}

int main(int argc, char **argv)
{
	char *s = GetIP("www.kolatv.com");
	KolaClient kola;

	kola.GetKey();
	kola.Login();
	kola.UpdateMenu();
	KolaMenu *m = kola.GetMenuByCid(1);
	if (m)
		std::cout << m->name << std::endl;
	m = kola.GetMenuByName("电影");
	if (m) {
		std::cout << m->name << std::endl;
		m->GetPage();
		m->GetPage();
		m->GetPage();
	}
	return 0;
}


