function get_video_url(url)
	print(url)
	if string.find(url, 'pa://') then
		return get_video_cntv(url)
	elseif string.find(url, 'm2o://') then
		return get_video_m2o(url)
	elseif string.find(url, 'pptv://') then
		return get_video_pptv(url)
	elseif string.find(url, 'qqtv://') then
		return get_video_qqtv(url)
	elseif string.find(url, 'sohutv://') then
		return get_video_sohutv(url)
	elseif string.find(url, 'imgotv://') then
		return get_video_imgotv(url)
	elseif string.find(url, 'url.52itv.cn') then
		return get_video_52itv(url)
	else
		return url
	end
end

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

local function curl_get( url, user_agent, referer )
	local text = ''
	c = cURL.easy_init()
	if user_agent == nil then
		user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36"
	end

	if referer == nil then
		referer = url
	end
	c:setopt_useragent(user_agent)
	c:setopt_referer(referer)
	c:setopt_followlocation(1)
	c:setopt_url(url)

	c:perform({writefunction = function(str) text = text .. str end})

	return text
end

-- 展开所有重定向
local function curl_get_52itv(video_url)
	local function h_build_w_cb(t)
		return function(s,len)
			--stores the received data in the table t
			--prepare header data
			name, value = s:match("(.-): (.+)")
			if name and value then
				t.headers[name] = value:gsub("[\n\r]", "")
				--print(name, t.headers[name])
				if name == 'Set-Cookie' then
					Cookie = t.headers[name]
				end
			else
				code, codemessage = string.match(s, "^HTTP/.* (%d+) (.+)$")
				if code and codemessage then
					t.code = tonumber(code)
					t.codemessage = codemessage:gsub("[\n\r]", "")
				end
			end

			return len, nil
		end
	end

	c = cURL.easy_init()

	c:setopt_useragent("GGwlPlayer/QQ243944493")
	c:setopt_url(video_url)

	ret = {}
	ret.headers = {}
	c:perform({headerfunction=h_build_w_cb(ret), writefunction=function(str) end })

	if ret.headers.Location and ret.headers.Localtion ~= '' then
		return curl_get_52itv(ret.headers.Location)
	end

	return video_url
end

-- pa://cctv_p2p_hdcctv1
function get_video_cntv( url )
	local function check_m3u8(url)
		if string.find(url, "m3u8") == nil or string.len(url) < 15 or string.find(url, 'cntv.cloudcdn.net') or string.find(url, 'dianpian.mp4') then
			return nil
		end
		return url
	end

	local url = string.format("http://vdn.live.cntv.cn/api2/live.do?client=iosapp&channel=%s", url)
	local text = kola.wget(url, false)

	if text then
		local js = cjson.decode(text)

		if js and js.hls_url then
			local video_url = nil
			if video_url == nil then video_url = check_m3u8(js.hls_url.hls1) end
			if video_url == nil then video_url = check_m3u8(js.hls_url.hls2) end
			if video_url == nil then video_url = check_m3u8(js.hls_url.hls3) end
			if video_url == nil then video_url = check_m3u8(js.hls_url.hls5) end

			if video_url then
				print(video_url)
				video_url = string.gsub(video_url, "m3u8 \\?", "m3u8?")
				video_url = string.gsub(video_url, ":8000:8000", ":8000")

				video_url = kola.strtrim(video_url)
				if string.find(video_url, "AUTH=ip") == nil then
					text = curl_get("http://vdn.live.cntv.cn/api2/live.do?channel=pa://cctv_p2p_hdcctv1", "cbox/5.0.0 CFNetwork/609.1.4 Darwin/13.0.0")
					auth = rex.match(text, '(AUTH=ip.*?)"')
					if auth then
						video_url =  string.format("%s?%s", video_url, auth)
					end
				end
				return video_url
			end
		end
	end

	return ''
end

-- 攻取节目的播放地址
function get_video_m2o(url)
	local text = kola.wget(url, false)
	if text == nil then
		return '{}'
	end
	text = kola.pcre('(<\\?xml[\\s\\S]*)', text)
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
		return videoUrl['hd/']
	elseif videoUrl['sd/'] then
		return videoUrl['sd/']
	elseif videoUrl['cd/'] then
		return videoUrl['cd/']
	elseif videoUrl['ld/'] then
		return videoUrl['ld/']
	end

	return ''
end

