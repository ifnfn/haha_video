local function isnan(x) return x ~= x end

local function find(var, tag, key, value)
	-- check input:
	if type(var)~="table" then return end
	if type(tag)=="string" and #tag==0 then tag=nil end
	if type(key)~="string" or #key==0 then key=nil end
	if type(value)=="string" and #value==0 then value=nil end
	-- compare this table:
	if tag~=nil then
		if var[0]==tag and ( value == nil or var[key]==value ) then
			setmetatable(var,{__index=xml, __tostring=xml.str})
			return var
		end
	else
		if value == nil or var[key]==value then
			setmetatable(var,{__index=xml, __tostring=xml.str})
			return var
		end
	end
	-- recursively parse subtags:
	for k,v in ipairs(var) do
		if type(v)=="table" then
			local ret = find(v, tag, key,value)
			if ret ~= nil then return ret end
		end
	end
end

local share = cURL.share_init()
share:setopt_share("COOKIE")
share:setopt_share("DNS")

local function curl_init(url, user_agent, referer)
	local c = cURL.easy_init()
	c:setopt_share(share)

	if user_agent == nil then
		user_agent = "Mozilla/5.0; GGwlPlayer/QQ243944493; Gecko/20100115 Firefox/3.6"
	end

	--if referer == nil then referer = url end

	--c:setopt_verbose(1)
	c:setopt_useragent(user_agent)
	if referer then
		c:setopt_referer(referer)
	end
	c:setopt_url(url)

	return c
end

local function curl_get(url, user_agent, referer)
	if url == nil then
		return nil
	end

	if string.find(url, "http://") == nil then
		url = kola.geturl(url)
	end
	local text = ''

	if kola.wget2xxx then --  wget2 有问题，暂时不采用
		return kola.wget2(url, {
			'User-Agent: ' .. user_agent,
			'Referer: ' .. referer,
			'Connection: Keep-Alive'
			})
	else
		c = curl_init(url, user_agent, referer)
		c:setopt_followlocation(1)
		c:perform({writefunction = function(str) text = text .. str end})
		return text
	end
end

-- 展开所有重定向
local function curl_get_location(video_url, recurs)
	local function h_build_w_cb(t)
		return function(s,len)
			name, value = s:match("(.-): (.+)")
			if name and value then
				t.headers[name] = value:gsub("[\n\r]", "")
				--print(name, t.headers[name])
			end

			return len, nil
		end
	end

	local text = ''
	c = curl_init(video_url, nil, nil)

	local ret = {}
	ret.headers = {}
	c:perform({headerfunction=h_build_w_cb(ret), writefunction=function(str) text = text .. str end })

	if ret.headers.Location and ret.headers.Localtion ~= '' then
		if recurs then
			return curl_get_location(ret.headers.Location, recurs)
		else
			return ret.headers.Location
		end
	end

	return video_url, text
end

local function curl_match(url, regular)
	local text = curl_get(url)
	if text then
		return rex.match(text, regular)
	end
end

local function curl_json(url, regular)
	local text = curl_get(url)
	if text then
		if regular and regular ~= '' then
			text = rex.match(text, regular)
		end
		if text and text ~= '' then
			return cjson.decode(text)
		end
	end
end

local function get_video_auth_cntv(url)
	local hlsurl = url

	local header = curl_get("http://vdn.apps.cntv.cn/api2/live.do?channel=pa://cctv_p2p_hdcctv2&type=ipad", "cbox/5.0.0 CFNetwork/609.1.4 Darwin/13.0.0")

	if string.find(url, 'cntv.cloudcdn.net:800') or string.find(url, 'cntv.wscdns.com:800') then
		local auth1 = rex.match(header, 'AUTH=(.*?)"')
		hlsurl = url .. '?AUTH=' .. auth1
	elseif string.find(url, 'live.cntv.cn') or string.find(url, 'cntv.wscdns.com') then
		local auth2 = rex.match(header, 'AUTH=(ip.*?)"')
		hlsurl = url .. '?AUTH=' .. auth2
	end

	return hlsurl
end

-- pa://cctv_p2p_hdcctv1
local function get_video_cntv(url)
	local function check_m3u8(url)
		if string.find(url, "m3u8") == nil or string.len(url) < 15 or string.find(url, 'cntv.cloudcdn.net') or string.find(url, 'dianpian.mp4') then
			return nil
		end

		return url
	end

	local url = string.format("http://vdn.live.cntv.cn/api2/live.do?client=iosapp&channel=%s", url)

	local js = curl_json(url)

	if js and js.hls_url then
		local video_url = nil
		if video_url == nil then video_url = check_m3u8(js.hls_url.hls1) end
		if video_url == nil then video_url = check_m3u8(js.hls_url.hls2) end
		if video_url == nil then video_url = check_m3u8(js.hls_url.hls3) end
		if video_url == nil then video_url = check_m3u8(js.hls_url.hls5) end

		if video_url then
			--print(video_url)
			video_url = string.gsub(video_url, "m3u8 \\?", "m3u8?")
			video_url = string.gsub(video_url, ":8000:8000", ":8000")

			video_url = kola.strtrim(video_url)

			return video_url
		end
	end

	return ''
