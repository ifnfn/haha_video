#ifndef __MPEG4IP_HTTP_PRIVATE_H__
#define __MPEG4IP_HTTP_PRIVATE_H__ 1


#include <ctype.h>
#include <string.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <fcntl.h>
#include <netdb.h>
#include <unistd.h>
#include <time.h>
#include <zlib.h>
#include <sys/ioctl.h>

#ifdef CURL
#include <curl/curl.h>
#include <curl/types.h>
#include <curl/easy.h>
#else
#include "httplib.h"
#endif

#define LOG_EMERG 0
#define LOG_ALERT 1
#define LOG_CRIT 2
#define LOG_ERR 3
#define LOG_WARNING 4
#define LOG_NOTICE 5
#define LOG_INFO 6
#define LOG_DEBUG 7

#define CHECK_AND_FREE(a) if ((a) != NULL) { free((void *)(a)); (a) = NULL;}
#define ADV_SPACE(a) {while (isspace(*(a)) && (*(a) != '\0'))(a)++;}

typedef enum {
	HTTP_STATE_INIT,
	HTTP_STATE_CONNECTED,
	HTTP_STATE_CLOSED
} http_state_t;

#define RESP_BUF_SIZE 2048

#define NONBLOCK 0
#define BLOCK 1

struct http_client_ {
	const char *m_orig_url;
	const char *m_current_url;
	const char *m_host;
	const char *m_resource;
	const char *m_content_location;
	const char *m_cookie;
	http_state_t m_state;
	uint16_t m_redirect_count;
	uint16_t m_redirect_count_max;
	const char *m_redir_location;
	uint16_t m_port;
	struct in_addr m_server_addr;
	int m_server_socket;

	// headers decoded
	int m_connection_close;
	int m_content_len_received;
	int m_transfer_encoding_chunked;
	int m_gzip_encoding;
	uint32_t m_content_len;
	http_resp_t *m_resp;

	// http response buffers
	uint32_t m_buffer_len, m_offset_on;
	char m_resp_buffer[RESP_BUF_SIZE + 1];
};

#define FREE_CHECK(a,b){ if (a->b != NULL) { free((void *)a->b); a->b = NULL;}}

int http_decode_and_connect_url (const char *name, http_client_t *ptr);

int http_build_header(char *buffer, uint32_t maxlen, uint32_t *at,
		http_client_t *cptr, const char *method,
		const char *add_header, const char *content_body, const char *referer);

int http_get_response(http_client_t *handle, http_resp_t **resp);

void http_resp_clear(http_resp_t *rptr);

#ifndef MIN
#define	MIN(a,b) (((a)<(b))?(a):(b))
#endif

#ifndef _WIN32
#define closesocket(p) close(p)
#endif
void http_debug(int loglevel, const char *fmt, ...)
#ifndef _WIN32
	__attribute__((format(__printf__, 2, 3)));
#endif
	;

#endif

static char _x2c(char hex_up, char hex_low)
{
	char digit;
	digit = 16 * (hex_up >= 'A' ? ((hex_up & 0xdf) - 'A') + 10 : (hex_up - '0'));
	digit += (hex_low >= 'A' ? ((hex_low & 0xdf) - 'A') + 10 : (hex_low - '0'));

	return (digit);
}


/**********************************************
 ** Usage : qURLencode(string to encode);
 ** Return: Pointer of encoded str which is memory allocated.
 ** Do    : Encode string.
 **********************************************/
char *URLencode(const char *str)
{
	char *encstr, buf[2+1];
	unsigned char c;
	int i, j;

	if(str == NULL) return NULL;
	if((encstr = (char *)malloc((strlen(str) * 3) + 1)) == NULL) return NULL;

	for(i = j = 0; str[i]; i++) {
		c = (unsigned char)str[i];
		if((c >= '0') && (c <= '9')) encstr[j++] = c;
		else if((c >= 'A') && (c <= 'Z')) encstr[j++] = c;
		else if((c >= 'a') && (c <= 'z')) encstr[j++] = c;
		else if((c == '@') || (c == '.') || (c == '/') || (c == '\\')
				|| (c == '-') || (c == '_') || (c == ':') ) encstr[j++] = c;
		else {
			sprintf(buf, "%02x", c);
			encstr[j++] = '%';
			encstr[j++] = buf[0];
			encstr[j++] = buf[1];
		}
	}
	encstr[j] = '\0';

	return encstr;
}

/**********************************************
 ** Usage : qURLdecode(query pointer);
 ** Return: Pointer of query string.
 ** Do    : Decode query string.
 **********************************************/
char *URLdecode(char *str)
{
	int i, j;

	if(!str) return NULL;
	for(i = j = 0; str[j]; i++, j++) {
		switch(str[j]) {
			case '+':{
					 str[i] = ' ';
					 break;
				 }
			case '%':{
					 str[i] = _x2c(str[j + 1], str[j + 2]);
					 j += 2;
					 break;
				 }
			default:{
					str[i] = str[j];
					break;
				}
		}
	}
	str[i]='\0';

	return str;
}

static char *convert_url(const char *to_convert)
{
	char *ret, *p;
	const char *q;
	size_t count;
	static const char *allowed="-_.!~*'();/?:@&=+$,";
	if (to_convert == NULL) return NULL;

	count = 0;
	q = to_convert;
	while (*q != '\0') {
		if (isalnum(*q)) count++;
		else if (strchr(allowed, *q) != NULL) {
			count++;
		} else count += 3;
		q++;
	}
	count++;

	ret = (char *)malloc(count);
	p = ret;
	while (*to_convert != '\0') {
		if (isalnum(*to_convert)) *p++ = *to_convert++;
		else if (strchr(allowed, *to_convert) != NULL) *p++ = *to_convert++;
		else {
			*p++ = '%';
			*p++ = '0' + ((*to_convert >> 4) & 0xf);
			*p++ = '0' + (*to_convert & 0xf);
			to_convert++;
		}
	}
	*p++ = *to_convert; // final \0
	return ret;
}

