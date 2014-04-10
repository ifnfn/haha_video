#include <stdio.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <string.h>
#include <sys/select.h>

#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>


#include "webserver.hpp"
#include "request.h"
#include "debug.h"

#define MAX_CLIENT 32

void * WebServerThread(void * param)
{
	CWebserver *webserver = (CWebserver*)param;

	webserver->DoLoop();
	pthread_exit((void *)NULL);
	return NULL;
}

bool CWebserver::Start()
{
	SAI servaddr;
	int optval = 1;

	//network-setup
	ListenSocket = socket(AF_INET, SOCK_STREAM, 0);
	setsockopt( ListenSocket, SOL_SOCKET, SO_REUSEADDR, (const void*)&optval, sizeof(int) );

	memset(&servaddr, 0, sizeof(servaddr));
	servaddr.sin_family = AF_INET;
	servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
	servaddr.sin_port = htons(cfg.Port);

	if ( ::bind(ListenSocket, (SA *) &servaddr, sizeof(servaddr)) != 0) {
		int i = 1;
		do {
			aprintf("bind to port %d failed...\n", cfg.Port);
			aprintf("%d. Versuch, warte 5 Sekunden\n",i++);
			sleep(5);
		} while (::bind(ListenSocket, (SA *) &servaddr, sizeof(servaddr)) != 0);
	}

	if (listen(ListenSocket, MAX_CLIENT) != 0) {
			perror("listen failed...");
			return false;
	}
	pthread_create (&server_thread, NULL, WebServerThread, this);
	dprintf("Server Start\n");

	return true;
}

void * WebThread(void * args)
{
	CWebserverRequest *req = (CWebserverRequest*) args;
	pthread_detach(pthread_self());
	if(req->GetRawRequest()) {
		if(req->ParseRequest()) {
			req->SendResponse();
			req->PrintRequest();
			req->EndRequest();
		}
	}
	delete req;
	pthread_exit((void *)NULL);
	return NULL;
}

void sig_chld(int signo)
{
	pid_t pid;
	int stat;

	pid=wait(&stat);
	printf("child %d terminated(stat:%d)/n",pid,stat);
}

void CWebserver::DoLoop()
{
	socklen_t clilen;
	SAI cliaddr;
	CWebserverRequest *req;
	int sock_connect;
	fd_set rfds;
	struct timeval tv;

	pthread_attr_t attr;
	pthread_attr_init(&attr);
	pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);

	signal(SIGCHLD,sig_chld);
	clilen = sizeof(cliaddr);
	while(!STOP) {
		FD_ZERO(&rfds);
		FD_SET(ListenSocket, &rfds);

		tv.tv_sec = 2;
		tv.tv_usec = 0;

		if ( select(ListenSocket + 1, &rfds, NULL, NULL, &tv) <= 0)
			continue;

		if (!FD_ISSET(ListenSocket, &rfds))
			continue;

		memset(&cliaddr, 0, sizeof(cliaddr));
		if ((sock_connect = accept(ListenSocket, (SA *) &cliaddr, &clilen)) == -1)	// accepting requests
			continue;
		//setsockopt(sock_connect, SOL_TCP, TCP_CORK, &t, sizeof(t));

		req = new CWebserverRequest(this);	// create new request
		req->Socket = sock_connect;
		req->Client_Addr = inet_ntoa(cliaddr.sin_addr);

		pthread_create (&req->thread_id, &attr, WebThread, (void *)req);
	}
}

void CWebserver::Stop()
{
	if (ListenSocket != 0) {
		STOP = true;
		close( ListenSocket );
		ListenSocket = 0;
	}
	if (server_thread != 0){
		pthread_join(server_thread,NULL);
		server_thread = 0;
	}
}

CWebserver::CWebserver(void)
{
	CDEBUG::getInstance()->Debug = false;

	server_thread = 0;
	ListenSocket = 0;
	STOP = false;
}

CWebserver::~CWebserver()
{
	Stop();
	Wait();
}

