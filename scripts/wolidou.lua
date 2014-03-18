local function h_build_w_cb(t)
	return function(s,len)
		--stores the received data in the table t
		--prepare header data
		name, value = s:match("(.-): (.+)")
		if name and value then
			t.headers[name] = value:gsub("[\n\r]", "")
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
	c:setopt_referer(url)
	c:setopt_url(key_url)

	return c
end

local function curl_key(s)
	local key_url = string.format("http://www.wolidou.com/s/key.php?f=k&t=%d", kola.gettime() * 1000)
	return curl_init(s, key_url)
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

	video_url = data_obj.u

	local s = cURL.share_init()
	s:setopt_share("COOKIE")
	s:setopt_share("DNS")

	local c = curl_key(s)
	local c2 = curl_init(s, video_url)

	-- getkey
	c:perform({writefunction=function(str) end })

	--geturl
	local ret = {}
	ret.headers = {}
	c2:perform({headerfunction=h_build_w_cb(ret), writefunction=function(str) end })

	if ret.headers.Location ~= 'http://www.wolidou.com/live.mp4' then
		return ret.headers.Location
	end

	return ""
end

local function sdsj_url(video_url)
	local s = cURL.share_init()
	s:setopt_share("COOKIE")
	s:setopt_share("DNS")

	video_url = string.format("%s&ts=%d", video_url, kola.gettime() * 1000)
	local c = curl_key(s)
	local c2 = curl_init(s, video_url)

	-- getkey
	c:perform({writefunction=function(str) end })

	--geturl
	local ret = ''
	c2:perform({writefunction=function(str) ret = ret .. str end })

	if ret then
		local data_obj = cjson.decode(ret)

		if data_obj ~= nil then
			return data_obj.wolidou
		end
	end

	return ''
end

local function sxmsp_url(video_url)
	local s = cURL.share_init()
	s:setopt_share("COOKIE")
	s:setopt_share("DNS")

	local c2 = curl_init(s, video_url)

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
	if string.find(video_url, 'http://www.wolidou.com/c/basic') then
		return basic_1(video_url)
	elseif string.find(video_url, 'http://www.wolidou.com/s/sdsj.php') or
		string.find(video_url, 'http://www.wolidou.com/s/dxcctv.php') or
		string.find(video_url, 'http://www.wolidou.com/s/yu.php') then
		return sdsj_url(video_url)
	elseif string.find(video_url, 'http://wolidou.gotoip3.com/sxmsp.php') or
    string.find(video_url, 'http://wolidou.gotoip3.com/pptv.php') then
		return sxmsp_url(video_url)
	elseif string.find(video_url, 'rtmp://') then
		return video_url
	else
		return video_url
	end
end

function get_channel(video_url)
	return ""
end