/* HTTP gzip decompress */
static int httpgzdecompress(Byte *zdata, uLong nzdata, Byte *data, uLong *ndata)
{
	int err = 0;
	z_stream d_stream; /* decompression stream */
	static char dummy_head[2] = {
		0x8 + 0x7 * 0x10,
		(((0x8 + 0x7 * 0x10) * 0x100 + 30) / 31 * 31) & 0xFF,
	};
	d_stream.zalloc = (alloc_func)0;
	d_stream.zfree = (free_func)0;
	d_stream.opaque = (voidpf)0;
	d_stream.next_in  = zdata;
	d_stream.avail_in = 0;
	d_stream.next_out = data;
	if(inflateInit2(&d_stream, 47) != Z_OK) {
		return -1;
	}
	while (d_stream.total_out < *ndata && d_stream.total_in < nzdata) {
		d_stream.avail_in = d_stream.avail_out = 1; /* force small buffers */
		if((err = inflate(&d_stream, Z_NO_FLUSH)) == Z_STREAM_END) {
			break;
		}
		if(err != Z_OK ) {
			if(err == Z_DATA_ERROR) {
				d_stream.next_in = (Bytef*) dummy_head;
				d_stream.avail_in = sizeof(dummy_head);
				if( (err = inflate(&d_stream, Z_NO_FLUSH)) != Z_OK) {
					return -1;
				}
			} else {
				return -1;
			}
		}
	}
	if(inflateEnd(&d_stream) != Z_OK) {
		return -1;
	}
	*ndata = d_stream.total_out;

	return 0;
}

int is_reallyconnect(int socket_fd)
{
	int ret;
	int count = 0;
	fd_set fds_write;
	fd_set fds_read;

	while (count++ < 100) {
		struct timeval tv;
		FD_ZERO(&fds_write);
		FD_SET(socket_fd, &fds_write);
		FD_ZERO(&fds_read);
		FD_SET(socket_fd, &fds_read);
		tv.tv_sec = 0;
		tv.tv_usec = 100 * 1000;

		ret = select(socket_fd + 1, &fds_read, &fds_write, NULL, &tv);
		if (ret < 0) {
			if(errno != EINTR){
				printf("connect socket select failed!\n");
				return -1;
			}
		}
		else if(ret > 0){
			if(FD_ISSET(socket_fd, &fds_read)||FD_ISSET(socket_fd, &fds_write)){
				int err;
				socklen_t err_len = sizeof(int);

				ret = getsockopt(socket_fd, SOL_SOCKET, SO_ERROR, &err, &err_len);

				if (ret == 0)
					break;
				else
					return -1;
			}
		}
	}

	if (count >= 30)
		return -1;

	return 0;
}

int tcp_connect2(const char *host, int port, int block)
{
	int sockfd, n;
	struct addrinfo hints, *res, *ressave;
	char serv[64];

	bzero(&hints,sizeof(hints));
	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_STREAM;

	sprintf(serv, "%d", port);

	if( (n = getaddrinfo(host, serv, &hints,&res)) != 0)
		printf("tcp_connect error for %s %s : %s\n",host,serv, gai_strerror(n));

	ressave = res;

	do{
		int opt = 1;
		sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
		if(sockfd < 0)
			continue;

		if( block == NONBLOCK ) {
			if (ioctl(sockfd, FIONBIO, &opt) < 0) {
				close(sockfd);
				sockfd = -1;
				continue;
			}
		}

		if (connect(sockfd, res->ai_addr, res->ai_addrlen) < 0) {
			if( block == NONBLOCK ) {
				if( errno != EINPROGRESS ) {
					printf("connect error : %s\n", strerror(errno));
					close(sockfd);
					sockfd = -1;
					continue;
				}

				if (is_reallyconnect(sockfd) != 0) {
					close(sockfd);
					sockfd = -1;
					continue;
				}
				opt = 0;
				if (ioctl(sockfd, FIONBIO, &opt) < 0) {
					close(sockfd);
					sockfd = -1;
					continue;
				}
			}
		}

		if (sockfd > 0)
			break;
	} while( (res = res->ai_next) != NULL);

	if(res == NULL)
		printf("tcp_connect error for %s %s\n",host,serv);

	freeaddrinfo(ressave);

	return (sockfd);
}

int tcp_connect(struct in_addr addr, unsigned short port, int block)
{
	int sock;
	struct sockaddr_in servaddr;
	fd_set rset, wset;
	int n;
	int maxfd;
	int opt = 1;
	struct timeval tval;
	unsigned int len, error;

	if( (sock = socket(AF_INET, SOCK_STREAM, 0)) == -1 )
	{
		printf("socket error : %s\n", strerror(errno));
		return -1;
	}

	servaddr.sin_family = AF_INET;
	servaddr.sin_port = htons(port);
	servaddr.sin_addr = addr;

	if (ioctl(sock, FIONBIO, &opt) < 0) {
		close(sock);
		perror("ioctl");
		return -1;
	}

	if( connect(sock, (struct sockaddr*)&servaddr, sizeof(servaddr)) < 0 ) {
		if( errno != EINPROGRESS ) {
			printf("connect error : %s\n", strerror(errno));
			return -1;
		}

		if( block == NONBLOCK ) {
			FD_ZERO(&rset);
			FD_SET(sock, &rset);
			wset = rset;
			maxfd = sock;
			tval.tv_sec = 30;
			tval.tv_usec = 0;

			if( (n = select(maxfd + 1, &rset, &wset, NULL, &tval)) == 0 ) {
				close(sock);
				errno = ETIMEDOUT;
				printf("network timeout 10s!\n");
				return -1;
			}

			if( FD_ISSET(sock, &rset) || FD_ISSET(sock, &wset) ) {
				len = sizeof(error);
				if( getsockopt(sock, SOL_SOCKET, SO_ERROR, &error, &len) < 0 ) {
					return -1;
				}
			}
			else
				printf("select error : sockfd not set\n");

			opt = 0;
			//set blocking
			if (ioctl(sock, FIONBIO, &opt) < 0) {
				close(sock);
				errno = error;
				return -1;
			}
		}
	}

	return sock;
}