function get_video_pptv(url)
	vid = string.gsub(url, "pptv://", "")
	local kk = "";
	local pphtml = curl_get("http://v.pptv.com/show/h1G4Np4EdLIVkics.html",
					"Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
					"http://live.pptv.com/")

	if pphtml and string.find(pphtml, "kk%%3D") then
		kk = rex.match(pphtml, 'kk%3D(.*?)"')
	end

	--if not isnan(vid) then
	--	return string.format("http://web-play.pptv.com/web-m3u8-%s.m3u8?type=m3u8.web.pad&playback=0&kk=%s&o=v.pptv.com", vid, kk)
	--	return string.format('http://web-play.pptv.com/web-m3u8-%s.m3u8?type=m3u8.web.pad&playback=0', id)
	--end

	local xml = kola.wget("http://jump.synacast.com/live2/" .. vid)
	if xml then
		local ip = rex.match(xml, '<server_host>(.*?)</server_host>')
		local delay = rex.match(xml, '<delay_play_time>(.*?)</delay_play_time>')

		return string.format("http://%s/live/5/30/%s.m3u8?type=m3u8.web.pad&playback=0&kk=%s&o=v.pptv.com", ip, vid, kk)
	end

	return ""
end

function get_video_qqtv( url )
	local function get_video_url1(playid)
		local url = playid
		if string.find(playid, "http://") == nil then
			url = string.format('http://zb.v.qq.com:1863/?progid=%s&redirect=0&apptype=live&pla=ios', playid)
		end
		local text = kola.wget(url, false)

		if text then
			text = kola.pcre('location url="(.*?)"', text)
			return kola.strtrim(text)
		end

		return ""
	end

	local function get_video_url2( playid )
		-- stream:
		--	1 : flv
		-- 	2 : m3u8
		local url = string.format('http://info.zb.qq.com/?stream=1&sdtfrom=003&cnlid=%s&cmd=2&pla=0&flvtype=1', playid)

		local text = kola.wget(url, false)
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

	local text = kola.wget(url, false)
	text = kola.pcre("QZOutput.*=({[\\s\\S]*});", text)
	local js = cjson.decode(text)

	if js then
		--{"ret":"0","flashver":"","p2p":"","http":"1","redirectver":"fplivev1.1"}
		--{"ret":-1,"msg":"no record"}
		if js.ret == "0" then
			return get_video_url2(playid)
		end
	end

	return get_video_url1(playid)
end

function get_video_sohutv(url)
	pid = string.gsub(url, "sohutv://", "")
    local url = string.format('http://live.tv.sohu.com/live/player_json.jhtml?encoding=utf-8&lid=%s&type=1', pid)
	local text = kola.wget(url, false)

	if text == nil then
		return ''
	end
	local ret = {}
	local js = cjson.decode(text)
	local live = js.data.live

	text = kola.wget(live, false)
	if text ~= nil then
		js = cjson.decode(text)

		if js.msg == 'OK' then
			return js.url
		end
	end

	return ''
end

function get_video_52itv(url)
	local function get_livekey()
		local d = kola.gettime()
		local key = string.format('st=QQ243944493&tm=%d', d)

		return string.format('%s-%d', string.lower(kola.md5(key)), d)
	end

	url = string.format('%s?k=%s', url, get_livekey())
	if string.find(url, '.sdtv') then
		local xml = curl_get(url, 'GGwlPlayer/QQ243944493', url)
		return ''
	elseif string.find(url, '.m3u8') then
		return curl_get_52itv(url)
	elseif string.find(url, '.letv') then
		local url = string.gsub(url, '.letv', '')
		url = curl_get_52itv(url)

		local xml = curl_get(url, "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.2; GGwlPlayer/QQ243944493) Gecko/20100115 Firefox/3.6");
		if string.find(xml, '</nodelist>') then
			print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
			print(xml)
			local nodelist = rex.match(xml, '<nodelist>(.*?)</nodelist>')
		end

		return url
	end
	return string.format('%s?k=%s -H "User-Agent: GGwlPlayer/QQ243944493"', url, get_livekey())
end

function get_video_imgotv(url)
	local pid = string.gsub(url, "imgotv://", "")
	local url = string.format("http://interface.hifuntv.com/mgtv/BasicIndex/ApplyPlayVideo?Tag=26&BussId=1000000&VideoType=1&MediaAssetsId=channel&CategoryId=1000&VideoIndex=0&Version=3.0.11.1.2.MG00_Release&VideoId=%s", pid);
	local text = kola.wget(url, false)

	text = kola.pcre('url="(.*?)"', text)
	return kola.strtrim(text)
end
