local function get_videolist_tv(tvid, vid, cid, name)
	--local url = string.format('http://cache.video.qiyi.com/vi/%s/%s/', tvid, vid)
	--local text = kola.wget(url, false)
	--local js = cjson.decode(text)
	--print(js.vu)
	local ret = {}
	ret.videos = {}
	ret.videos[1] = {}
	ret.videos[1].cid = cid
	ret.videos[1].pid = tvid
	ret.videos[1].vid = vid
	ret.videos[1].resolution = get_resolution(tvid, vid)
	ret.videos[1].name = name
	--ret.videos[1].name = js['an']
	--ret.videos[1].resolution = {}
	--ret.videos[1].resolution.script = 'qiyi'
	--ret.videos[1].resolution['function'] = 'get_resolution'
	--ret.videos[1].resolution.parameters = {}
	--ret.videos[1].resolution.parameters[1] = tvid
	--ret.videos[1].resolution.parameters[2] = vid

	ret.totalSet   = 1
	ret.updateSet  = 1
	ret.videos[1].info = {}
	return cjson.encode(ret)
end

--  获取节目集列表
function get_videolist(aid, vid, tvid, cid, name, pageNo, pageSize)
	if cid == '1' then
		return get_videolist_tv(tvid, vid, cid, name)
	end
	local page=1
	local quit=0
	local ret = {}
	local videos = {}
	local offset = 0
	ret.size = 0
	repeat
		local url = string.format('http://cache.video.qiyi.com/avlist/%s/%d/', aid, page)
		local text = kola.wget(url, false)

		text = kola.pcre("var videoListC=([\\s\\S]*)", text)
		if text == nil then
			return '{}'
		end

		local js = cjson.decode(text)
		if js.code ~= 'A00000' then
			return cjson.encode(ret)
		end

		ret.totalSet   = js.data.pm
		ret.updateSet  = js.data.pt
		if tonumber(pageSize) == 0 and tonumber(pageNo) then
			return cjson.encode(ret)
		end

		local size = tonumber(pageSize)
		local pos  = tonumber(pageNo) * size

		for k,v in ipairs(js.data.vlist) do
			if k + offset - 1 >= pos and ret.size < size then
				local video = {}
				video.cid         = js.data.cid
				video.pid         = js.data.aid
				video.vid         = v.vid
				video.playlistid  = v.id
				video.name        = v.vn
				video.showName    = v.vn
				if v.duration ~= nil then
					video.playLength  = tonumber(v.duration) * 60
				end
				video.order       = v.pd
				video.smallPicUrl = v.vpic
				video.resolution = {}
				video.resolution.script = 'qiyi'
				video.resolution['function'] = 'get_resolution'
				video.resolution.parameters = {}
				video.resolution.parameters[1] = v.id
				video.resolution.parameters[2] = v.vid

				video.info = {}
				ret.size = ret.size + 1
				videos[ret.size] = video
			end
			if ret.size >= size then
				quit = 1
				break
			end
		end
		page = page + 1
		offset = offset + js.data.pn
	until quit == 1 or offset == js.data.pt

	if #videos > 0 then
		ret.videos = videos
	end

--	print(cjson.encode(ret))
	return cjson.encode(ret)
end

function get_video_url(tvid, vid)
	local url = string.format('http://cache.video.qiyi.com/jp/tmts/%s/%s/', tvid, vid)
	local text = kola.wget(url, false)

	if not text then
		return '{}'
	end

	local js = cjson.decode(text)

	if js.code ~= 'A00000' then
		return ''
	end

	return js.data.m3u
end


-- 攻取节目视频清晰度
function get_resolution(tvid, vid)
	local function get_url(tvid, vid)
		res = {}
		res.script = 'qiyi'
		res['function'] = 'get_video_url'
		res.parameters = {}
		res.parameters[1] = tvid
		res.parameters[2] = vid

		return res
	end
	local function get_name(k)
		if k == 96 then
			return '流畅'
		elseif k == 1 then
			return '标清'
		elseif k == 2 then
			return '高清'
		elseif k == 3 then
			return '超清'
		elseif k == 4 then
			return '720P'
		elseif k == 5 then
			return '1080P'
		else
			return tostring(k)

		end
	end

	local url = string.format('http://cache.video.qiyi.com/jp/tmts/%s/%s/', tvid, vid)
	local text = kola.wget(url, false)

	if not text then
		return '{}'
	end

	local js = cjson.decode(text)

	if js.code ~= 'A00000' then
		return '{}'
	end

	local rx = {}
	for _,v in pairs(js.data.vidl) do
		local key = get_name(v.vd)
		if key ~= '' then
			rx[key] = get_url(tvid, v.vid)
			if js.data.vid == v.vid then
				rx[key].default = 1
			end
		end
	end

	return cjson.encode(rx)
end
