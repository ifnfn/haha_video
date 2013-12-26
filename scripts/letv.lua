--  获取节目集列表
function get_videolist(pid, vid, pageNo, pageSize)
	local function get_album_set(vid)
		local url = string.format('http://www.letv.com/v_xml/%s.xml', vid)
		local text = kola.wget(url)
		--print(url)

		text = kola.pcre("<playurl><!\\[CDATA(.*)\\]></playurl>", text)
		local js = cjson.decode(text)
		--print(text)

		local ret = {}
		--ret.totalSet   = js.totalSets
		ret.updateSet  = js.total
		return cjson.encode(rx)
	end

	local ret = {}

	if tonumber(pageNo) == 0 and tonumber(pageSize) == 0 then
		ret = get_album_set(vid)
		return cjson.encode(ret)
	end

	local url = string.format('http://app.letv.com/ajax/getFocusVideo.php?p=1&top=0&max=1000&pid=%s', pid)
	local text = kola.wget(url)

	text = string.sub(text, 2, -2)

	ret.size = 0
	local videos = {}
	local js = cjson.decode(text)
	for k,v in ipairs(js) do
--		print(v.vid, v.title)
		local video = {}

		video.cid         = js.cid
		video.pid         = pid
		video.vid         = tostring(v.vid)
		video.playlistid  = pid
		video.name        = v.title
		video.showName    = v.title
		if v.duration ~= nil then
			video.playLength  = tonumber(v.duration) * 60
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
	local text = kola.wget(url)

	text = kola.pcre("<playurl>(.*)</playurl>", text)
	text = kola.pcre("<!\\[CDATA(.*)\\]>", text)
	--print(text)
	local js = cjson.decode(text)

	local ret = {}
	for k,v in ipairs(js) do
		for a,b in pairs(v.dispatch) do
			ret[a] = base64_to_url(b[1])
		end
		for a,b in pairs(v.dispatchbak) do
			if ret[a] == nil then
				ret[a] = base64_to_url(b[1])
			end
		end

		for a,b in pairs(v.dispatchbak1) do
			if ret[a] == nil then
				ret[a] = base64_to_url(b[1])
			end
		end
		for a,b in pairs(v.dispatchbak2) do
			if ret[a] == nil then
				ret[a] = base64_to_url(b[1])
			end
		end
		for a,b in pairs(v.dispatchspath) do
			if ret[a] == nil then
				ret[a] = base64_to_url(b[1])
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
