
-- 获取节目的播放地址
function get_video_url(url)
	local text = kola.wget(url, false)
	if text then
		text = kola.pcre("var playurl = '(.*)';", text)
		return kola.strtrim(text)
	end

	return ""
end
