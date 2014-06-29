-- 攻取节目的播放地址
function get_video_url(url)
	--local url = string.format("http://live.gslb.letv.com/gslb?stream_id=%s&ext=m3u8&sign=live_tv&format=1", url)
	local text = kola.wget(url, false)
	print(url)

	if text and string.find(text, "<html>") then
		local js = cjson.decode(text)
		if js ~= nil then
			return js.location
		end
	end

	return ''
end
