-- 攻取节目的播放地址
function get_video_url(pid)
	local url = string.format('http://l.smgbb.cn/channelurl.ashx?starttime=0&endtime=0&channelcode=%s', pid)
	local text = kola.wget(url, false)

	if text ~= nil then
		text = kola.pcre('\\[CDATA\\[(.*)\\]\\]></channel>', text)
		return string.sub(text, 1, -2)
	end

	return ""
end

function get_channel(pid)
	print('pid:', pid)
	local ret = {}
	local url = string.format('http://l.smgbb.cn/schedule.ashx?channel=%s', pid)
	print(url)
	local text = kola.wget(url, false)

	if text ~= nil then
		local js = cjson.decode(text)
		for k, v in ipairs(js.schedule) do
			ret[k] = {}
			ret[k].time_string = v.time
			ret[k].time        = tonumber(v.start)
			ret[k].duration    = tonumber(v['end']) - tonumber(v['start'])
			ret[k].title       = v.title
			--print(k, ret[k].time_string, ret[k].duration, ret[k].title)
		end
	end

	return cjson.encode(ret)

end
