function kola_main(url, cid)
	local text = kola.wget(url)

	if text == nil then
		return ''
	end
	local ret = {}
	local js = cjson.decode(text)
	local live = js.data.live

	text = kola.wget(live)
	if text ~= nil then
		js = cjson.decode(text)

		if js.msg == 'OK' then
			return js.url
		end
	end

	return ''
end

function get_channel(vid)
	local url = string.format("http://poll.hd.sohu.com/live/stat/menu-segment.json?&sid=%s", vid)

	--print(url)
	local ret = {}
	local text = kola.wget(url)
	if text ~= nil then
		local d = os.date("*t", kola.gettime())
		local js = cjson.decode(text)
		for k,v in ipairs(js.attachment[1].MENU_LIST) do
			t = v.START_TIME
			d.hour=tonumber(string.sub(t, 1, string.find(t, ":") - 1))
			d.min=tonumber(string.sub(t, string.find(t, ":") + 1))
			d.sec= 0
			ret[k] = {}
			ret[k].time_string = v.START_TIME
			ret[k].time = os.time(d)
			ret[k].duration = 0
			ret[k].title = v.NAME
			if k > 1 then
				ret[k-1].duration = os.difftime(ret[k].time, ret[k-1].time)
			end
			--print(k, ret[k].time_string, ret[k].duration, ret[k].title)
		end
	end

	return cjson.encode(ret)
end