end

local function get_video_m2otv(url)
	local function drm( url )
		local url = 'http://www.ahtv.cn//m2o/player/drm.php?url=' .. kola.urlencode('http://stream2.ahtv.cn/ahgg/hd/live.m3u8')
		return curl_get(url)
	end

	local url = string.gsub(url, "m2otv://", "http://")

	local text = curl_match(url, '(<\\?xml[\\s\\S]*)')

	if not text then
		return '{}'
	end

	local x = xml.eval(text)

	local baseUrl = nil
	local v= find(x, "video")
	for a, b in pairs(v) do
		if a == 'baseUrl' then
			baseUrl = b
			break
		end
	end

	local videoUrl = {}

	local v= find(x, "video", "item")
	for a, b in pairs(v) do
		local sd = nil
		if b['url'] ~= nil then
			videoUrl[b['url']] = string.format("%s%slive.m3u8", baseUrl, b['url'])
		end
	end

	if videoUrl['hd/'] then
		return drm(videoUrl['hd/'])
	elseif videoUrl['sd/'] then
		return drm(videoUrl['sd/'])
	elseif videoUrl['cd/'] then
		return drm(videoUrl['cd/'])
	elseif videoUrl['ld/'] then
		return drm(videoUrl['ld/'])
	end

	return ''
end

local function get_video_pptv(url)
	vid = string.gsub(url, "pptv://", "")
	local kk = "";
	local user_agent = "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53"
	local pphtml = curl_get("http://v.pptv.com/show/h1G4Np4EdLIVkics.html",
					user_agent, "http://live.pptv.com/")

	if pphtml and string.find(pphtml, "kk%%3D") then
		kk = rex.match(pphtml, 'kk%3D(.*?)"')
	end

	if not isnan(vid) then
		--url = string.format("http://web-play.pptv.com/web-m3u8-%s.m3u8?type=ikan&playback=0&kk=%s&o=v.pptv.com", vid, kk)
		url = string.format("http://web-play.pptv.com/web-m3u8-%s.m3u8?type=ipad&playback=0&kk=%s", vid, kk)
		--url = string.format('http://web-play.pptv.com/web-m3u8-%s.m3u8?type=m3u8.web.pad&playback=0', id)
		return url
	end

	url = "http://jump.synacast.com/live2/" .. vid
	local xml = curl_get(url)
	if xml then
		local ip = rex.match(xml, '<server_host>(.*?)</server_host>')
		local delay = rex.match(xml, '<delay_play_time>(.*?)</delay_play_time>')

		return string.format("http://%s/live/5/30/%s.m3u8?type=m3u8.web.pad&playback=0&kk=%s&o=v.pptv.com", ip, vid, kk)
	end

	return ""
end

local function get_video_qqtv(url)
	local function get_video_url1(playid)
		local url = playid
		if string.find(playid, "http://") == nil then
			url = string.format('http://zb.v.qq.com:1863/?progid=%s&redirect=0&apptype=live&pla=ios', playid)
		end

		return curl_match(url, 'location url="(.*?)"')
	end

	local function get_video_url2( playid )
		-- stream:
		--	1 : flv
		-- 	2 : m3u8
		local url = string.format('http://info.zb.qq.com/?stream=1&sdtfrom=003&cnlid=%s&cmd=2&pla=0&flvtype=1', playid)

		local text = curl_get(url)
		if text then
			text = string.gsub(text, ";", "")
			local js = cjson.decode(text)

			if js then
				return js.playurl
			end
		end

		return ""
	end

	playid = string.gsub(url, "qqtv://", "")
	local url = string.format('http://zb.cgi.qq.com/commdatav2?cmd=4&channel_id=%s', playid)

	local js = curl_json(url, "QZOutput.*=({[\\s\\S]*});")
	if js then
		--{"ret":"0","flashver":"","p2p":"","http":"1","redirectver":"fplivev1.1"}
		--{"ret":-1,"msg":"no record"}
		if js.ret == "0" then
			return get_video_url2(playid)
		end
	end

	return get_video_url1(playid)
end

local function get_video_sohutv(url)
	pid = string.gsub(url, "sohutv://", "")
    local url = string.format('http://live.tv.sohu.com/live/player_json.jhtml?encoding=utf-8&lid=%s&type=1', pid)

	local js = curl_json(url)

	if js and js.data.live then
		js = curl_json(js.data.live)

		if js and js.code == '000000' then
			return js.url
		end
	end

	return ''
