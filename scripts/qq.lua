
local function curl_json(url)
	local text = kola.wget(url)
	text = rex.match(text, "QZOutput.*=({[\\s\\S]*});")
	if text ~= nil then
		return cjson.decode(text)
	end
end

--  获取节目集列表
function get_videolist(url, qvid, pageNo, pageSize)
	local function get_video( v )
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
		video.resolution.parameters[2] = v.url

		return video
	end
	--print(url, qvid, pageNo, pageSize)

	local js = curl_json(url)

	local offset = 0

	if not js.list then
		return '{}'
	end

	local ret = {}
	ret.totalSet   = 0
	ret.updateSet  = 0
	ret.size       = 0

	local videos = {}

	for k,v in ipairs(js.list) do
		if v.ID == qvid and #v.src_list.vsrcarray > 0 then
			vsrc = v.src_list.vsrcarray[1]
			for k,v in pairs(vsrc.playlist) do
				if type(k) == 'number' then
					ret.size = ret.size + 1
					videos[ret.size] = get_video(v)
				else
					for kk,vv in pairs(v) do
						ret.size = ret.size + 1
						videos[ret.size] = get_video(vv)
					end
				end

			end

			if v.BC ~= '综艺' then
				ret.totalSet   = vsrc.total_episode
				ret.updateSet  = vsrc.cnt
			else
				ret.totalSet   = #videos
				ret.updateSet  = #videos
			end
		end
	end

	if #videos > 0 and tonumber(pageSize) > 0 then
		ret.videos = {}
		local size = tonumber(pageSize)
		local pos  = tonumber(pageNo) * size
		for i=1,size do
			if i + pos > #videos then
				break
			end
			ret.videos[i] = videos[i+pos]
		end
	end

	--print(cjson.encode(ret))
	return cjson.encode(ret)
end

local function getKey(qvid)
	local url = string.format('http://vv.video.qq.com/getkey?vid=%s&filename=%s.flv&otype=json', qvid, qvid)

	local js = curl_json(url)

	if js ~= nil then
		return js.key
	else
		return ''
	end
end

-- 每一个片段都要生成一个 key, 并且生成完整地址
local function get_fix_segments(url_prefix, qvid, segments, stream_id)
	-- 获取所有视频段的 key
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
		local text = rex.match(v, "QZOutput.*=({[\\s\\S]*});")

		if string.find(text, 'key') then
			keys[k] = '?vkey=' .. cjson.decode(text).key
		else
			keys[k] = ''
			return nil
		end
	end

	-- 生成视频段
	local urls_list  = {}
	for i=1,seg_num do
		urls_list[i] = {}
		urls_list[i].time = segments[i].duration
		urls_list[i].url  = string.format("%s%s.%s.%d.mp4%s", url_prefix, qvid, name_prefix, i, keys[i])
	end

	return urls_list
end

-- 获取视频的直接播放地址
function get_video_url(url_prefix, qvid, segments, stream_id, default_url)
	local segments = cjson.decode(segments)
	if #segments == 0 then
		return default_url
	end

	local urls_list = get_fix_segments(url_prefix, qvid, segments, stream_id)

	if not urls_list then
		return default_url
	end

	--print(cjson.encode(urls_list))
	if #urls_list == 1 then
		return urls_list[1].url
	else
		url = kola.geturl("/video/getplayer?step=3")
		return kola.wpost(url, cjson.encode(urls_list))
	end
end

function get_resolution(qvid, video_url)
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

	-- 有些 qvid 并没有视频，需要从网页中提取（如综艺）
	local function get_qvid(qvid)
		local js = nil
		while qvid do
			local url = string.format('http://vv.video.qq.com/getinfo?vids=%s&otype=json&defaultfmt=mp4', qvid)
			js = curl_json(url)

			if js == nil or js.em == 61 then
				local text = kola.wget(video_url, false)
				qvid = rex.match(text, 'vid:"(.*?)"')
				js = nil
			else
				break
			end
		end

		return qvid, js
	end

	local function video_url_script(js, qvid, segments, stream_id, default)
		local function get_default_url(js)
			local fn     = js.vl.vi[1].fn
			local vkey   = js.vl.vi[1].fvkey
			local level  = js.vl.vi[1].level
			local br     = js.vl.vi[1].br
			local prefix = get_url_prefix(js.vl.vi[1].ul.ui)

			return string.format('%s%s?vkey=%s&br=%s&platform=2&fmt=mp4&level=%s&sdtfrom=v4010', prefix, fn, vkey, br, level)
		end

		local res = {}
		if default then
			res.default = 1
		end

		res.script = 'qq'
		res['function'] = 'get_video_url'
		res.parameters = {}
		res.parameters[1] = get_url_prefix(js.vl.vi[1].ul.ui)
		res.parameters[2] = qvid
		res.parameters[3] = cjson.encode(segments)
		res.parameters[4] = stream_id
		res.parameters[5] = get_default_url(js)

		if default then
			default = false
		end
		return res, default
	end

	local ret = {}
	local js = nil

	qvid, js = get_qvid(qvid)

	if not js then
		return '{}'
	end

	local stream_type = js.fl.fi
	local format_num  = #stream_type
	local segments = {}
	cl = js.vl.vi[1].cl
	if cl.fc > 0 then
		for k,v in pairs(js.vl.vi[1].cl.ci) do
			segments[k] = {}
			segments[k].duration = tonumber(v.cd)
			segments[k].index    = v.idx
			segments[k].size     = v.cs
		end
	end

	if format_num == 0 then
		local url_prefix  = get_url_prefix(js.vl.vi[1].ul.ui)
		ret['高清'] = strint("%s%s.flv?vkey=%s", url_prefix, qvid, getkey(qvid))
		ret['高清'].default = 1
	else
		local Default = true
		for j=1,format_num do
			local definition = stream_type[j].name
			local stream_id  = stream_type[j].id

			if definition == 'hd' then
				ret['高清'], Default = video_url_script(js, qvid, segments, stream_id, Default)
			elseif definition == 'sd' then
				ret['标清'], Default = video_url_script(js, qvid, segments, stream_id, Default)
			elseif definition == 'shd' then
				ret['超清'], Default = video_url_script(js, qvid, segments, stream_id, Default)
			elseif definition == 'fhd' then
				ret['原画质'], Default = video_url_script(js, qvid, segments, stream_id, Default)
			else
				ret['默认'], Default = video_url_script(js, qvid, segments, stream_id, Default)
			end
		end
	end

	return cjson.encode(ret)
end
