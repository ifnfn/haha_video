-- 攻取节目的播放地址

local function get_key(t)
    local e = 0
    for s = 0, 7 do
        e = bit.band(1, t)
        t = bit.rshift(t, 1)
        e = e * 2 ^ 31
        t = t + e
    end
    return tonumber("0x"..bit.tohex(bit.bxor(t, 185025305)))
end

local function curl_get_location(video_url)
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

	print(video_url)
	local text = ''
	c = cURL.easy_init()

	c:setopt_useragent("Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.2; GGwlPlayer/QQ243944493) Gecko/20100115 Firefox/3.6")
	c:setopt_url(video_url)

	local ret = {}
	ret.headers = {}
	c:perform({headerfunction=h_build_w_cb(ret), writefunction=function(str) text = text .. str end })

	if ret.headers.Location and ret.headers.Localtion ~= '' then
		return curl_get_location(ret.headers.Location)
	end

	return video_url, text
end

function get_video_url(url)
	print(url)
	-- http://live.gslb.letv.com/gslb?stream_id=cctv1&tag=live&ext=m3u8&sign=live_tv


	local stream_id = rex.match(url, 'stream_id=(.*?)&')
	print(stream_id)
	local time = kola.gettime() + 600
	local letv_str = string.format("%s,%d,%s", stream_id, time, '1ca1fc9546da2b196ce9edfa5decd787')
	local key = string.lower(kola.md5(letv_str))
	print(key)

	local url = string.format('%s&platid=10&splatid=1011&expect=2&format=0&playid=2&tm=%d&key=%s', url, time, key)
	print(url)

	return curl_get_location(url)
end

--http://live.gslb.letv.com/gslb?stream_id=cctv1&tag=live&sign=live_tv&ext=m3u8&platid=10&splatid=1011&expect=2&format=0&playid=2&tm=1404468553&key=4e64dbdeb3b709765405d7705c855eae
--http://live.gslb.letv.com/gslb?stream_id=cctv1&tag=live&ext=m3u8&sign=live_tv&platid=10&splatid=1011&expect=2&format=0&playid=2&tm=1404468553&key=3385ac3a244116936493635785674c2b
--http://live.gslb.letv.com/gslb?stream_id=cctv1&tag=live&ext=m3u8&sign=live_tv&platid=10&splatid=1011&expect=2&format=0&playid=2&tm=1404468279&key=9f69bfdcb1267d0cff471b02dedd5d51
