local function check_m3u8(url)
	if string.find(url, "m3u8") then
		local text = ''
		c = cURL.easy_init()
		c:setopt_useragent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36")
		-- setup url
		c:setopt_url(url)
		-- perform, invokes callbacks
		c:perform({writefunction = function(str) text = text .. str end})

		--local text = kola.wget(url, false)
		if text and string.find(text, "EXTM3U") then
			print(url, " ", text)
			return url
		end
	end

	return nil
end

-- 攻取节目的播放地址
function get_video_url(vid, aid)
	local url = string.format("http://vdn.live.cntv.cn/api2/liveHtml5.do?channel=pa://cctv_p2p_hd%s&client=html5", vid)
	local text = kola.wget(url, false)
	--print(text)
	local video_url = ''
	if text then
		local hls_vod_url = ''

		text = kola.pcre("var html5VideoData = '(.*)';", text)
		--print(text)
		local js = cjson.decode(text)

		-- 如果有 hls
		if js.hls_url then
			if check_m3u8(js.hls_url.hls1) then
				return js.hls_url.hls1
			end
			if check_m3u8(js.hls_url.hls2) then
				return js.hls_url.hls2
			end
			if check_m3u8(js.hls_url.hls3) then
				return js.hls_url.hls3
			end
		end

		-- 如果有 hds
		if js['hds_url'] then
			video_url = js['hds_url']['hds2']
			if string.find(video_url, 'http://') and string.find(video_url, 'channel') then
				return video_url
			end
		end
	end

	return ''
end

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

-- 获取节目的EPG
function get_channel(vid)
	local ret = {}
	local url = string.format('http://tv.cntv.cn/index.php?action=zhibo-jiemu2&channel=%s', vid)
	local text = kola.wget(url, false)
	local idx = 1

	for time,title in rex.gmatch(text, '<span class="sp_1">(.*?)</span>[\\s\\S]*?&nbsp;(.*?)[</a>|</li>]') do
		ret[idx] = to_epg(time, title)

		if idx > 1 then
			ret[idx-1].duration = os.difftime(ret[idx].time, ret[idx - 1].time)
		end
		idx = idx + 1
	end

	return cjson.encode(ret)
end
