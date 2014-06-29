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
