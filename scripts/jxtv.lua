-- 攻取节目的播放地址
function get_video_url(url)
	local text = kola.wget(url, false)
	if text ~= nil then
		text = kola.pcre('streamer: "(.*)"', text)
		return string.sub(text, 1, -2) ..  '/livestream.flv'
	end

	return ""
end

function get_channel(vid)
	return ""
end
