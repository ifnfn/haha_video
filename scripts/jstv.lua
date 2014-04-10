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

local function to_epg(time, title)
	local function strtotime(t)
		local d = os.date("*t", kola.gettime())

		d.sec  = 0
		if kola.strsplit then
			d.hour, d.min = kola.strsplit(":", time, 2)
			d.hour = tonumber(d.hour)
			d.min  = tonumber(d.min)
		else
			d.hour = tonumber(string.sub(time, 1, string.find(time, ":") - 1))
			d.min  = tonumber(string.sub(time,    string.find(time, ":") + 1))
		end

		return os.time(d)
	end

	local epg = {}

	epg.time_string = time
	epg.title       = string.gsub(title, "_$", "") -- strip, trim, 去头尾空格
	epg.time        = strtotime(time)
	epg.duration    = 0

	return epg
end

-- 获取节目的EPG
function get_channel(vid)
	vid = tonumber(vid)
	local url = 'http://newplayerapi.jstv.com/rest/getstation_8.html'
	local ret = {}

	text = kola.wget(url, false)
	if text then
		local js = cjson.decode(text)

		for id, ch in ipairs(js.paramz.channels) do
			if ch.id == vid then
				local len = #ch.guides
				for i, gui in ipairs(ch.guides) do
					k = len - i + 1
					ret[k] = to_epg(gui.bctime, gui.name)
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
