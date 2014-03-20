-- 攻取节目的播放地址
function get_video_url(url)
	local u = string.gsub(url, "tv.html", "api.html")

	local url = string.format("%s&st=99", u)

	u = kola.wget(url)

	if u ~= nil then
		return kola.urldecode(u)
	end

	return ""
end

-- 获取节目的EPG
function get_channel(url)
	-- 无EPG
	return "{}"
end
