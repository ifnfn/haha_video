local function check_m3u8(url)
	url = string.gsub(url, "m3u8 ?", "m3u8?")
	url = string.gsub(url, ":8000:8000", ":8000")

	if string.find(url, "m3u8") and string.len(url)>= 15 and string.find(url, "dianpian.mp4") == nil and string.find(url, "cntv.cloudcdn.net") == nil then
		local text = ''
		c = cURL.easy_init()
		c:setopt_useragent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36")
		-- setup url
		c:setopt_url(url)
		-- perform, invokes callbacks
		c:perform({writefunction = function(str) text = text .. str end})

		--local text = kola.wget(url, false)
		if text and string.find(text, "EXTM3U") then
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

		if not js then
			return ''
		end
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

function get_video_url2( vid, aid )
	local url = string.format("http://vdn.live.cntv.cn/api2/live.do?client=iosapp&channel=pa://cctv_p2p_hd%s", vid)
	local text = kola.wget(url, false)

	local video_url = ''
	if text then
		local hls_vod_url = ''
		local js = cjson.decode(text)

		if not js then
			return ''
		end
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
end
