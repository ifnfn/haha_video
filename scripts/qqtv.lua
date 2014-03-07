-- 攻取节目的播放地址
function get_video_url(url)
	local text = kola.wget(url, false)

	if text ~= nil then
		text = kola.pcre('location url="(.*?)"', text)
		return string.sub(text, 1, -2)
	end

	return ""
end

function get_channel(vid)
	local url = string.format('http://v.qq.com/live/tv/%s.html', vid)
	local text = kola.wget(url, false)

	local ret = {}
	if text ~= nil then
		local i = 1
		local d = os.date("*t", time)
		for x in rex.gmatch(text, '(<div class=".*sta_unlive j_wanthover">[\\s\\S]*?</div>)') do
			for time, title in rex.gmatch(x, '<span class="time">(.*)</span>\\s*<span title="(.*)" class') do
				print(time, title)
				d.hour = tonumber(string.sub(time, 1, string.find(time, ":") - 1))
				d.min  = tonumber(string.sub(time, string.find(time, ":") + 1))

				ret[i] = {}
				ret[i].time_string = time
				ret[i].time        = os.time(d)
				ret[i].title       = title
				if i > 1 then
					ret[i-1].duration = os.difftime(ret[i].time, ret[i-1].time)
				end
				i = i + 1
			end
		end
	end

	return cjson.encode(ret)
end
