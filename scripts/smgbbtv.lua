-- 攻取节目的播放地址
function get_video_url(pid)
	local url = string.format('http://l.smgbb.cn/channelurl.ashx?starttime=0&endtime=0&channelcode=%s', pid)
	local text = kola.wget(url, false)

	if text then
		text = kola.pcre('\\[CDATA\\[(.*)\\]\\]></channel>', text)
		return kola.strtrim(text)
	end

	return ""
end
