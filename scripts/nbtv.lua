function get_video_url(url, id, referer)
	--print(url, id, referer)
	local text = kola.wget(url, false)

	if text and text ~= "TVie Exception: No streams." then
		local data_obj = cjson.decode(text)
		if data_obj then
			return string.format('http://zb.nbtv.cn:8134/hls-live/livepkgr/_definst_/liveevent/%s_1.m3u8', data_obj.channel_name)
		end
	end

	return ''
end
