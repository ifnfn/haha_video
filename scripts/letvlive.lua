function kola_main(url)
	--local url = string.format("http://live.gslb.letv.com/gslb?stream_id=%s&ext=m3u8&sign=live_tv&format=1", url)
	--print(url)
	text = kola.wget(url)
	if text ~= nil then
		local js = cjson.decode(text)
		if js ~= nil then
			return js.location
		end
	end

	return ""
end

function get_channel(vid)
	local time = kola.gettime()
	local d = os.date("%Y%m%d", time)
	local url = string.format("http://st.live.letv.com/live/playlist/%s/%s.json?_=%d", d, vid, time)
	d = os.date("*t", time)

	local ret = {}
	text = kola.wget(url)
	if text ~= nil then
		local js = cjson.decode(text)
		for k,v in ipairs(js.content) do
			--print(k,v.playtime, v.duration, v.title)
			ret[k] = {}
			t = v.playtime
			d.hour=tonumber(string.sub(t, 1, string.find(t, ":") - 1))
			d.min=tonumber(string.sub(t, string.find(t, ":") + 1))
			ret[k].time_string = v.playtime
			ret[k].time = os.time(d)
			ret[k].duration = v.duration
			ret[k].title = v.title
		end
	end

	return cjson.encode(ret)
end