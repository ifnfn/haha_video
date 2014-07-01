#include <stdio.h>

#include "kola.hpp"
#include "json.hpp"

KolaEpg::KolaEpg() {
	finished = false;
	pool = client->threadPool;
}

KolaEpg::KolaEpg(Variant epg)
{
	finished = false;
	scInfo = epg;

	pool = client->threadPool;
}

bool KolaEpg::LoadFromText(string text)
{
	bool ret = false;

	json_error_t error;
	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

	if (js) {
		Parser(js);
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

void KolaEpg::Set(Variant epg) {
	scInfo = epg;
	mutex.lock();
	finished = false;
	epgList.clear();
	status = Task::StatusInit;
	mutex.unlock();
	Update();
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

bool epg_compr(EPG &e1, EPG &e2)
{
	return e1.startTime < e2.startTime;
}

void KolaEpg::Sort()
{
	sort(epgList.begin(), epgList.end(), epg_compr);
}

void KolaEpg::Run(void)
{
	string text = scInfo.GetString();

	if (not text.empty()) {
		mutex.lock();
		epgList.clear();
		mutex.unlock();
		LoadFromText(text);
		mutex.lock();
		Sort();
		mutex.unlock();
	}
	finished = true;
}

void KolaEpg::Update()
{
	mutex.lock();
	if (finished == false && status == Task::StatusInit && not scInfo.Empty()) {
		Start();
	}
	mutex.unlock();
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
	mutex.unlock();
}

size_t KolaEpg::Count()
{
	mutex.lock();
	size_t size = epgList.size();
	mutex.unlock();

	return size;
}

bool KolaEpg::Get(int index, EPG &epg)
{
	bool ret = false;
	mutex.lock();
	if (index >= 0 && index < epgList.size()) {
		epg = epgList.at(index);
		ret = true;
	}
	mutex.unlock();

	return ret;
}