end


local function get_letv_video2(url)
	url = string.gsub(url, 'format=%d+', 'format=1')
	url = string.gsub(url, 'playid=%d+', 'playid=3')

	local js = curl_json(url)
	if js and js.nodelist then
		for k,v in pairs(js.nodelist) do
			if v.location then
				return v.location
			end
		end
	end

	return url
end

local function get_video_52itvkey(url)
	local time = kola.gettime() + 300
	local text = string.format('%d,3360a490fb76d9b648fe14019a8aaab8', time)
	return string.format('%s?tm=%d&key=%s&', url, time, string.lower(kola.md5(text)))
end

local function get_M3u8tmKey(url)
	local time = kola.gettime() + 500
	local text = string.format('%d,　###############', time)

	return string.format('%s?tm*=%d&key*=%s&', url, time, string.lower(kola.md5(text)))
end

local function get_M3u8URL(url)
	if string.find(url, "/pptv/") or string.find(url, "/letv/") then
			url = curl_match(url, "(http://.*)");
			if string.find(url, "live.gslb.letv.com/gslb") then
				url = get_letv_video2(url)
			end
	end

	return url
end

local function get_video_vlive(url)
	url = get_M3u8tmKey(url)
	url = get_M3u8URL(url)

	return url
end

local function get_video_52itv(url)
	url = get_video_52itvkey(url)

	if string.find(url, '.sdtv') then
		local xml = curl_get(url, 'GGwlPlayer/QQ243944493', url)
		return ''
	elseif string.find(url, '.m3u8') then
		return curl_get_location(url, true)
	elseif string.find(url, '.letv') then
		url, _ = curl_get_location(url, false)
		return get_letv_video2(url)
	end

	return curl_get_location(url)
end

local function get_video_imgotv(url)
	local pid = string.gsub(url, "imgotv://", "")
	local pid = string.gsub(pid, "/", "")
	local url = string.format("http://interface.hifuntv.com/mgtv/BasicIndex/ApplyPlayVideo?Tag=26&BussId=1000000&VideoType=1&MediaAssetsId=channel&CategoryId=1000&VideoIndex=0&Version=3.0.11.1.2.MG00_Release&VideoId=%s", pid);

	return curl_match(url, 'url="(.*?)"')
end

local function get_video_lntv(url)
	pid = string.gsub(url, "lntv://", "")
	local url = 'http://zd.lntv.cn/lnradiotvnetwork/live_liveDetail.do?flag=1&id=' .. pid
	--print(url)

	url = curl_match(url, "var playM3U8 = '(.*?)';")
	url = curl_match(url, "(http://.*)")
	return url
end

local function get_video_tvie(url)
	url = string.gsub(url, "tvie://", "http://")

	local referer = rex.match(url, "referer=(.*)")

	if referer then
		referer = kola.urldecode(referer)
	end

	--local function get_timestamp()
	--	return kola.gettime()
	--end

	local function getvideo(url)
		if referer ~= nil and referer ~= '' then
			return string.format('%s -H "Referer: %s"', url, referer)
		end
		return url
	end
	--print(url)
	local text = curl_get(url)

	if text and text ~= "TVie Exception: No streams." then
		local data_obj = cjson.decode(text)
		if data_obj == nil then
			return ''
		end

		if string.find(url, 'nbtv.cn') then -- 宁波台跟别人为什么要不一样呢？
			return string.format('http://zb.nbtv.cn:8134/hls-live/livepkgr/_definst_/liveevent/%s_1.m3u8', data_obj.channel_name)
		end

		if type(data_obj.result) == "table" then
			if (data_obj ~= nil) and type(data_obj.result.datarates) == "table" then
				local video_url = ''
				local id        = rex.match(url, 'getCDNByChannelId/(\\d*)')
				local timestamp = math.floor(data_obj.result.timestamp / 1000) * 1000

				for k,v in pairs(data_obj.result.datarates) do
					local cname = v[1]
					if cname == nil then
						cname = 'channels'
					end
					video_url = string.format('http://%s/channels/%s/%s.flv/live?%s', cname, id, k, tostring(timestamp))
					break
				end

				return getvideo(video_url)
			end
		elseif type(data_obj.streams) == "table" then
			local channel_name = data_obj['channel_name']
			local customer_name = data_obj['customer_name']
			local streams = data_obj['streams']
			local video_url = ''

			for k,v in pairs(streams) do
				-- video_url = string.format('http://%s/channels/%s/%s/flv:%s/live?%d',
				-- v.cdnlist[1], customer_name, channel_name, k, get_timestamp())
				video_url = string.format('http://%s/channels/%s/%s/flv:%s/live',
					v.cdnlist[1], customer_name, channel_name, k)
				break
			end

			return getvideo(video_url)
		end
	end

	return ""
