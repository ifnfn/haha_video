-- 攻取节目的播放地址
function get_video_url(url, cid)
	local text = kola.wget(url, false)

	if text == nil then
		return ''
	end
	local ret = {}
	local js = cjson.decode(text)
	local live = js.data.live

	text = kola.wget(live, false)
	if text ~= nil then
		js = cjson.decode(text)

		if js.msg == 'OK' then
			return js.url
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
	local url = string.format("http://poll.hd.sohu.com/live/stat/menu-segment.json?&sid=%s", vid)

	--print(url)
	local ret = {}
	local text = kola.wget(url, false)
	if text ~= nil then
		local js = cjson.decode(text)
		for k,v in ipairs(js.attachment[1].MENU_LIST) do
			ret[k] = to_epg(v.START_TIME, v.NAME)
			if k > 1 then
				ret[k-1].duration = os.difftime(ret[k].time, ret[k-1].time)
			end
			--print(k, ret[k].time_string, ret[k].duration, ret[k].title)
		end
	end

	return cjson.encode(ret)
end

