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

function get_videolist(cid, pid, vid, pageNo, pageSize)
	local function get_album_set(vid)
		local ret = {}
		ret.updateSet = 1
		ret.totalSet = 1

		return cjson.encode(ret)
	end

	local pno = tonumber(pageNo)
	local psize = tonumber(pageSize);
	if pno == 0 and psize == 0 then
		return get_album_set(vid)
	end

	local url = string.format('http://www.ahtv.cn/m2o/player/channel_xml.php?first=1&id=%s', vid)
	--print(url)
	local text = kola.wget(url)
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
	if text == nil then
		return '{}'
	end

	local ret = {}

	video = {}
	video.cid         = cid
	video.pid         = pid
	video.vid         = vid
	video.name        = v.name
	video.resolution = {}
	video.resolution.text = {}
	local v= find(x, "video", "item")
	for a, b in pairs(v) do
		local sd = nil
		if b['url'] ~= nil then
			if b['url'] == 'sd/' then
				sd = '超清'
			elseif b['url'] == 'hd/' then
				sd = '高清'
			elseif b['url'] == 'hd/' then
				sd = '标清'
			end
			if sd ~= nil then
				local fullUrl = string.format("%s%slive.m3u8", baseUrl, b['url'])
				video.resolution.text[sd] = {}
				video.resolution.text[sd].text = fullUrl
			end
		end
	end
	video.info = {}
	video.info['script']        = 'ahtv'
	video.info['function']      = 'get_channel'
	video.info['parameters'] = {}
	video.info['parameters'][1] = vid

	ret.size = 1
	ret.videos = {}
	ret.videos[1] = video

	return cjson.encode(ret)
end

function get_channel(vid)
	local url = string.format("http://www.ahtv.cn/m2o/player/program_xml.php?time=%d&channel_id=%s", kola.gettime(), vid)
	--print(url)

	local ret = {}
	text = kola.wget(url)
	if text == nil then
		return '{}'
	end
	text = kola.pcre('(<\\?xml[\\s\\S]*)', text)
	x = xml.eval(text)
	v= find(x, "program", "item")
	for k, b in pairs(v) do
		if type(b) == "table" then
			ret[k] = {}
			s = tonumber(b['startTime'])
			ret[k].time_string = os.date("%H:%M", s)
			ret[k].time = s
			ret[k].duration = tonumber(b['duration'])
			ret[k].title = b['name']
		end
	end

	return cjson.encode(ret)
end
