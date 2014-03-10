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

function get_video_url(video_url)
	text = kola.wget(video_url) --http://www.wolidou.com/c/basic_1.php?u=cctv2
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

	local c = cURL.easy_init()
	c:setopt_share(s)
	local referer = 'http://www.wolidou.com'
	local key_url = string.format("http://www.wolidou.com/s/key.php?f=k&t=%d", kola.gettime() * 1000)
	c:setopt_referer(referer)
	c:setopt_url(key_url)

	local c2 = cURL.easy_init()
	c2:setopt_share(s)
	c2:setopt_url(video_url)
	c2:setopt_referer(referer)

	-- getkey
	c:perform({writefunction=function(str)  end })

	--geturl
	local ret = {}
	ret.headers = {}
	c2:perform({headerfunction=h_build_w_cb(ret), writefunction=function(str) print(str) end })

	return ret.headers.Location
end

