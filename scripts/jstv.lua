function kola_main(url)
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

function get_channel(vid)
	vid = tonumber(vid)
	local url = 'http://newplayerapi.jstv.com/rest/getstation_8.html'
	local ret = {}

	text = kola.wget(url, false)
	if text ~= nil then
		local js = cjson.decode(text)

		for id, ch in ipairs(js.paramz.channels) do
			if ch.id == vid then
				local d = os.date("*t", kola.gettime())

				local len = #ch.guides
				for i, gui in ipairs(ch.guides) do
					t = gui.bctime
					d.hour = tonumber(string.sub(t, 1, string.find(t, ":") - 1))
					d.min  = tonumber(string.sub(t, string.find(t, ":") + 1))
					d.sec  = 0

					k = len - i + 1
					ret[k] = {}
					ret[k].title = gui.name

					ret[k].time_string = gui.bctime
					ret[k].time = os.time(d)
					ret[k].duration = 0
					if k < len then
						ret[k].duration = os.difftime(ret[k+1].time, ret[k].time)
					end
				end

				break
			end
		end
	end

	return cjson.encode(ret)
end