/*
 * http_init_connection()
 * decode url and make connection
 */
http_client_t *http_init_connection(const char *name)
{
	http_client_t *ptr;
	char *url;
#ifdef _WIN32
	WORD wVersionRequested;
	WSADATA wsaData;
	int ret;

	wVersionRequested = MAKEWORD( 2, 0 );

	ret = WSAStartup( wVersionRequested, &wsaData );
	if ( ret != 0 ) {
		/* Tell the user that we couldn't find a usable */
		/* WinSock DLL.*/
		http_debug(LOG_ERR, "Can't initialize http_debug");
		return NULL;
	}
#endif
	ptr = (http_client_t *)malloc(sizeof(http_client_t));
	if (ptr == NULL) {
		return NULL;
	}

	memset(ptr, 0, sizeof(http_client_t));
	ptr->m_state = HTTP_STATE_INIT;
	url = convert_url(name);
	ptr->m_redirect_count_max = 5;
	http_debug(LOG_INFO, "Connecting to %s", url);
	if (http_decode_and_connect_url(url, ptr) < 0) {
		free(url);
		http_free_connection(ptr);
		return NULL;
	}
	free(url);
	return ptr;
}

/*
 * http_free_connection - disconnect (if still connected) and free up
 * everything to do with this session
 */
void http_free_connection (http_client_t *ptr)
{
	if (ptr->m_state == HTTP_STATE_CONNECTED) {
		closesocket(ptr->m_server_socket);
		ptr->m_server_socket = -1;
	}
	FREE_CHECK(ptr, m_orig_url);
	FREE_CHECK(ptr, m_current_url);
	FREE_CHECK(ptr, m_host);
	FREE_CHECK(ptr, m_resource);
	FREE_CHECK(ptr, m_redir_location);
	FREE_CHECK(ptr, m_content_location);
	FREE_CHECK(ptr, m_cookie);
	free(ptr);
#ifdef _WIN32
	WSACleanup();
#endif
}

void http_set_location(http_client_t *cptr, int maxlen)
{
	cptr->m_redirect_count_max = maxlen;
}
/*
 * http_get - get from url after client already set up
 */
int http_get(http_client_t *cptr, const char *url, http_resp_t **resp, const char *cookie, const char *referer)
{
	char header_buffer[4096];
	uint32_t buffer_len;
	int ret;
	int more;
	char cookie_buffer[2048];

	if (cptr == NULL)
		return -1;

	if (*resp != NULL) {
		http_resp_clear(*resp);
	}

	http_debug(LOG_DEBUG, "url is %s\n", url);
	if (url != NULL) {
		if (http_decode_and_connect_url(url, cptr) < 0) {
			http_debug(LOG_DEBUG, "resource is now %s", url);
			CHECK_AND_FREE(cptr->m_resource);
			cptr->m_resource = strdup(url);
		}
	} else {
		cptr->m_resource = cptr->m_content_location;
		cptr->m_content_location = NULL;
	}

	if (cookie) {
		sprintf(cookie_buffer, "Cookie: %s", cookie);
		cookie = cookie_buffer;
	}
	else if (cptr->m_cookie) {
		sprintf(cookie_buffer, "Cookie: %s", cptr->m_cookie);
		cookie = cookie_buffer;
	}

	buffer_len = 0;
	/*
	 * build header and send message
	 */
	ret = http_build_header(header_buffer, 4096, &buffer_len, cptr, "GET", cookie, NULL, referer);
	http_debug(LOG_DEBUG, "%s", header_buffer);
	if (send(cptr->m_server_socket,
				header_buffer,
				buffer_len,
				0) < 0) {
		http_debug(LOG_CRIT,"Http send failure");
		return -1;
	}
	cptr->m_redirect_count = 0;
	more = 0;
	/*
	 * get response - handle redirection here
	 */
	do {
		ret = http_get_response(cptr, resp);
		http_debug(LOG_INFO, "Response %d", (*resp)->ret_code);
		http_debug(LOG_DEBUG, "%s", (*resp)->body);
		if (ret < 0) return ret;
		switch ((*resp)->ret_code / 100) {
			default:
			case 1:
				more = 0;
				break;
			case 2:
				return 1;
			case 3:
				cptr->m_redirect_count++;
				if (cptr->m_redirect_count > cptr->m_redirect_count_max) {
					return 1;
				}
				if (http_decode_and_connect_url(cptr->m_redir_location, cptr) < 0) {
					http_debug(LOG_CRIT, "Couldn't reup location %s", cptr->m_redir_location);
					return -1;
				}
				buffer_len = 0;
				ret = http_build_header(header_buffer, 4096, &buffer_len, cptr, "GET", cookie, NULL, referer);
				http_debug(LOG_DEBUG, "%s", header_buffer);
				if (send(cptr->m_server_socket, header_buffer, buffer_len, 0) < 0) {
					http_debug(LOG_CRIT,"Send failure");
					return -1;
				}

				break;
			case 4:
			case 5:
				return 0;
		}
	} while (more == 0);

	return ret;
}

