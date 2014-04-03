-- 攻取节目的播放地址
function get_video_url(url)
	url = 'http://www.wasu.cn/Api/' .. string.gsub(url, 'show', 'getLiveInfoByid')

	local text = kola.wget(url, false)
	text = kola.pcre("<video>(.*)</video>", text)
	return kola.strtrim(text)
end

-- 获取节目的EPG
function get_channel(vid, id)

	return ''
end
