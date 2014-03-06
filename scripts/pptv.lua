--  获取节目集列表
function get_videolist(channel_id, pageNo, pageSize)
	--print(channel_id, pageNo, pageSize)
	local url = string.format('http://svcdn.pptv.com/show/v2/playlist.json?psize=%s&sid=%s&pindex=%s', pageSize, channel_id, pageNo)
	print(url)
	local text = kola.wget(url, false)

	if text == nil then
		return '{}'
	end

	js = cjson.decode(text)

	if js.err ~= 0 then
		return '{}'
	end

	local ret = {}
	ret.totalSet   = js.data.count
	ret.updateSet  = #js.data.videos
	ret.size       = 0
	if js.sid == nil then
		ret.totalSet = 1
		ret.updateSet = 1
	end
	if tonumber(pageSize) == 0 and tonumber(pageNo) then
		return cjson.encode(ret)
	end

	local videos = {}
	for k,v in ipairs(js.data.videos) do
		local video = {}
		video.vid         = v.url
		video.name        = v.title
		video.showName    = v.title
		video.order       = tonumber(v.eptitle)
		video.smallPicUrl = string.format("http://s%d.pplive.cn/v/cap/%s/h120.jpg", v.sn, v.url)
		video.playLength  = tonumber(v.duration)

		video.resolution  = {}
		video.resolution.script = 'pptv'
		video.resolution['function'] = 'get_resolution'
		video.resolution.parameters = {}
		video.resolution.parameters[1] = v.cid
		video.resolution.parameters[2] = v.sid

		ret.size = ret.size + 1
		videos[ret.size] = video
		if ret.size >= ret.updateSet then
			break
		end
	end

	if #videos > 0 then
		ret.videos = videos
	end

	print(cjson.encode(ret))
	return cjson.encode(ret)
end

function find(var, tag, key, value)
	-- check input
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

function get_resolution(cid, sid)
	local function video_url_script(qvid, url_prefix, segments, stream_id, default)
		res = {}
		if default then
			res.default = 1
		end
		res.script = 'pptv'
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

	local url = string.format('http://web-play.pptv.com/webplay3-0-%s.xml&version=4&type=web.fpp', channel_id)
	local text = kola.wget(url, false)

	ret = {}

	default = 'hd'
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

	return cjson.encode(ret)
end


function get_video_url(qvid, url_prefix, segments, stream_id)
	return "http:/ddddd"
end
