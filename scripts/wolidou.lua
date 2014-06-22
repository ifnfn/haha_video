local share = cURL.share_init()
share:setopt_share("COOKIE")
share:setopt_share("DNS")

Cookie=''
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
	return len,nil
	end
end

local function curl_init(s, url, referer)
	local c = cURL.easy_init()
	c:setopt_share(s)
	local key_url = url
	if referer == nil then
		referer = 'http://www.wolidou.com'
	end
	c:setopt_referer(referer)
	c:setopt_useragent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36")
	c:setopt_url(key_url)

	return c
end

local function curl_key(s)
	local key_url = string.format("http://www.wolidou.com/s/key.php?f=k&t=%d", kola.gettime() * 1000)
	return curl_init(s, key_url)
end

local function jstv_url(video_url)
	local c1 = curl_key(share)
	local c2 = curl_init(share, video_url)

	--c1:setopt_verbose(1)
	--c2:setopt_verbose(1)

	-- getkey
	c1:perform({writefunction=function(str) end })

	--geturl
	local ret = {}
	ret.headers = {}
	c2:perform({headerfunction=h_build_w_cb(ret), writefunction=function(str) end })

	if ret.headers.Location ~= 'http://www.wolidou.com/live.mp4' then
		return ret.headers.Location
	end

	return ""
end


local function GetUrl(url)
	local c2 = curl_init(share, url)
	local ret = {}
	ret.headers = {}

	local text = ''
	c2:perform({headerfunction=h_build_w_cb(ret), writefunction=function(str) text = text .. str end })

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

local function basic_1(video_url)
	text = kola.wget(video_url, false)
	if text == nil then
		return ''
	end

	local data_obj = cjson.decode(text)

	if data_obj == nil then
		return ''
	end

	return jstv_url(data_obj.u)
end

local function sdsj_url(video_url)
	video_url = string.format("%s&ts=%d", video_url, kola.gettime() * 1000)
	local c1 = curl_key(share)
	local c2 = curl_init(share, video_url)

	-- getkey
	c1:perform({writefunction=function(str) end })

	--geturl
	local ret = ''
	c2:perform({writefunction=function(str) ret = ret .. str end })

	if ret then
		local data_obj = cjson.decode(ret)

		if data_obj then
			return data_obj.wolidou
		end
	end

	return ''
end

local function sxmsp_url(video_url)
	local c2 = curl_init(share, video_url)

	--geturl
	local ret = {}
	ret.headers = {}
	c2:perform({headerfunction=h_build_w_cb(ret), writefunction=function(str) end })

	if ret.headers.Location ~= 'http://www.wolidou.com/live.mp4' then
		return ret.headers.Location
	end

	return ""
end

function get_video_url(video_url)
	--print(string.format("get_video_url(%s)", video_url))
	if string.find(video_url, 'rtmp://') or string.find(video_url, ".m3u8") then
		return video_url
	elseif string.find(video_url, 'http://www.wolidou.com/c/basic_1') then
		return basic_1(video_url)
	elseif string.find(video_url, 'http://www.wolidou.com/c/basic_2') then
		return GetUrl(video_url)
	elseif string.find(video_url, 'sdsj.php') or string.find(video_url, 'dxcctv.php') or string.find(video_url, 'yu.php') then
		return sdsj_url(video_url)
	elseif string.find(video_url, 'sxmsp.php') or string.find(video_url, 'pptv.php') or string.find(video_url, 'moon.php') then
		return sxmsp_url(video_url)
	elseif string.find(video_url, 'http://www.wolidou.com/x') then
		local url = GetUrl(video_url)
		if string.find(video_url, 'henan') and Cookie ~= '' then
			url = url .. ' -H Set-Cookie: ' .. Cookie
		end
		return url
	elseif string.find(video_url, 'jstv.com.wolidou.php') then
		return jstv_url(video_url)
	elseif string.find(video_url, 'live.mp4') then
		return ""
	else
		return video_url
	end
end
