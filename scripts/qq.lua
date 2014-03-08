local function GetData(url)
	local text = kola.wget(url, false)
	text = kola.pcre("QZOutput.*=({[\\s\\S]*});", text)

	if text == nil then
		return '{}'
	end

	return cjson.decode(text)
end

local function getKey(qvid)
	local url = string.format('http://vv.video.qq.com/getkey?vid=%s&filename=%s.flv&otype=json', qvid, qvid)

	local js = GetData(url)

	if js ~= nil then
		return js.key
	else
		return ''
	end
end

--  获取节目集列表
function get_videolist(url, qvid, pageNo, pageSize)
	local ret = {}

	local js = GetData(url)

	local videos = {}
	local offset = 0

	for k,v in ipairs(js.list) do
		if v.ID == qvid then
			if #v.src_list.vsrcarray > 0 then
				vsrc = v.src_list.vsrcarray[1]
				ret.totalSet   = vsrc.total_episode
				ret.updateSet  = vsrc.cnt
				ret.size       = 0

				if tonumber(pageSize) == 0 and tonumber(pageNo) then
					return cjson.encode(ret)
				end

				local size = tonumber(pageSize)
				local pos  = tonumber(pageNo) * size

				for k,v in ipairs(vsrc.playlist) do
					if k + offset - 1 >= pos and ret.size < size then
						local video = {}
						video.vid         = v.id
						video.name        = v.title
						video.showName    = v.title
						video.order       = tonumber(v.episode_number)
						video.smallPicUrl = v.pic
						video.resolution  = {}
						video.resolution.script = 'qq'
						video.resolution['function'] = 'get_resolution'
						video.resolution.parameters = {}
						video.resolution.parameters[1] = v.id

						ret.size = ret.size + 1
						videos[ret.size] = video
					end
					if ret.size >= size then
						quit = 1
						break
					end
				end
			end
		end
	end

	if #videos > 0 then
		ret.videos = videos
	end

	--print(cjson.encode(ret))
	return cjson.encode(ret)
end

function get_video_url(qvid, url_prefix, segments, stream_id)
	-- 获取所有视频段的 key
	segments = cjson.decode(segments)
	local name_prefix = 'p' .. string.sub(tostring(stream_id), 3)
	local seg_num     = #segments
	local key_urls    = {}         -- 用于多线程攻取 keys
	local keys        = {}         -- 视频段key

	for i=1,seg_num do
		key_urls[i] = string.format("http://vv.video.qq.com/getkey?vid=%s&format=%d&filename=%s.%s.%d.mp4&otype=json",
										qvid, stream_id, qvid, name_prefix, i)
	end
	local keys = kola.mwget(key_urls)
	for k,v in pairs(keys) do
		local text = kola.pcre("QZOutput.*=({[\\s\\S]*});", v)

		if text == nil then keys[k] = ''else keys[k] = cjson.decode(text).key end
	end

	-- 生成视频段
	local urls_list  = {}
	for i=1,seg_num do
		urls_list[i] = {}
		urls_list[i].time = segments[i].duration
		urls_list[i].url  = string.format("%s%s.%s.%d.mp4?vkey=%s", url_prefix, qvid, name_prefix, i, keys[i])
	end

	--print(cjson.encode(urls_list))
	if #urls_list == 1 then
		return urls_list[1].url
	else
		url = kola.getserver() .. "/video/getplayer?step=3"
		return kola.wpost(url, cjson.encode(urls_list))
	end
end

function get_resolution(qvid)
	local function video_url_script(qvid, url_prefix, segments, stream_id, default)
		res = {}
		if default then
			res.default = 1
		end
		res.script = 'qq'
		res['function'] = 'get_video_url'
		res.parameters = {}
		res.parameters[1] = url_prefix
		res.parameters[2] = qvid
		res.parameters[3] = cjson.encode(segments)
		res.parameters[4] = stream_id

		if default then
			default = false
		end
		return res, default
	end

	local function get_url_prefix(ui)
		if #ui == 0 then
			return ''
		end
		local url = ui[1].url
		local level = 0
		for k,v in pairs(ui) do
			local tmp_level = 0

			if string.find(v.url, 'videocdn.qq.com') then
				if level < 9 then tmp_level = 9 end
			elseif string.find(v.url, 'video.qq.com') then
				if level < 8 then tmp_level = 8 end
			elseif string.find(v.url, 'tc.qq.com') then
				if level < 7 then tmp_level = 7 end
			else
				tmp_level = 1
			end

			if tmp_level > level then
				level = tmp_level
				url = v.url
			end
		end

		return url
	end

	local ret = {}
	local url = string.format('http://vv.video.qq.com/getinfo?vids=%s&otype=json', qvid)
	local js = GetData(url)

	if js == nil then
		return '{}'
	end

	local url_prefix = get_url_prefix(js.vl.vi[1].ul.ui)
	--local url_prefix  = js.vl.vi[1].ul.ui[1].url
	local stream_type = js.fl.fi
	local format_num  = #stream_type
	local segments = {}
	for k,v in pairs(js.vl.vi[1].cl.ci) do
		segments[k] = {}
		segments[k].duration = tonumber(v.cd)
		segments[k].index    = v.idx
		segments[k].size     = v.cs
	end

	if format_num == 0 then
		ret['高清'] = strint("%s%s.flv?vkey=%s", url_prefix, qvid, getkey(qvid))
		ret['高清'].default = 1
	else
		local Default = true
		for j=1,format_num,1 do
			local definition = stream_type[j].name
			local stream_id  = stream_type[j].id

			if definition == 'hd' then
				ret['高清'], Default = video_url_script(url_prefix, qvid, segments, stream_id, Default)
			end
			if definition == 'sd' then
				ret['标清'], Default = video_url_script(url_prefix, qvid, segments, stream_id, Default)
			end
			if definition == 'shd' then
				ret['超清'], Default = video_url_script(url_prefix, qvid, segments, stream_id, Default)
			end
			if definition == 'fhd' then
				ret['原画质'], Default = video_url_script(url_prefix, qvid, segments, stream_id, Default)
			end
		end
	end

	return cjson.encode(ret)
end
