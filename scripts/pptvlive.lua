-- 攻取节目的播放地址
function get_video_url(id)
	if id then
		return string.format('http://web-play.pptv.com/web-m3u8-%s.m3u8?type=m3u8.web.pad&playback=0', id)
	end

	return ''
end

-- 获取节目的EPG
function get_channel(vid)
	local time = kola.gettime()
	local url = string.format('http://live.pptv.com/api/tv_menu?cb=kola&date=%s&id=%s&canBack=0', 
			os.date("%Y-%m-%d", time),
			vid)

	local ret = {}
	local text = kola.wget(url, false)
	if text then
		text = rex.match(text, 'kola\\((.*)\\)')

		local js = cjson.decode(text)
		local i = 1
		local d = os.date("*t", time)
		for time,title in rex.gmatch(js.html, "</i>(\\w*:\\w*)</span></a>\\s*.*?title\\s*=\\s*['\"](.*?)['\"]") do
			d.hour = tonumber(string.sub(time, 1, string.find(time, ":") - 1))
			d.min  = tonumber(string.sub(time, string.find(time, ":") + 1))

			ret[i] = {}
			ret[i].time_string = time
			ret[i].time        = os.time(d)
			ret[i].title       = title
			ret[i].duration    = 0
			if i > 1 then
				ret[i-1].duration = os.difftime(ret[i].time, ret[i-1].time)
			end
			i = i + 1
		end
	end
	return cjson.encode(ret)
end