int http_post(http_client_t *cptr, const char *url, http_resp_t **resp, const char *body, const char *cookie, const char *referer)
{
	char *header_buffer;
	uint32_t buffer_len, max_len = 2048;
	int ret = -1;
	int more;
	char *encode_body = NULL;
	char cookie_buffer[256] = "Content-Type: application/x-www-form-urlencoded";

	if (cptr == NULL)
		return -1;

	if (*resp != NULL) {
		http_resp_clear(*resp);
	}
	buffer_len = 0;
	if (url != NULL) {
		CHECK_AND_FREE(cptr->m_resource);
		cptr->m_resource = strdup(url);
	}

	if (body && strlen(body) > 0) {
		encode_body = URLencode(body);
		max_len = strlen(encode_body) + 2048;
	}
	header_buffer = (char*)malloc(max_len);

	if (cookie) {
		sprintf(cookie_buffer, "Content-Type: application/x-www-form-urlencoded\r\nCookie: %s", cookie);
		cookie = cookie_buffer;
	}

	/*
	 * build header and send message
	 */
	ret = http_build_header(header_buffer, max_len - 1, &buffer_len, cptr, "POST", cookie, encode_body, referer);
	if (ret == -1) {
		http_debug(LOG_ERR, "Could not build header");
		goto out;
	}
	http_debug(LOG_DEBUG, "%s", header_buffer);
	if (send(cptr->m_server_socket,
				header_buffer,
				buffer_len,
				0) < 0) {
		http_debug(LOG_CRIT,"Http send failure");
		goto out;
	}
	cptr->m_redirect_count = 0;
	more = 0;

	/*
	 * get response - handle redirection here
	 */
	do {
		ret = http_get_response(cptr, resp);
		http_debug(LOG_INFO, "Response %d", (*resp)->ret_code);
		http_debug(LOG_DEBUG, "%s", (*resp)->body);
		if (ret < 0)
			goto out;
		switch ((*resp)->ret_code / 100) {
			default:
			case 1:
				more = 0;
				break;
			case 2:
				ret = 1;
				goto out;
			case 3:
				cptr->m_redirect_count++;
				if (cptr->m_redirect_count > 5) {
					goto out;
				}
				if (http_decode_and_connect_url(cptr->m_redir_location, cptr) < 0) {
					http_debug(LOG_CRIT, "Couldn't reup location %s", cptr->m_redir_location);
					goto out;
				}
				buffer_len = 0;
				ret = http_build_header(header_buffer, 4096, &buffer_len, cptr, "POST", cookie,  encode_body, referer);
				http_debug(LOG_DEBUG, "%s", header_buffer);
				if (send(cptr->m_server_socket,
							header_buffer,
							buffer_len,
							0) < 0) {
					http_debug(LOG_CRIT,"Send failure");
					goto out;
				}

				break;
			case 4:
			case 5:
				ret = 0;
				goto out;
		}
	} while (more == 0);

out:
	free(header_buffer);
	free(encode_body);
	return ret;
}

/*
 * http_disect_url
 * Carve URL up into portions that we can use - store them in the
 * client structure.  url points after http:://
 * We're looking for m_host (destination name), m_port (destination port)
 * and m_resource (location of file on m_host - also called path)
 */
static int http_dissect_url(const char *name, http_client_t *cptr)
{
	// Assume name points at host name
	const char *uptr = name;
	const char *nextslash, *nextcolon, *rightbracket;
	char *host;
	size_t hostlen;

	// skip ahead after host
	rightbracket = NULL;
	if (*uptr == '[') {
		rightbracket = strchr(uptr, ']');
		if (rightbracket != NULL) {
			uptr++;
			// literal IPv6 address
			if (rightbracket[1] == ':') {
				nextcolon = rightbracket + 1;
			} else
				nextcolon = NULL;
			nextslash = strchr(rightbracket, '/');
		} else
			return -1;
	}
	else {
		nextslash = strchr(uptr, '/');
		nextcolon = strchr(uptr, ':');
	}

	cptr->m_port = 80;
	if (nextslash != NULL || nextcolon != NULL) {
		if (nextcolon != NULL && (nextcolon < nextslash || nextslash == NULL)) {
			hostlen = nextcolon - uptr;
			// have a port number
			nextcolon++;
			cptr->m_port = 0;
			while (isdigit(*nextcolon)) {
				cptr->m_port *= 10;
				cptr->m_port += *nextcolon - '0';
				nextcolon++;
			}
			if (cptr->m_port == 0 || (*nextcolon != '/' && *nextcolon != '\0')) {
				return -1;
			}
		}
		else {
			// no port number
			hostlen = nextslash - uptr;

		}
		if (hostlen == 0)
			return -1;

		FREE_CHECK(cptr, m_host);
		if (rightbracket != NULL) hostlen--;
		host = (char*)malloc(hostlen + 1);
		if (host == NULL)
			return -1;

		memcpy(host, uptr, hostlen);
		host[hostlen] = '\0';
		cptr->m_host = host;
	}
	else {
		if (*uptr == '\0')
			return EINVAL;

		FREE_CHECK(cptr, m_host);
		host = strdup(uptr);
		if (rightbracket != NULL)
			host[strlen(host) - 1] = '\0';

		cptr->m_host = host;
	}

	FREE_CHECK(cptr, m_content_location);
	if (nextslash != NULL) {
		cptr->m_content_location = strdup(nextslash);
	} else {
		cptr->m_content_location = strdup("/");
	}
	http_debug(LOG_DEBUG, "content location is %s", cptr->m_content_location);
	return 0;
}

