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

	else
		return url
	end
end

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
	print(url)
	channel_id = string.gsub(url, "pptv://", "")
	if channel_id then
		return string.format('http://web-play.pptv.com/web-m3u8-%s.m3u8?type=m3u8.web.pad&playback=0', channel_id)
	end

	return ''
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

function get_video_imgotv(url)
	return ""
end


