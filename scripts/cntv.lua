function find(var, tag, key, value)
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

function geturl_hds(url, aid)
	local text = kola.wget(url, false)
	if text == nil then
		url = string.format('http://vcbox.cntv.chinacache.net/cache/%s_/seg1/index.f4m', aid)
		print(url)
		text = kola.wget(url, false)
	end

	if text == nil then
		return ''
	end

	local x = xml.eval(text)

	local video_url = ''
	local bitrate = 0
	local v= find(x, "manifest", "media")
	for a, b in pairs(v) do
		if b.streamId ~= nil then
			this_b = tonumber(b.bitrate)
			if this_b > bitrate then
				if b.url == 'index' then
					video_url = string.format('http://hdshls.cntv.chinacache.net/cache/%s_/seg0/index.m3u8', aid)
				else
					u = string.gsub(b.url, "seg1", "seg0")
					u = string.sub(u, 4)
					video_url = string.format('http://hdshls.cntv.chinacache.net/%s.m3u8', u)
				end
				bitrate = this_b
			end
			--print(b.url, b.bitrate)
		end
	end

	print(video_url)

	return video_url
end

function cctv_p2p_url(vid, aid)
	local url = string.format("http://vdn.live.cntv.cn/api2/liveHtml5.do?channel=pa://cctv_p2p_hd%s", vid)
	local text = kola.wget(url, false)
	local video_url = ''
	if text ~= nil then
		text = kola.pcre("var html5VideoData = '(.*)';", text)
		--print(text)
		local js = cjson.decode(text)

		-- 如果有 hds
		if js['hds_url'] ~= nil then
			local u = js['hds_url']['hds1']
			if string.find(u, "http://") ~= nil and string.find(u, "f4m") ~= nil then
				return geturl_hds(u, aid)
			end
		end

		-- 如果有 hls
		for a, url in pairs(js["hls_url"]) do
			if url ~= nil and string.find(url, "http://") ~= nil then
				text = kola.wget(url, false)

				if text ~= nil and string.find(text, "EXTM3U") ~= nil then
					video_url = url
				end
			end
		end
	end

	return video_url
end

function kola_main(vid, aid)
	return cctv_p2p_url(vid, aid)
end

function kola_main1(vid, aid)
	print(vid, aid)
	local url = string.format("http://vcbox.cntv.chinacache.net/cache/hds%s.f4m", vid)
	print(url)
	local text = kola.wget(url, false)
	if text == nil then
		url = string.format('http://vcbox.cntv.chinacache.net/cache/%s_/seg1/index.f4m', aid)
		print(url)
		text = kola.wget(url, false)
	end

	if text == nil then
		return ''
	end

	local x = xml.eval(text)

	local video_url = ''
	local bitrate = 0
	local v= find(x, "manifest", "media")
	for a, b in pairs(v) do
		if b.streamId ~= nil then
			this_b = tonumber(b.bitrate)
			if this_b > bitrate then
				if b.url == 'index' then
					video_url = string.format('http://hdshls.cntv.chinacache.net/cache/%s_/seg0/index.m3u8', aid)
				else
					u = string.gsub(b.url, "seg1", "seg0")
					u = string.sub(u, 10)
					video_url = string.format('http://hdshls.cntv.chinacache.net/cache/%s.m3u8', u)
				end
				bitrate = this_b
			end
			--print(b.url, b.bitrate)
		end
	end

	--print(video_url)

	return video_url
end

function get_channel(vid)
	return ""
end
