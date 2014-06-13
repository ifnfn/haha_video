local function to_epg(time, title)
	local function strtotime(t)
		local d = os.date("*t", kola.gettime())

		d.hour, d.min = kola.strsplit(":", time, 2)
		d.hour = tonumber(d.hour)
		d.min  = tonumber(d.min)
		d.sec  = 0

		return os.time(d)
	end

	local epg = {}

	epg.time_string = time
	epg.title       = string.gsub(title, "_$", "") -- strip, trim, 去头尾空格
	epg.time        = strtotime(time)
	epg.duration    = 0

	return epg
end

-- CNTV 中央台的 EPG
function get_channel_cntv(albumName)
	local id = string.match(albumName, ".*-(%d+) ")
	local vid = string.format("cctv%s", id)

	local ret = {}
	local url = string.format('http://tv.cntv.cn/index.php?action=epg-list&date=%s&channel=%s', os.date("%Y-%m-%d", kola.gettime()), vid)
	local text = kola.wget(url, false)
	local idx = 1

	for time, title in rex.gmatch(text, '<a target="_blank" href=".*" class="p_name_a">(.*) (.*?)</a>') do
		-- print(time, title)
		ret[idx] = to_epg(time, title)

		if idx > 1 then
			ret[idx - 1].duration = os.difftime(ret[idx].time, ret[idx - 1].time)
		end
		idx = idx + 1
	end

	for time, title in rex.gmatch(text, '<a class="p_name" href="###">(.*) (.*?)</a>') do
		-- print(time, title)
		ret[idx] = to_epg(time, title)

		if idx > 1 then
			ret[idx - 1].duration = os.difftime(ret[idx].time, ret[idx - 1].time)
		end
		idx = idx + 1
	end
	return cjson.encode(ret)
end