/*
 * http_decode_and_connect_url
 * decode the url, and connect it.  If we were already connected,
 * disconnect the socket and move forward
 */
int http_decode_and_connect_url (const char *name, http_client_t *cptr)
{
	int check_open;
	uint16_t port;
	const char *old_host;
	struct hostent *host;

	if (strncasecmp(name, "http://", strlen("http://")) != 0) {
		return -1;
	}
	name += strlen("http://");

	check_open = 0;
	port = 80;
	old_host = NULL;
	if (cptr->m_state == HTTP_STATE_CONNECTED) {
		check_open = 1;
		port = cptr->m_port;
		old_host = cptr->m_host;
		cptr->m_host = NULL; // don't inadvertantly free it
	}

	if (http_dissect_url(name, cptr) < 0) {
		// If there's an error - nothing's changed
		return -1;
	}

	if (check_open) {
		// See if the existing host matches the new one
		int match = 0;
		// Compare strings, first
		if (strcasecmp(old_host, cptr->m_host) == 0) {
			// match
			if (port == cptr->m_port)
				match = 1;
		}
#if 0
		else {
			// Might be same - resolve new address and compare
			host = gethostbyname(cptr->m_host);
			if (host == NULL)
				return -1;

			if (memcmp(host->h_addr, &cptr->m_server_addr, sizeof(struct in_addr)) == 0 && (port == cptr->m_port))
				match = 1;
			else
				cptr->m_server_addr = *(struct in_addr *)host->h_addr;
		}
#endif
		free((void *)old_host); // free off the old one we saved

		if (match == 0) {
			cptr->m_state = HTTP_STATE_CLOSED;
			closesocket(cptr->m_server_socket);
			cptr->m_server_socket = -1;
		}
		else {
			// keep using the same socket...
			return 0;
		}
	}
#if 0
	else {
		// No existing connection - get the new address.
		host = gethostbyname(cptr->m_host);
		if (host == NULL)
			return -1;

		cptr->m_server_addr = *(struct in_addr *)host->h_addr;
	}
#endif

	cptr->m_server_socket = tcp_connect2(cptr->m_host, cptr->m_port, NONBLOCK);
	if (cptr->m_server_socket == -1)
		return -1;

	cptr->m_state = HTTP_STATE_CONNECTED;
	return 0;
}

static const char *user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0";

/*
 * http_build_header - create a header string
 * Will eventually want to expand this if we want to specify
 * content type, etc.
 */
