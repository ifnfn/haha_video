-- 攻取节目的播放地址
function get_video_url(url)
	--local url = string.format("http://live.gslb.letv.com/gslb?stream_id=%s&ext=m3u8&sign=live_tv&format=1", url)
	local text = kola.wget(url, false)
	print(url)

	if text ~= nil and string.find(text, "<html>") ~= nil then
		local js = cjson.decode(text)
		if js ~= nil then
			return js.location
		end
	end

	return ''
end

local function to_epg(time, title)
	local epg = {}
	local d = os.date("*t", kola.gettime())
	d.hour = tonumber(string.sub(time, 1, string.find(time, ":") - 1))
	d.min  = tonumber(string.sub(time,    string.find(time, ":") + 1))
	d.sec  = 0

	epg.time_string = time
	epg.title       = string.gsub(title, "_$", "") -- strip, trim, 去头尾空格
	epg.time        = os.time(d)
	epg.duration    = 0

	--print(epg.time_string, epg.duration, epg.title)
	return epg
end

-- 获取节目的EPG
function get_channel(vid)
	local time = kola.gettime()
	local url = string.format("http://st.live.letv.com/live/playlist/%s/%s.json?_=%d", os.date("%Y%m%d", time), vid, time)

	local ret = {}
	text = kola.wget(url, false)
	if text ~= nil then
		local js = cjson.decode(text)
		for k,v in ipairs(js.content) do
			--print(k,v.playtime, v.duration, v.title)
			ret[k] = to_epg(v.playtime, v.title)
			ret[k].duration = v.duration
		end
	end

	return cjson.encode(ret)
end
