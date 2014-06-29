-- 攻取节目的播放地址
function get_video_url(url)
	if url ~= '' then
		return url
	end
	local text = kola.wget('http://newplayerapi.jstv.com/rest/getplayer_1.html')
	if text == nil then
		return ''
	end

	local js = cjson.decode(text)

	for _, ch in ipairs(js.paramz.stations) do
--            "auto": "/live/jsws?fmt=x264_0k_flv&sora=15",
--            "supor": "/live/jsws?fmt=x264_700k_flv&size=720x576",
--            "high": "/live/jsws?fmt=x264_700k_flv&size=720x576",
--            "fluent": "/live/jsws?fmt=x264_400k_flv&size=720x576",
--            "logo": "/Attachs/Channel/43/2932868ce4104e74bd9c4108f60d2e96.png "
	end

	return ''
end
