function kola_main(city)
	local url = "http://weather.hao.360.cn/api_weather_info.php?app=hao360"

	if city ~= nil and city ~= '' then
		url = kola.getserver() .. "/city?cid=1&name=" .. city
		local areaCode = kola.wget(url)

		if areaCode ~= nil and areaCode ~= '' then
			url = string.format("http://weather.hao.360.cn/api_weather_info.php?app=hao360&city_code=%s", areaCode)
		end
	end
	--print(url)
	local text = kola.wget(url, false)

	local ret = {}
	if text ~= nil then
		text = kola.pcre("callback\\((.*)\\);", text)
		local js = cjson.decode(text)

		if js == nil then
			return {}
		end

		ret.area = ''
		city = ''
		for k,v in pairs(js.area) do
			if v[1] ~= city then
				ret.area = ret.area .. v[1]
				city = v[1]
			end
		end

		ret.weather = {}
		for i, w in pairs(js.weather) do
			info = {}
			info.date = w.date

			info.day = {}
			info.day.picture       = string.format("http://p2.qhimg.com/d/_hao360/weather/big/%s.png",  w.info.day[1])
			info.day.code          = w.info.day[1]
			info.day.weather       = w.info.day[2]
			info.day.temp          = w.info.day[3]
			info.day.windDirection = w.info.day[4]
			info.day.windPower     = w.info.day[5]

			info.night = {}
			info.night.picture       = string.format("http://p2.qhimg.com/d/_hao360/weather/big/%s.png",  w.info.night[1])
			info.night.code          = w.info.night[1]
			info.night.weather       = w.info.night[2]
			info.night.temp          = w.info.night[3]
			info.night.windDirection = w.info.night[4]
			info.night.windPower     = w.info.night[5]

			ret.weather[i] = info
		end
		if js.pm25 and js.pm25.pm25 then
			ret.pm25 = tostring(js.pm25.pm25[1])
		end
	end

	--print(cjson.encode(ret))
	return cjson.encode(ret)
end