end

local function get_video_wolidou(url)
	local function curl_s_key(s)
		local key_url = string.format("http://www.wolidou.com/x/key.php?f=k&t=%d", kola.gettime() * 1000)
		c1 = curl_init(key_url)
		c1:perform({writefunction=function(str) end })
	end

	local function GetUrl(url)
		local c2 = curl_init(url)
		local ret = {}
		ret.headers = {}

		local text = ''
		c2:perform( {writefunction=function(str) text = text .. str end} )

		if ret.headers.Location and ret.headers.Location ~= 'http://www.wolidou.com/live.mp4' then
			return get_video_url(ret.headers.Location)
		end

		local data_obj = cjson.decode(text)

		if data_obj == nil then
			return get_video_url(text)
		end

		if data_obj.u then
			return get_video_url(data_obj.u)
		elseif data_obj.wolidou then
			return get_video_url(data_obj.wolidou)
		end
	end

	if string.find(url, 'http://www.wolidou.com/x') then
		curl_s_key(share)
		return GetUrl(url)
	elseif string.find(url, 'live.mp4') then
		return ""
	end

	return url
end

local function get_video_jlntv(url)
	local url = string.gsub(url, 'jlntv://', 'http://live.jlntv.cn/')
	return curl_match(url, "var playurl = '(.*)';")
end

local function get_video_jxtv(url)
	local url = string.gsub(url, 'jxtv://', 'http://')
	return curl_match(url, 'html5file:"(.*)"')
end

local function get_video_smgbbtv(url)
	local pid = string.gsub(url, 'smgbbtv://', '')
	local url = string.format('http://l.smgbb.cn/channelurl.ashx?starttime=0&endtime=0&channelcode=%s', pid)

	return curl_match(url, '\\[CDATA\\[(.*)\\]\\]></channel>')
end

local function get_video_wztv(url)
	local pid = string.gsub(url, "wztv://", "")
	return curl_match('http://www.dhtv.cn/static/js/tv.js?acm', "file: '(.*)'")
end

local function get_video_iqilu(url)
	local live, m3u8 = rex.match(url, 'iqilu://(.*?)/(.*)')

	local key_url = 'http://huodong.iqilu.com/active/video/clientnew/public_s/?c=' .. live
	local user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0 like Mac OS X)'
	local referer = 'http://v.iqilu.com/live/' .. live .. '/'
	local text = curl_get( key_url, user_agent, referer )

	--print(text)
	time, st = rex.match(text, '\\|href\\|.*?\\|(.*?)\\|else\\|.*?\\|(.*?)\\|test\\|')
	return string.format('http://m3u8.iqilu.com/live/%s.m3u8?st=%s&e=%s', m3u8, st, time)
end

function get_video_url_direct(url, albumName, vid)
	local func_maps = {
		['^http://url.52itv.cn/vlive'] = get_video_vlive,
		['^http://url.52itv.cn/gslb']  = get_video_52itvkey,
		['^http://url.52itv.cn/live']  = get_video_52itvkey,
		['cntv.cloudcdn.net']          = get_video_auth_cntv,
		['cntv.wscdns.com']            = get_video_auth_cntv,
		['live.cntv.cn']               = get_video_auth_cntv,

		['^pa://']         = get_video_cntv,
		['^pptv://']       = get_video_pptv,
		['^qqtv://']       = get_video_qqtv,
		['^sohutv://']     = get_video_sohutv,
		['^imgotv://']     = get_video_imgotv,
		['^lntv://']       = get_video_lntv,
		['^m2otv://']      = get_video_m2otv,
		['^tvie://']       = get_video_tvie,
		['^jlntv://']      = get_video_jlntv,
		['^jxtv://']       = get_video_jxtv,
		['^smgbbtv://']    = get_video_smgbbtv,
		['^iqilu://']      = get_video_iqilu,
		['^wztv://']       = get_video_wztv,
		['wolidou.com']    = get_video_wolidou,
		--['.letv']          = get_video_52itv,
		--['ext=letv']       = get_video_52itv,
	}

	print(albumName, vid, url)
	for k,func in pairs(func_maps) do
		if string.find(url, k) then
			url = func(url)
			break
		end
	end
	return url
end

function get_video_url(url, albumName, vid)
	return get_video_url_direct(url, albumName, vid)
	--local key = kola.md5(kola.chipid() .. url)
	--local cache_url = string.format('/video/cache_list_%s?time=180', key)
	--local value = curl_get(cache_url)
	--if value == nil or value == '' then
	--	value = get_video_url_direct(url, albumName, vid)
	--	kola.wpost(cache_url, value)
	--else
	--	print("in cached.", cache_url)
	--end

	--return value
end

