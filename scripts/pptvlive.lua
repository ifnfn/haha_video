-- 攻取节目的播放地址
function get_video_url(id)
	print(url)
	if id then
		return string.format('http://web-play.pptv.com/web-m3u8-%s.m3u8?type=m3u8.web.pad&playback=0', id)
	end

	return ''
end
