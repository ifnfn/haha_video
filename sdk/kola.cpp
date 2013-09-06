#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <jansson.h>
#include <pcre.h>

#include "httplib.h"
#include "json.h"
#include "base64.h"
#include "kola.hpp"

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


//	FILE *fp = fopen("a.txt", "r");
//	char *x = ReadStringFile(fp);
//	char *line = x;

#define OFFSET_SIZE 200
int regular (const char *pattern, const char *content) {
	pcre *re;
	int rc;
	int erroffset;
	int ovector[OFFSET_SIZE];
	const char *error;

	pattern = "(var) (playlistId|pid|vid|tag|PLAYLIST_ID)\\s*=\\s*\"(.+?)\";";
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

	while (offset < length && (rc = pcre_exec(re, 0, content, length, offset, flags, ovector, OFFSET_SIZE)) > 0) {
		int i;
		for (i = 0; i < rc; i++) {
			const char *substring_start = content + ovector[2*i];
			int substring_length = ovector[2*i+1] - ovector[2*i];
			printf("$%2d: %.*s\n", i, substring_length, substring_start);
			// strncpy(buf, content+ovector[2*j], ovector[2*j+1]-ovector[2*j]);
			// pcre_copy_substring(content, ovector, rc, 0, buffer, size);
		}
		offset = ovector[2 * (rc - 1)];
		//offset = ovector[1];
		flags |= PCRE_NOTBOL;
	}

	pcre_free(re); // finished matching

	return 0;
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

	http_client_t *http_client;
	http_resp_t *http_resp = NULL;

	printf("%s:%s:%s\n", name, source, dest);
	json_t *regular = json_object_get(cmd, "regular");
	if (cmd && json_is_array(regular)) {
		int i;
		int count = json_array_size(regular);
		for (i = 0; i < count; i++) {
			json_t *p = json_array_get(regular, i);
			const char *r = json_string_value(p);
			printf("regular[%d] = %s\n", i, r);
		}
	}

	http_client = http_init_connection(source);
	if (http_client == NULL) {
		printf("no client\n");
		return (1);
	}
	ret = http_get(http_client, "", &http_resp);
	printf("ret= %d, http_resp=%p\n", ret, http_resp);
	if (ret && http_resp) {
		printf("%s\n", http_resp->body);
	}

	return 0;
}

bool KolaClient::Login(void)
{
	json_error_t error;
	char *data = NULL, *filename = NULL;//http_get("127.0.0.1", 9990, "video/login?user_id=123123");
	char typebuf[70];
	int len;
	int ret;
	http_client_t *http_client;
	http_resp_t *http_resp = NULL;
	const char *url = "http://127.0.0.1:9990";

	http_client = http_init_connection(url);
	if (http_client == NULL) {
		printf("no client\n");
		return (1);
	}

	ret = http_get(http_client, "/video/login?user_id=123123", &http_resp);
	if (http_resp) {
		json_t *js = json_loads(http_resp->body, JSON_REJECT_DUPLICATES, &error);
		if (js) {
			const char *v = json_gets(js, "key", "");
			printf("===================================================\n");
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
		}
	}
	http_resp_free(http_resp);
	http_free_connection(http_client);

	return 0;
}

int main(int argc, char **argv)
{
	KolaClient kola;

	kola.Login();
	return 0;
}


