function kola_main(city)
	local url = "http://weather.hao.360.cn/api_weather_info.php?app=hao360"

	local text = kola.wget(url, false)

	local ret = {}
	if text ~= nil then
		text = kola.pcre("callback\\((.*)\\);", text)
		local js = cjson.decode(text)

		if js == nil then
			return {}
		end

		ret.weather = {}
		for i, w in pairs(js.weather) do
			info = {}
			info.date = w.date

			info.day = {}
			info.day.picture       = string.format("http://p2.qhimg.com/d/_hao360/weather/big/%s.png",  w.info.day[1])
			info.day.weather       = w.info.day[2]
			info.day.temp          = w.info.day[3]
			info.day.windDirection = w.info.day[4]
			info.day.windPower     = w.info.day[5]

			info.night = {}
			info.night.picture       = string.format("http://p2.qhimg.com/d/_hao360/weather/big/%s.png",  w.info.night[1])
			info.night.weather       = w.info.night[2]
			info.night.temp          = w.info.night[3]
			info.night.windDirection = w.info.night[4]
			info.night.windPower     = w.info.night[5]

			ret.weather[i] = info
		end

		ret.pm25 = js.pm25.pm25[1]
	end

	return cjson.encode(ret)
end
