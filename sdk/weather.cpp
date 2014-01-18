//
//  weather.cpp
//  kolatv
//
//  Created by Silicon on 14-1-18.
//  Copyright (c) 2014年 Silicon. All rights reserved.
//

#include "kola.hpp"
#include "http.hpp"
#include "json.hpp"
#include "script.hpp"


void KolaWeather::Clear()
{
	size_t count = weatherList.size();
	
	for (int i=0; i < count; i++)
		delete weatherList[i];
	
	weatherList.clear();
}

void KolaWeather::Run(void)
{
	LuaScript &lua = LuaScript::Instance();
	vector<string> args;
	args.push_back("");
	
	string text = lua.RunScript(args, "weather");

	printf("%s\n", text.c_str());
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
				if (v) {
					w->day.picture       = json_gets(v, "picture", "");
					w->day.weather       = json_gets(v, "weather", "");
					w->day.temp          = json_gets(v, "temp", ""); 
					w->day.windDirection = json_gets(v, "windDirection", "");
					w->day.windPower     = json_gets(v, "windPower", ""); 
				}
				v = json_geto(info, "night");
				if (v) {
					w->day.picture       = json_gets(v, "picture", "");
					w->night.weather       = json_gets(v, "weather", "");
					w->night.temp          = json_gets(v, "temp", "");
					w->night.windDirection = json_gets(v, "windDirection", "");
					w->night.windPower     = json_gets(v, "windPower", "");
				}
			
				this->weatherList.push_back(w);
			}
		}
		
		PM25 = json_gets(js, "pm25", "");
		mutex.unlock();

		json_delete(js);
	}
}

void KolaWeather::Update() {
	Wait();
	mutex.lock();
	Clear();
	mutex.unlock();
	Start();
}

Weather *KolaWeather::Today() {
	Weather *w = NULL;
	mutex.lock();
	if (weatherList.size() > 0)
		w = weatherList[0];
	mutex.unlock();
	return w;
}
Weather *KolaWeather::Tomorrow() {
	Weather *w = NULL;
	mutex.lock();
	if (weatherList.size() > 1)
		w = weatherList[1];
	
	mutex.unlock();
	return w;
}

