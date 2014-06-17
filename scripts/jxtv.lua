-- 获取节目的播放地址
function get_video_url(url)
	local text = kola.wget(url)
	if text then
		text = kola.pcre('html5file:"(.*)"', text)
		return kola.strtrim(text)
		--text = kola.pcre('streamer: "(.*)"', text)
		--return kola.strtrim(text) ..  '/livestream.flv'
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

	return epg
end

-- 获取节目的EPG
function get_channel(url)
	local text = kola.wget(url)
	local ret = {}
	local idx = 1
	for time,title in rex.gmatch(text, '<b>(.*)</b><span class="name">(.*)</span>') do
		ret[idx] = to_epg(time, title)

		if idx > 1 then
			ret[idx-1].duration = os.difftime(ret[idx].time, ret[idx - 1].time)
		end
		idx = idx + 1
	end

	return cjson.encode(ret)
end
