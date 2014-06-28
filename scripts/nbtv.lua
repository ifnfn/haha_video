function get_video_url(url, id, referer)
	print(url, id, referer)
	local text = kola.wget(url, false)

	if text and text ~= "TVie Exception: No streams." then
		local data_obj = cjson.decode(text)
		if data_obj then
			return string.format('http://zb.nbtv.cn:8134/hls-live/livepkgr/_definst_/liveevent/%s_1.m3u8', data_obj.channel_name)
		end
	end

	return ''
end

function get_channel(vid, id)
	local url = string.format("%s/0/%d", vid, kola.gettime())

	local ret = {}
	text = kola.wget(url, false)
	if text and text ~= "TVie Exception: No streams." then
		local d = os.date("*t", kola.gettime())
		local prev_d = d
		local js = cjson.decode(text)
		for k,v in ipairs(js.result[1]) do
			ret[k] = {}
			s = tonumber(v.start_time)
			ret[k].time_string = os.date("%H:%M", s)
			ret[k].time        = s
			ret[k].duration    = tonumber(v.end_time) - s
			ret[k].title       = v.name
		end
	end

	return cjson.encode(ret)
end
