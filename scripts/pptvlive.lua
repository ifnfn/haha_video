function kola_main(id)
	if id then
		return string.format('http://web-play.pptv.com/web-m3u8-%s.m3u8?type=m3u8.web.pad&playback=0', id)
	end

	return ''
end


function get_channel(vid)
	local time = kola.gettime()
	local url = string.format('http://live.pptv.com/api/tv_menu?cb=kola&date=%s&id=%s&canBack=0', 
			os.date("%Y-%m-%d", time),
			vid)

	print(url)
	local ret = {}
	local text = kola.wget(url, false)
	if text ~= nil then
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
			print(ret[i].time, ret[i].time_string, ret[i].title)
			if i > 1 then
				--print(ret[i].title, ret[i-1].title)
				ret[i-1].duration = os.difftime(ret[i].time, ret[i-1].time)
			end
			i = i + 1
		end
	end
	return cjson.encode(ret)
end
