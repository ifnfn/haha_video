-- 攻取节目的播放地址
function get_video_url(url, id)
	local text = kola.wget(url, false)
	if text then
		text = kola.pcre("file: '(.*)'", text)
		return kola.strtrim(text) .. id
	end

	return ""
end

