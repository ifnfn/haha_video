#include <stdio.h>

#include "kola.hpp"
#include "json.hpp"

KolaEpg::KolaEpg(Variant epg)
{
	finished = false;
	scInfo = epg;
}

bool KolaEpg::LoadFromText(string text)
{
	bool ret = false;

	json_error_t error;
	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

	if (js) {
		Parser(js);
		this->pool = client->threadPool;
		ret = true;
	}

	json_delete(js);

	return ret;
}

void KolaEpg::Parser(json_t *js)
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
}

bool KolaEpg::GetCurrent(EPG &e)
{
	return Get(e, KolaClient::Instance().GetTime());
}

bool KolaEpg::GetNext(EPG &e)
{
	EPG ok;
	int count;
	bool ret = false;
	time_t t = KolaClient::Instance().GetTime();

	mutex.lock();
	count = (int)epgList.size();

	for (int i=0; i < count; i++) {
		EPG x = epgList.at(i);

		if (x.startTime > t) {
			e = x;
			ret = true;
			break;
		}
	}
	mutex.unlock();

	return ret;
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
			break;
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
	finished = true;
}

void KolaEpg::Update()
{
	if (finished == false && status == Task::StatusInit) {
		Start();
	}
}

bool KolaEpg::UpdateFinish()
{
	Update();
	return status == Task::StatusFinish && finished;
}

void KolaEpg::Clear()
{
	mutex.lock();
	finished = false;
	status = Task::StatusInit;
	epgList.clear();
	Update();
	mutex.unlock();
}

