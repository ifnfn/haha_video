//
//  common.cpp
//  kolatv
//
//  Created by Silicon on 14-3-27.
//  Copyright (c) 2014年 Silicon. All rights reserved.
//

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <zlib.h>
#include <openssl/md5.h>
#include <signal.h>
#include <arpa/inet.h>
#include <netdb.h>

#include "common.hpp"

typedef unsigned char BYTE;

inline static unsigned char toHex(unsigned char x) {
	return x > 9 ? x + 55 : x + 48;
}

inline BYTE fromHex(const BYTE &x)
{
        return isdigit(x) ? x-'0' : x-'A'+10;
}

string UrlEncode(const string & sIn)
{
	string sOut;

	for(size_t i=0; i < sIn.size(); ++i) {
		unsigned char buf[4];
		memset(buf, 0, 4);
		if(isalnum((unsigned char)sIn[i]))
			buf[0] = sIn[i];
		else if(isspace((unsigned char)sIn[i]))
			buf[0] = '+';
		else {
			buf[0] = '%';
			buf[1] = toHex((unsigned char)sIn[i] >> 4);
			buf[2] = toHex((unsigned char)sIn[i] % 16);
		}
		sOut += (char *)buf;
	}

	return sOut;
}

string UrlDecode(const string &sIn)
{
	string sOut;

	for( size_t ix = 0; ix < sIn.size(); ix++ ) {
		BYTE ch = 0;
		if(sIn[ix]=='%') {
			ch = (fromHex(sIn[ix+1])<<4);
			ch |= fromHex(sIn[ix+2]);
			ix += 2;
		}
		else if(sIn[ix] == '+')
			ch = ' ';
		else
			ch = sIn[ix];

		sOut += (char)ch;
	}

	return sOut;
}

/**
 * 功能:获取芯片的CPUID。
 * 参数:
 *    pbyCPUID:       芯片提供的CPUID，最多128个字节
 *    pLen:           输出CPUID的实际长度
 * 返回值:
 *    0:              获取CPUID成功
 *    其他值: 获取CPUID失败
 */
static bool GetCPUID(string &CPUID, ssize_t len)
{
	int fd;
	uint8_t *data;

	fd = open("/proc/gx_otp", O_RDWR);
	if (fd < 0){
		//printf("open otp err!!!\n");
		return false;
	}
	data =(uint8_t*)malloc(len);
	memset(data, 0 ,len);
	len = read(fd, data, len);
	close(fd);

	for (int i = 0; i < len; i++) {
		char buffer[8];
		sprintf(buffer, "%02X", data[i]);
		CPUID += buffer;
	}
	free(data);

	return true;
}

string GetChipKey(void)
{
	static string CPUID;
	if (CPUID.empty()) {
		if (GetCPUID(CPUID, 8) == false)
			CPUID = "000002";
	}

	return CPUID;
}

string MD5(const char *data, size_t size)
{
	MD5_CTX ctx;
	unsigned char md[16];
	char buf[33]={'\0'};

	MD5_Init(&ctx);
	MD5_Update(&ctx, data, size);
	MD5_Final(md,&ctx);

	for(int i=0; i<16; i++ ){
		sprintf(buf+ i * 2,"%02X", md[i]);
	}

	return string(buf);
}

string GetIP(const char *hostp)
{
	string ip;
	struct hostent *host = gethostbyname(hostp);

	if (host) {
		char str[64];
		const char *p = inet_ntop(host->h_addrtype, host->h_addr, str, sizeof(str));
		if (p)
			ip = p;
		//freehostent(host);
	}

	return ip;
}

void split(const string& src, const string& separator, vector<string>& dest)
{
	string str = src;
	string substring;
	string::size_type start = 0, index;

	do {
		index = str.find_first_of(separator,start);
		if (index != string::npos) {
			substring = str.substr(start,index-start);
			dest.push_back(substring);
			start = str.find_first_not_of(separator,index);
			if (start == string::npos) return;
		}
	}while(index != string::npos);

	//the last token
	substring = str.substr(start);
	dest.push_back(substring);
}

string stringlink(string key, string value)
{
	return "\""  + key + "\" : \"" + value + "\"";
}

string UrlLink(string a, string b)
{
	if (!b.empty() && b.at(0) != '/')
		return a + "/" + b;
	else
		return a + b;
}