int http_build_header (char *buffer,
		uint32_t maxlen,
		uint32_t *at,
		http_client_t *cptr,
		const char *method,
		const char *add_header, const char *content_body, const char *referer)
{
	int ret;
#define SNPRINTF_CHECK(fmt, ...) \
	ret = snprintf(buffer + *at, maxlen - *at, (fmt), __VA_ARGS__); \
	if (ret == -1) { \
		return -1; \
	}\
	*at += ret;

	SNPRINTF_CHECK("%s ", method);
	if (cptr->m_content_location != NULL &&
			(strcmp(cptr->m_content_location, "/") != 0 ||
			 *cptr->m_resource != '/')) {
		SNPRINTF_CHECK("%s", cptr->m_content_location);
	}
	SNPRINTF_CHECK("%s HTTP/1.1\r\n"         , cptr->m_resource);
	if (cptr->m_port != 80) {
		SNPRINTF_CHECK("Host: %s:%d\r\n" , cptr->m_host, cptr->m_port);
	}
	else {
		SNPRINTF_CHECK("Host: %s\r\n"    , cptr->m_host);
	}
	SNPRINTF_CHECK("User-Agent: %s\r\n"      , user_agent);
	SNPRINTF_CHECK("Accept: %s\r\n"          , "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
	SNPRINTF_CHECK("Connection: %s\r\n"      , "Kepp-Alive");
	SNPRINTF_CHECK("Accept-Encoding: %s\r\n" , "gzip");
	SNPRINTF_CHECK("Referer: %s\r\n"         , referer);
	if (add_header != NULL) {
		SNPRINTF_CHECK("%s\r\n", add_header);
	}
	if (content_body != NULL) {
		int len = strlen(content_body);
		SNPRINTF_CHECK("Content-length: %d\r\n\r\n", len);
		SNPRINTF_CHECK("%s", content_body);
	} else {
		SNPRINTF_CHECK("%s", "\r\n");
	}


	printf("buffer=%s\n", buffer);
#undef SNPRINTF_CHECK
	return ret;
}

static int http_recv (int server_socket,
		char *buffer,
		uint32_t len)
{
	int ret;
#ifdef HAVE_POLL
	struct pollfd pollit;

	pollit.fd = server_socket;
	pollit.events = POLLIN | POLLPRI;
	pollit.revents = 0;

	ret = poll(&pollit, 1, 2000);
#else
	fd_set read_set;
	struct timeval timeout;
	FD_ZERO(&read_set);
	FD_SET(server_socket, &read_set);
	timeout.tv_sec = 2;
	timeout.tv_usec = 0;
	ret = select(server_socket + 1, &read_set, NULL, NULL, &timeout);
#endif
	if (ret <= 0) {
		return -1;
	}

	ret = recv(server_socket, buffer, len, 0);
	http_debug(LOG_DEBUG, "Return from recv is %d", ret);
	return ret;
}

/*
 * http_read_into_buffer - read bytes into buffer at the buffer offset
 * to the end of the buffer.
 */
static int http_read_into_buffer (http_client_t *cptr,
		uint32_t buffer_offset)
{
	int ret;

	ret = http_recv(cptr->m_server_socket,
			cptr->m_resp_buffer + buffer_offset,
			RESP_BUF_SIZE - buffer_offset);

	if (ret <= 0) return ret;

	cptr->m_buffer_len = buffer_offset + ret;

	return ret;
}

/*
 * http_get_next_line()
 * Use the existing buffers that we've read, and try to get a coherent
 * line.  This saves having to do a bunch of 1 byte reads looking for a
 * cr/lf - instead, we read as many bytes as we can into the buffer, and
 * then process it.
 */
static const char *http_get_next_line (http_client_t *cptr)
{
	int ret;
	uint32_t ix;
	int last_on;

	/*
	 * If we don't have any data, try to read a buffer full
	 */
	if (cptr->m_buffer_len <= 0) {
		cptr->m_offset_on = 0;
		ret = http_read_into_buffer(cptr, 0);
		if (ret <= 0) {
			return NULL;
		}
	}

	/*
	 * Look for CR/LF in the buffer.  If we find it, NULL terminate at
	 * the CR, then set the buffer values to look past the crlf
	 */
	for (ix = cptr->m_offset_on + 1;
			ix < cptr->m_buffer_len;
			ix++) {
		if (cptr->m_resp_buffer[ix] == '\n' &&
				cptr->m_resp_buffer[ix - 1] == '\r') {
			const char *retval = &cptr->m_resp_buffer[cptr->m_offset_on];
			cptr->m_offset_on = ix + 1;
			cptr->m_resp_buffer[ix - 1] = '\0'; // make it easy
			return retval;
		}
	}

	if (cptr->m_offset_on == 0) {
		return NULL;
	}

	/*
	 * We don't have a line.  So, move the data down in the buffer, then
	 * read into the rest of the buffer
	 */
	cptr->m_buffer_len -= cptr->m_offset_on;
	if (cptr->m_buffer_len != 0) {
		memmove(cptr->m_resp_buffer,
				&cptr->m_resp_buffer[cptr->m_offset_on],
				cptr->m_buffer_len);
		last_on = cptr->m_buffer_len;
	} else {
		last_on = 1;
	}
	cptr->m_offset_on = 0;

	ret = http_read_into_buffer(cptr, cptr->m_buffer_len);
	if (ret <= 0) {
		return NULL;
	}

	/*
	 * Continue searching through the buffer.  If we get this far, we've
	 * received like 2K or 4K without a CRLF - most likely a bad response
	 */
	for (ix = last_on;
			ix < cptr->m_buffer_len;
			ix++) {
		if (cptr->m_resp_buffer[ix] == '\n' &&
				cptr->m_resp_buffer[ix - 1] == '\r') {
			const char *retval = &cptr->m_resp_buffer[cptr->m_offset_on];
			cptr->m_offset_on = ix + 1;
			cptr->m_resp_buffer[ix - 1] = '\0'; // make it easy
			return retval;
		}
	}
	return NULL;
}

/****************************************************************************
 * HTTP header decoding
 ****************************************************************************/

#define HTTP_CMD_DECODE_FUNC(a) static void a(const char *lptr, http_client_t *cptr)

/*
 * Connection: header
 */
HTTP_CMD_DECODE_FUNC(http_cmd_connection)
{
	// connection can be comma seperated list.
	while (*lptr != '\0') {
		if (strncasecmp(lptr, "close", strlen("close")) == 0) {
			cptr->m_connection_close = 1;
			return;
		} else {
			while (*lptr != '\0' && *lptr != ',') lptr++;
		}
	}
}

/*
 * Content-length: header
 */
HTTP_CMD_DECODE_FUNC(http_cmd_content_length)
{
	cptr->m_content_len = 0;
	while (isdigit(*lptr)) {
		cptr->m_content_len_received = 1;
		cptr->m_content_len *= 10;
		cptr->m_content_len += *lptr - '0';
		lptr++;
	}
}

/*
 * Content-type: header
 */
HTTP_CMD_DECODE_FUNC(http_cmd_content_type)
{
	FREE_CHECK(cptr->m_resp, content_type);
	cptr->m_resp->content_type = strdup(lptr);
}

/*
 * Location: header
 */
HTTP_CMD_DECODE_FUNC(http_cmd_location)
{
	FREE_CHECK(cptr, m_redir_location);
	cptr->m_redir_location = strdup(lptr);
}

/*
 * Transfer-Encoding: header
 */
HTTP_CMD_DECODE_FUNC(http_cmd_transfer_encoding)
{
	do {
		if (strncasecmp(lptr, "chunked", strlen("chunked")) == 0) {
			cptr->m_transfer_encoding_chunked = 1;
			return;
		}
		while ((*lptr != '\0') && (*lptr != ';')) lptr++;
		ADV_SPACE(lptr);
	} while (*lptr != '\0');
}

HTTP_CMD_DECODE_FUNC(http_cmd_gzip_encoding)
{
	do {
		if (strncasecmp(lptr, "gzip", strlen("gzip")) == 0) {
			cptr->m_gzip_encoding = 1;
			return;
		}
		while ((*lptr != '\0') && (*lptr != ';')) lptr++;
		ADV_SPACE(lptr);
	} while (*lptr != '\0');
}

HTTP_CMD_DECODE_FUNC(http_cmd_set_cookie)
{
	cptr->m_cookie = strdup(lptr);
	do {
		if (strncasecmp(lptr, "_xsrf", strlen("_xsrf")) == 0) {
			const char *p = (char *)strstr(lptr, ";");
			if (p) {
				cptr->m_resp->xsrf_cookie = (const char*)calloc(1, p - lptr + 1);

				memcpy((void*)cptr->m_resp->xsrf_cookie, (void*)lptr, p - lptr);
				printf("%s: %s\n", cptr->m_host, cptr->m_resp->xsrf_cookie);
				return;
			}
		}
		while (*lptr != '\0') lptr++;
		ADV_SPACE(lptr);
	} while (*lptr != '\0');
}

static struct {
	const char *val;
	uint32_t val_length;
	void (*parse_routine)(const char *lptr, http_client_t *cptr);
} header_types[] =
{
#define HEAD_TYPE(a, b) { a, sizeof(a), b }
	HEAD_TYPE("connection", http_cmd_connection),
	HEAD_TYPE("content-length", http_cmd_content_length),
	HEAD_TYPE("content-type", http_cmd_content_type),
	HEAD_TYPE("location", http_cmd_location),
	HEAD_TYPE("transfer-encoding", http_cmd_transfer_encoding),
	HEAD_TYPE("Content-Encoding" , http_cmd_gzip_encoding),
	HEAD_TYPE("set-cookie", http_cmd_set_cookie),

	{NULL, 0, NULL },
};

static void http_decode_header (http_client_t *cptr, const char *lptr)
{
	int ix;
	const char *after;

	ix = 0;
	ADV_SPACE(lptr);

	while (header_types[ix].val != NULL) {
		if (strncasecmp(lptr,
					header_types[ix].val,
					header_types[ix].val_length - 1) == 0) {
			after = lptr + header_types[ix].val_length - 1;
			ADV_SPACE(after);
			if (*after == ':') {
				after++;
				ADV_SPACE(after);
				/*
				 * Call the correct parsing routine
				 */
				(header_types[ix].parse_routine)(after, cptr);
				return;
			}
		}
		ix++;
	}

	//rtsp_debug(LOG_DEBUG, "Not processing response header: %s", lptr);
}

static uint32_t to_hex (const char **hex_string)
{
	const char *p = *hex_string;
	uint32_t ret = 0;
	while (isxdigit(*p)) {
		ret *= 16;
		if (isdigit(*p)) {
			ret += *p - '0';
		} else {
			ret += tolower(*p) - 'a' + 10;
		}
		p++;
	}
	*hex_string = p;
	return ret;
}

/*
 * http_get_response - get the response, process it, and fill in the response
 * structure.
 */
int http_get_response (http_client_t *cptr, http_resp_t **resp)
{
	const char *p;
	int resp_code;
	int ix;
	int done;
	uint32_t len;
	int ret;

	/*
	 * Clear out old response header
	 */
	if (*resp != NULL) {
		cptr->m_resp = *resp;
		http_resp_clear(*resp);
	} else {
		cptr->m_resp = (http_resp_t *)malloc(sizeof(http_resp_t));
		memset(cptr->m_resp, 0, sizeof(http_resp_t));
		*resp = cptr->m_resp;
	}

	/*
	 * Reset all relevent variables
	 */
	FREE_CHECK(cptr, m_redir_location);
	cptr->m_connection_close = 0;
	cptr->m_content_len_received = 0;
	cptr->m_offset_on = 0;
	cptr->m_buffer_len = 0;
	cptr->m_transfer_encoding_chunked = 0;
	cptr->m_gzip_encoding = 0;

	/*
	 * Get the first line and process it
	 */
	p = http_get_next_line(cptr);
	if (p == NULL) {
		http_debug(LOG_INFO, "did not get first line");
		return -1;
	}

	/*
	 * http/version.version processing
	 */
	ADV_SPACE(p);
	if (*p == '\0' || strncasecmp(p, "http/", strlen("http/")) != 0) {
		http_debug(LOG_INFO, "first line did not start with HTTP/");
		return -1;
	}
	p += strlen("http/");
	ADV_SPACE(p);
	while (*p != '\0' && isdigit(*p)) p++;
	if (*p++ != '.') return -1;
	while (*p != '\0' && isdigit(*p)) p++;
	if (*p++ == '\0') return -1;
	ADV_SPACE(p);

	/*
	 * error code processing - 200 is gold
	 */
	resp_code = 0;
	for (ix = 0; ix < 3; ix++) {
		if (isdigit(*p)) {
			resp_code *= 10;
			resp_code += *p++ - '0';
		} else {
			http_debug(LOG_ERR, "did not get 3-digit response code");
			return -1;
		}
	}
	(*resp)->ret_code = resp_code;
	ADV_SPACE(p);
	if (*p != '\0') {
		(*resp)->resp_phrase = strdup(p);
	}

	/*
	 * Now begin processing the headers
	 */
	done = 0;
	do {
		p = http_get_next_line(cptr);
		if (p == NULL) {
			return -1;
		}
		if (*p == '\0') {
			done = 1;
		} else {
			http_debug(LOG_DEBUG, "%s", p);
			// we have a header.  See if we want to process it...
			http_decode_header(cptr, p);
		}
	} while (done == 0);

	// Okay - at this point - we have the headers done.  Let's
	// read the body
	if (cptr->m_content_len_received != 0) {
		/*
		 * We have content-length - read that many bytes.
		 */
		if (cptr->m_content_len != 0) {
			cptr->m_resp->body = (char *)calloc(1, cptr->m_content_len + 1);
			len = cptr->m_buffer_len - cptr->m_offset_on;
			memcpy(cptr->m_resp->body,
					&cptr->m_resp_buffer[cptr->m_offset_on],
					MIN(len, cptr->m_content_len));
			while (len < cptr->m_content_len) {
				ret = http_read_into_buffer(cptr, 0);
				if (ret <= 0) {
					return -1;
				}
				memcpy(cptr->m_resp->body + len,
						cptr->m_resp_buffer,
						MIN(cptr->m_content_len - len, cptr->m_buffer_len));
				len += cptr->m_buffer_len;
			}
			cptr->m_resp->body[cptr->m_content_len] = '\0';
			cptr->m_resp->body_len = cptr->m_content_len;
		}
	} else if (cptr->m_transfer_encoding_chunked != 0) {
		/*
		 * Chunk encoded - size in hex, body, size in hex, body, 0
		 */
		// read a line,
		uint32_t te_size;
		p = http_get_next_line(cptr);
		if (p == NULL) {
			http_debug(LOG_ALERT, "no chunk size reading chunk transitions");
			return -1;
		}
		te_size = to_hex(&p);
		cptr->m_resp->body = NULL;
		cptr->m_resp->body_len = 0;
		/*
		 * Read a te_size chunk of bytes, read CRLF at end of that many bytes,
		 * read next size
		 */
		while (te_size != 0) {
			http_debug(LOG_DEBUG, "Chunk size %d", te_size);
			cptr->m_resp->body = (char *)realloc(cptr->m_resp->body,
					cptr->m_resp->body_len + te_size + 1);
			len = MIN(te_size, cptr->m_buffer_len - cptr->m_offset_on);
			memcpy(cptr->m_resp->body + cptr->m_resp->body_len,
					&cptr->m_resp_buffer[cptr->m_offset_on],
					len);
			cptr->m_offset_on += len;
			cptr->m_resp->body_len += len;
			http_debug(LOG_DEBUG, "chunk - copied %d from rest of buffer(%d)",
					len, cptr->m_resp->body_len);
			while (len < te_size) {
				int ret;
				ret = http_recv(cptr->m_server_socket,
						cptr->m_resp->body + cptr->m_resp->body_len,
						te_size - len);
				if (ret <= 0) return -1;
				len += ret;
				cptr->m_resp->body_len += ret;
				http_debug(LOG_DEBUG, "chunk - recved %d bytes (%d)",
						ret, cptr->m_resp->body_len);
			}
			p = http_get_next_line(cptr); // should read CRLF at end
			if (p == NULL || *p != '\0') {
				http_debug(LOG_ALERT, "Http chunk reader - should be CRLF at end of chunk, is %s", p);
				return -1;
			}
			p = http_get_next_line(cptr); // read next size
			if (p == NULL) {
				http_debug(LOG_ALERT,"No chunk size after first");
				return -1;
			}
			te_size = to_hex(&p);
		}
		if (cptr->m_resp->body_len > 0)
			cptr->m_resp->body[cptr->m_resp->body_len] = '\0'; // null terminate
	} else {
		// No termination - just keep reading, I guess...
		len = cptr->m_buffer_len - cptr->m_offset_on;
		cptr->m_resp->body = (char *)malloc(len + 1);
		cptr->m_resp->body_len = len;
		memcpy(cptr->m_resp->body,
				&cptr->m_resp_buffer[cptr->m_offset_on],
				len);
		http_debug(LOG_INFO, "Len bytes copied - %d", len);
		while (http_read_into_buffer(cptr, 0) > 0) {
			char *temp;
			len = cptr->m_resp->body_len + cptr->m_buffer_len;
			temp = (char*)realloc(cptr->m_resp->body, len + 1);
			if (temp == NULL) {
				return -1;
			}
			cptr->m_resp->body = temp;
			memcpy(&cptr->m_resp->body[cptr->m_resp->body_len],
					cptr->m_resp_buffer,
					cptr->m_buffer_len);
			cptr->m_resp->body_len = len;
			http_debug(LOG_INFO, "Len bytes added - %d", len);
		}
		cptr->m_resp->body[cptr->m_resp->body_len] = '\0';
	}

	if (cptr->m_gzip_encoding != 0) {
		int multiple = 8;
		uLong ndata;
		Byte *data = NULL;
		while (multiple < 32) {
			ndata = cptr->m_resp->body_len * multiple;
			data = (Byte*)calloc(1, ndata + 1);
			if (httpgzdecompress((Byte*)cptr->m_resp->body, cptr->m_resp->body_len, data, &ndata) == 0) {
				if (ndata < cptr->m_resp->body_len * multiple)
					break;
			}
			multiple++;
			free(data);
			data = NULL;
		}

		if (data) {
			FREE_CHECK(cptr->m_resp, body);
			cptr->m_resp->body = (char*)data;
			cptr->m_resp->body_len = (uint32_t)ndata;
		}
	}

	return 0;
}

/*
 * http_resp_clear - clean out http_resp_t structure
 */
void http_resp_clear (http_resp_t *rptr)
{
	FREE_CHECK(rptr, body);
	FREE_CHECK(rptr, content_type);
	FREE_CHECK(rptr, resp_phrase);
	FREE_CHECK(rptr, xsrf_cookie);
}

/*
 * http_resp_free - clean out http_resp_t and free
 */
void http_resp_free (http_resp_t *rptr)
{
	if (rptr != NULL) {
		http_resp_clear(rptr);
		free(rptr);
	}
}

/*
 * Logging code
 */
//static int http_debug_level = LOG_ERR;
static int http_debug_level = LOG_EMERG ;

void http_set_loglevel (int loglevel)
{
	http_debug_level = loglevel;
}

void http_debug (int loglevel, const char *fmt, ...)
{
#if 0
	va_list ap;
	//if (loglevel <= http_debug_level) {
	if (1) {
		va_start(ap, fmt);
		struct timeval thistime;
		struct tm thistm;
		char buffer[80];
		time_t secs;

		gettimeofday(&thistime, NULL);
		// To add date, add %a %b %d to strftime
		secs = thistime.tv_sec;
		localtime_r(&secs, &thistm);
		strftime(buffer, sizeof(buffer), "%X", &thistm);
		printf("%s.%03ld-libhttp-%d: ",
				buffer, (unsigned long)thistime.tv_usec / 1000, loglevel);
		vprintf(fmt, ap);
		printf("\n");

		va_end(ap);
	}
#endif
}

