-- 攻取节目的播放地址
function get_video_url(url, id)
	local text = kola.wget(url, false)
	if text ~= nil then
		text = kola.pcre("file: '(.*)'", text)
		return string.sub(text, 1, -2) .. id
	end

	return ""
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
	local ret = {}
	local url = "http://www.dhtv.cn/api/programs/?ac=get&_channel=" .. vid 
	local text = kola.wget(url, false)

	if text == nil then
		return '{}'
	end
	text = string.sub(text, 2, #text - 1)
	if text == nil then
		return '{}'
	end
	text = string.sub(text, 2, #text - 1)

	local js = cjson.decode(text)
	for k,v in ipairs(js.data) do
		ret[k] = to_epg(v.start, v.name)
		if k > 1 then
			ret[k-1].duration = os.difftime(ret[k].time, ret[k-1].time)
		end
	end

	return cjson.encode(ret)
end
