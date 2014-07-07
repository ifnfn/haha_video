--  获取节目集列表
function get_videolist(pid, vid, pageNo, pageSize)
	local function str_to_min(s)
		local list = {}
		local id = 0
		for i in string.gmatch(s, "%w+") do
			id = id + 1
			list[id] = i
		end

		if id == 3 then
			return tonumber(list[1]) * 3600 + tonumber(list[2]) * 60 + tonumber(list[3])
		elseif id == 2 then
			return tonumber(list[1]) * 60 + tonumber(list[2])
		elseif id == 1 then
			return tonumber(list[1])
		else
			return 0
		end
	end
	local function get_album_set(vid)
		local url = string.format('http://www.letv.com/v_xml/%s.xml', vid)
		local text = kola.wget(url, false)
		--print(url)
		if text == nil then
			return '{}'
		end

		text = rex.match(text, "<playurl><!\\[CDATA(.*)\\]></playurl>")

		--print(text)
		if text == nil then
			return '{}'
		end

		local js = cjson.decode(text)
		--print(text)

		local ret = {}
		--ret.totalSet = js.totalSets
		ret.updateSet = js[1].total

		return cjson.encode(ret)
	end

	local ret = {}

	local pno = tonumber(pageNo)
	local psize = tonumber(pageSize);
	if pno == 0 and psize == 0 then
		return get_album_set(vid)
	end

	local url = string.format('http://app.letv.com/ajax/getFocusVideo.php?p=1&top=%d&max=%d&pid=%s', pno * psize, psize, pid)
	local text = kola.wget(url, false)
	if text == nil then
		return '{}'
	end

	text = kola.strtrim(text)

	if text == nil then
		return '{}'
	end

	ret.size = 0
	local videos = {}
	local js = cjson.decode(text)
	for k,v in ipairs(js) do
		video = {}

		video.cid         = js.cid
		video.pid         = pid
		video.vid         = tostring(v.vid)
		video.playlistid  = pid
		video.name        = v.title
		video.showName    = v.title
		if v.duration ~= nil then
			video.playLength = str_to_min(v.duration)
		end
		video.order       = v.key
		video.smallPicUrl = v.pic
		video.largePicUrl = v.pic
		video.resolution = {}
		video.resolution.script = 'letv'
		video.resolution['function'] = 'get_resolution'
		video.resolution.parameters = {}
		video.resolution.parameters[1] = video.vid
		video.resolution.parameters[2] = tostring(video.cid)

		video.info = {}
		videos[k] = video
		ret.size = ret.size + 1
	end

	if #videos > 0 then
		ret.videos = videos
	end

	--print(cjson.encode(ret))
	return cjson.encode(ret)
end

-- 攻取节目视频清晰度
function get_resolution(vid)
	local function base64_to_url(text)
		local o = 0
		local i = 0
		while true do
			i = string.find(text, '/' , i + 1)
			if i == nil then
				break
			end
			o=i
		end
		i = string.find(text, '?', o)
		local x = string.sub(text, o + 1, i - 1)

		local a1 = string.sub(text, 1, string.find(text, '/', 8))
		local a2 = kola.base64_decode(x)

		return a1 .. a2
	end

	local url = string.format('http://www.letv.com/v_xml/%s.xml', vid)
	local text = kola.wget(url, false)

	text = rex.match(text, "<playurl>(.*)</playurl>")
	text = rex.match(text, "<!\\[CDATA(.*)\\]>")

	if text == nil then
		return '{}'
	end

	local js = cjson.decode(text)

	local ret = {}
	for k,v in ipairs(js) do
		if v.dispatch ~= nil and type(v.dispatch) == "table" then
			for a,b in pairs(v.dispatch) do
				ret[a] = base64_to_url(b[1])
			end
		end

		if v.dispatchbak ~= nil and type(v.dispatchbak) == "table" then
			for a,b in pairs(v.dispatchbak) do
				if ret[a] == nil then
					ret[a] = base64_to_url(b[1])
				end
			end
		end

		if v.dispatchbak1 ~= nil and type(v.dispatchbak1) == "table" then
			for a,b in pairs(v.dispatchbak1) do
				if ret[a] == nil then
					ret[a] = base64_to_url(b[1])
				end
			end
		end

		if v.dispatchbak2 ~= nil and type(v.dispatchbak2) == "table" then
			for a,b in pairs(v.dispatchbak2) do
				if ret[a] == nil then
					ret[a] = base64_to_url(b[1])
				end
			end
		end

		if v.dispatchspath ~= nil and type(v.dispatchspath) == "table" then
			for a,b in pairs(v.dispatchspath) do
				if ret[a] == nil then
					ret[a] = base64_to_url(b[1])
				end
			end
		end
	end

	local rx = {}
	for k,v in pairs(ret) do
		if k == '350' then
			rx['标清'] = {}
			rx['标清'].text = v
		elseif k == '1000' then
			rx['高清'] = {}
			rx['高清'].text = v
			rx['高清'].default = 1
		elseif k == '1300' or k == '720p' then
			rx['超清'] = {}
			rx['超清'].text = v
		elseif k == '1080p' then
			rx['原画质'] = {}
			rx['原画质'].text = v
		else
			print(k,v)
		end
	end

	return cjson.encode(rx)
end
