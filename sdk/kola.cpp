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

#define OFFSET_SIZE 200
static int regular(const char *pattern, const char *content, char **out, int *len)
{
	pcre *re;
	int rc;
	int erroffset;
	int ovector[OFFSET_SIZE];
	const char *error;

	re = pcre_compile(
			pattern,    /* the pattern                  */
			0,          /* default options              */
			&error,     /* for error message            */
			&erroffset, /* for error offset             */
			NULL);      /* use default character tables */

	if (re == NULL) {
		perror("pcre_compile failed");
		return -1;
	}

	int offset = 0;
	int flags = 0;
	int length = strlen(content);
	int outlen = 0;

	*out = NULL;

	while (offset < length && (rc = pcre_exec(re, 0, content, length, offset, flags, ovector, OFFSET_SIZE)) > 0) {
		const char *substring_start = content + ovector[0];
		int substring_length = ovector[1] - ovector[0];

		*out = (char *)realloc(*out, outlen + substring_length + 1);
		memcpy(*out + outlen, substring_start, substring_length);
		outlen += substring_length + 1;
		(*out)[outlen - 1] = '\n';

		offset = ovector[2 * (rc - 1)];
		//offset = ovector[1];
		flags |= PCRE_NOTBOL;
	}
	if (*len)
		*len =outlen;

	pcre_free(re); // finished matching

	return 0;
}

void test(void) {
	Pcre pcre;
	FILE *fp = fopen("a.txt", "r");
	char *x = ReadStringFile(fp);
	fclose(fp);
	pcre.AddRule("(var) (playlistId|pid|vid|PLAYLIST_ID)\\s*=\\s*\"(.+?)\";");
	string xout = pcre.MatchAll(x);
	std::cout << xout << std::endl;
	free(x);
}

static char *http_get_str(const char *url)
{
	char *ret = NULL;
	http_client_t *http_client;
	http_resp_t *http_resp = NULL;
	http_client = http_init_connection(url);
	if (http_client == NULL) {
		printf("no client: %s\n", url);
		return NULL;
	}
	int rc = http_get(http_client, "", &http_resp);
	if (rc && http_resp && http_resp->body)
		ret = strdup(http_resp->body);

	http_resp_free(http_resp);
	http_free_connection(http_client);

	return ret;
}

KolaClient::KolaClient(void)
{
	char buffer[512];
	char *p = GetIP(SERVER_HOST);

	if (p) {
		sprintf(buffer, "http://%s:%d", p, PORT);
		host_url = strdup(buffer);
		free(p);
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
void KolaClient::GetKey(void)
{
	char url[256];
	sprintf(url, "%s/key", host_url);

	const char *t = http_get_str(url);
	printf("%s=\n", t);
	if (t) {
		publicKey = t;
		std::cout << publicKey << std::endl;
#if ENABLE_SSL
		BIO *key= BIO_new_mem_buf((void*)t, strlen(t));
		rsa = PEM_read_bio_RSA_PUBKEY(key, NULL, NULL, NULL);
		BIO_free_all(key);
#endif
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
	const char *name = json_gets(cmd, "name", "");
	const char *source = json_gets(cmd, "source", "");
	const char *dest = json_gets(cmd, "dest", "");
	char *html;
	string regular_result;
	Pcre pcre;

	html = http_get_str(source);

	if (html == NULL)
		return false;

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

	free(html);

	int in_size = regular_result.size();
	int out_size = BASE64_SIZE(in_size);

	char *out_buffer = (char *)malloc(out_size);
	base64encode((unsigned char *)regular_result.c_str(), in_size, (unsigned char*)out_buffer, out_size);
	json_sets(cmd, "data", out_buffer);
	char *body = json_dumps(cmd, 2);

	http_client_t *http_client;
	http_resp_t *http_resp = NULL;
	http_client = http_init_connection(dest);
	if (http_client == NULL) {
		printf("no client: %s\n", dest);
		goto out;
	}
	ret = http_post(http_client, "", &http_resp, body);
	if (ret && http_resp && http_resp->body) {
		printf("%s\n", http_resp->body);
	}

	http_resp_free(http_resp);
	http_free_connection(http_client);

out:
	free(body);
	free(out_buffer);

	return 0;
}

bool KolaClient::Login(void)
{
	json_error_t error;
	char *data = NULL, *filename = NULL;
	char typebuf[70];
	int len;
	int ret;
	http_client_t *http_client;
	http_resp_t *http_resp = NULL;

	http_client = http_init_connection(host_url);
	if (http_client == NULL) {
		printf("no client: %s\n", host_url);
		return (1);
	}

	ret = http_get(http_client, "/login?user_id=123123", &http_resp);
	if (http_resp) {
		json_t *js = json_loads(http_resp->body, JSON_REJECT_DUPLICATES, &error);
		if (js) {
			const char *v = json_gets(js, "key", "");
			baseUrl = json_gets(js, "server", host_url);
			printf("key= %s\n", v);
			json_t *cmd = json_geto(js, "command");
			if (cmd && json_is_array(cmd)) {
				int i;
				int count = json_array_size(cmd);
				for (i = 0; i < count; i++) {
					json_t *p = json_array_get(cmd, i);
					if (p)
						ProcessCommand(p);
				}
			}

			nextLoginSec = json_geti(js, "next", nextLoginSec);
		}
	}
	http_resp_free(http_resp);
	http_free_connection(http_client);

	return 0;
}

int main(int argc, char **argv)
{
	char *s = GetIP("www.kolatv.com");
//	test();
//	return 0;
	KolaClient kola;

	kola.Login();
	return 0;
}

