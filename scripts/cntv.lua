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

function check_m3u8(url)
	local text = kola.wget(url, false)
	if text ~= nil and string.find(text, "EXTM3U") ~= nil then
		return url
	end

	return nil
end

function geturl_hds(url, aid)
	local text = kola.wget(url, false)

	if text == nil then
		return ''
	end

	local x = xml.eval(text)

	local video_url = nil
	local bitrate = 0
	local v= find(x, "manifest", "media")
	for a, b in pairs(v) do
		if b.streamId ~= nil then
			this_b = tonumber(b.bitrate)
			if this_b > bitrate then
				bitrate = this_b
				if b.url ~= 'index' then
					u = string.gsub(b.url, "seg1", "seg0")
					video_url = '/' .. string.sub(u, 4) .. ".m3u8"
					local u = check_m3u8(video_url)
					if u ~= nil then
						video_url = u
					end
				end
			end
		end
	end

	return video_url
end

function cctv_p2p_url(vid, aid)
	local url = string.format("http://vdn.live.cntv.cn/api2/liveHtml5.do?channel=pa://cctv_p2p_hd%s&client=html5", vid)
	local text = kola.wget(url, false)
	local video_url = ''
	if text ~= nil then
		local hls_vod_url = ''

		text = kola.pcre("var html5VideoData = '(.*)';", text)
		--print(text)
		local js = cjson.decode(text)

		if js.hls_url ~= nil then
			if js.hls_url.hls1 ~= nil and js.hls_url.hls1 ~= '' then
				hls_vod_url = js.hls_url.hls1
			else
				hls_vod_url = js.hls_url.hls2
			end

			video_url = check_m3u8(hls_vod_url)
			if video_url ~= nil then
				return video_url
			end
		end

		video_url = js['hds_url']['hds2']
		if string.find(video_url, "http://") ~= nil and string.find(video_url, "channel") ~= nil then
			return video_url
		end

		-- 如果有 hds
		video_url = ''
		if js['hds_url'] ~= nil then
			local u = js['hds_url']['hds1']
			if string.find(u, "http://") ~= nil and string.find(u, "f4m") ~= nil then
				u = geturl_hds(u, aid)
				if u ~= nil then
					return u
				end
			end
		end
	end

	return video_url
end

function kola_main(vid, aid)
	return cctv_p2p_url(vid, aid)
end

function get_channel(vid)
	return ""
end
