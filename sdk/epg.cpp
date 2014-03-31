//
//  epg.cpp
//  kolatv
//
//  Created by Silicon on 14-3-31.
//  Copyright (c) 2014年 Silicon. All rights reserved.
//

#include <stdio.h>
#include "kola.hpp"
#include "json.hpp"

KolaEpg::KolaEpg(json_t *js) {
	json_to_variant(js, &scInfo);
}

bool KolaEpg::LoadFromText(string text)
{
	bool ret = false;

	json_error_t error;
	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

	if (js)
		ret = LoadFromJson(js);

	json_delete(js);

	return ret;
}

bool KolaEpg::LoadFromJson(json_t *js)
{
	json_t *v;

	mutex.lock();
	json_array_foreach(js, v) {
		EPG e;
		e.startTime = json_geti(v, "time", 0);
		e.duration = json_geti(v, "duration", 0);
		json_gets(v, "title", e.title);
		json_gets(v, "time_string", e.timeString);

		epgList.push_back(e);
	}
	mutex.unlock();

	return true;
}

bool KolaEpg::GetCurrent(EPG &e)
{
	return Get(e, KolaClient::Instance().GetTime());
}

bool KolaEpg::GetNext(EPG &e)
{
	EPG ok;
	int count;
	time_t t = KolaClient::Instance().GetTime();

	mutex.lock();
	count = (int)epgList.size();

	time_t time = 0xffffffff;
	for (int i=0; i < count; i++) {
		EPG x = epgList.at(i);

		if (x.startTime > t && x.startTime < time) {
			time = x.startTime;
			e = x;
		}
	}
	mutex.unlock();

	return time != 0xffffffff;
}

bool KolaEpg::Get(EPG &e, time_t t)
{
	bool ret = false;
	int count;

	mutex.lock();
	count = (int)epgList.size();

	for (int i = count - 1; i >= 0; i--) {
		EPG x = epgList.at(i);

		if (t >= x.startTime) {
			e = x;
			ret = true;
		}
	}
	mutex.unlock();

	return ret;
}

void KolaEpg::Run(void)
{
	string text = scInfo.GetString();

	if (not text.empty()) {
		LoadFromText(text);
	}
}

void KolaEpg::Update()
{
	if (status != Task::StatusDownloading) {
		mutex.lock();
		Clear();
		mutex.unlock();
		status = Task::StatusInit;
		Start();
	}
}

bool KolaEpg::UpdateFinish()
{
	return status == Task::StatusFinish;
}

void KolaEpg::Clear()
{
	epgList.clear();
}

