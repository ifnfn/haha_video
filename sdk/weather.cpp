#include "kola.hpp"
#include "http.hpp"
#include "json.hpp"
#include "script.hpp"

KolaWeather::~KolaWeather()
{
	Clear();
}

void KolaWeather::Clear()
{
	size_t count = weatherList.size();
	
	for (int i=0; i < count; i++)
		delete weatherList[i];
	
	weatherList.clear();
}

void KolaWeather::Get(string name, StringList &value)
{
	string url = "city?name=" + name;

	json_t *js = json_loadurl(url.c_str());

	if (js) {
		json_t *v;
		json_array_foreach(js, v) {
			const char *n = json_gets(v, "name", "");
			value.Add(n);
		}

		json_decref(js);
	}
}

void KolaWeather::GetProvince(StringList &value)
{
	Get("", value);
}

void KolaWeather::GetCity(string province, StringList &city)
{
	Get(province, city);
}

void KolaWeather::GetCounty(string province, string city, StringList &county)
{
	Get(province + "-" + city, county);
}

void KolaWeather::SetArea(string area)
{
	this->Area = area;
}

void KolaWeather::SetArea(string province, string area, string county)
{
	if (not province.empty()) {
		this->Area = province;

		if (not area.empty()) {
			this->Area += "-" + area;

			if (not county.empty())
				this->Area += "-" + county;
		}
	}
}

bool KolaWeather::ParserWeatherData(WeatherData& data, json_t *js)
{
	data.picture       = json_gets(js, "picture",       "");
	data.code          = json_gets(js, "code",          "");
	data.weather       = json_gets(js, "weather",       "");
	data.temp          = json_gets(js, "temp",          "");
	data.windDirection = json_gets(js, "windDirection", "");
	data.windPower     = json_gets(js, "windPower",     "");

	return true;
}

void KolaWeather::Run(void)
{
	LuaScript &lua = LuaScript::Instance();
	vector<string> args;

	args.push_back(Area);
	string text = lua.RunScript(args, "weather");

	if (not text.empty()) {
		json_error_t error;

		json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
		
		if (js == NULL)
			return;

		mutex.lock();
		Clear();

		json_t *weather = json_geto(js, "weather");
		if (weather) {
			json_t *info;
			json_array_foreach(weather, info) {
				Weather *w = new Weather();
				
				w->date = json_gets(info, "date", "");
				
				json_t *v = json_geto(info, "day");
				if (v)
					ParserWeatherData(w->day, v);
				v = json_geto(info, "night");
				if (v)
					ParserWeatherData(w->night, v);

				this->weatherList.push_back(w);
			}
		}

		PM25 = json_gets(js, "pm25", "");
		mutex.unlock();

		json_delete(js);
	}
}

bool KolaWeather::UpdateFinish()
{
	return status == Task::StatusFinish;
}

void KolaWeather::Update()
{
	if (status != Task::StatusDownloading) {
		mutex.lock();
		Clear();
		mutex.unlock();
		status = Task::StatusInit;
		Start();
	}
}

Weather *KolaWeather::Today()
{
	Weather *w = NULL;
	mutex.lock();
	if (weatherList.size() > 0)
		w = weatherList[0];
	mutex.unlock();
	return w;
}

Weather *KolaWeather::Tomorrow()
{
	Weather *w = NULL;
	mutex.lock();
	if (weatherList.size() > 1)
		w = weatherList[1];
	
	mutex.unlock();
	return w;
}

