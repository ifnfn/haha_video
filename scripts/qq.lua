local function GetData(url)
	local text = kola.wget(url, false)
	text = kola.pcre("QZOutput.*=({[\\s\\S]*});", text)

	if text == nil then
		return '{}'
	end

	--print(text)
	return cjson.decode(text)
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
					print(k, v)
					if k + offset - 1 >= pos and ret.size < size then
						local video = {}
						video.vid         = v.id
						video.name        = v.title
						video.showName    = v.title
						video.order       = tonumber(v.episode_number)
						video.smallPicUrl = v.pic
						video.resolution = {}
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

local function getKey(qvid)
	local url = string.format('http://vv.video.qq.com/getkey?vid=%s&filename=%s.flv&otype=json', qvid, qvid)

	local js = GetData(url)

	if js ~= nil then
		return js.key
	else
		return ''
	end
end

function get_resolution(qvid)
	local ret = {}
	local url = string.format('http://vv.video.qq.com/getinfo?vids=%s&otype=json', qvid)
	print(url)
	local js = GetData(url)

	local url_prefix = js.vl.vi[1].ul.ui[1].url
	local seg_num =  js.vl.vi[1].cl.fc
	local stream_type = js.fl.fi
	local format_num = #stream_type

	if format_num == 0 then
		ret['hd'] = strint("%s%s.flv?vkey=%s", url_prefix, qvid, getkey(qvid))
	else
		for j=1,format_num,1 do
			local definition = stream_type[2 + j]['name']
			local stream_id  = stream_type[2 + j]['id']
			local urls_list  = {}
			local name_prefix = 'p' .. string.sub(stream_id, 3)

			for i=1,seg_num do
				local filename = string.format("%s.%s.%d.mp4", qvid, name_prefix, i)
				local VIDOE_URL = string.format("http://vv.video.qq.com/getkey?vid=%s&format=%d&filename=%s&otype=json", qvid, stream_id, filename)
				local js = GetData(VIDOE_URL)

				if js ~= nil then
					local video_url = string.format("%s%s?vkey=%s", url_prefix, filename, js.key)
					print(video_url)

					urls_list[i] = video_url
				end
			end

			ret[definition] = urls_list
		end
	end

	print(cjson.encode(ret))
	return cjson.encode(ret)
end
