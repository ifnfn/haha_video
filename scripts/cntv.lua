local function check_m3u8(url)
	if string.find(url, "m3u8") then
		local text = kola.wget(url, false)
		if text and string.find(text, "EXTM3U") then
			return url
		end
	end

	return nil
end

-- 攻取节目的播放地址
function get_video_url(vid, aid)
	local url = string.format("http://vdn.live.cntv.cn/api2/liveHtml5.do?channel=pa://cctv_p2p_hd%s&client=html5", vid)
	print(url)
	local text = kola.wget(url, false)
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
			if string.find(video_url, "http://") and string.find(video_url, "channel") then
				return video_url
			end
		end
	end

	return ''
end

function get_channel(vid)
	local ret = {}
	local url = string.format('http://tv.cntv.cn/index.php?action=zhibo-jiemu2&channel=%s', vid)
	local text = kola.wget(url, false)
	local d = os.date("*t", kola.gettime())
	local idx = 1

	for time,title in rex.gmatch(text, '<span class="sp_1">(.*?)</span>[\\s\\S]*?&nbsp;(.*?)[</a>|</li>]') do
		d.hour = tonumber(string.sub(time, 1, string.find(time, ":") - 1))
		d.min  = tonumber(string.sub(time,    string.find(time, ":") + 1))
		d.sec  = 0

		ret[idx] = {}
		ret[idx].title       = string.gsub(title, "_$", "") -- strip, trim, 去头尾空格
		ret[idx].time_string = time
		ret[idx].time        = os.time(d)
		ret[idx].duration = 0
		if idx > 1 then
			ret[idx].duration = os.difftime(ret[idx].time, ret[idx - 1].time)
		end
		idx = idx + 1
	end

	return cjson.encode(ret)
end
