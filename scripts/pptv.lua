local function find(var, tag, key, value)
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

--  获取节目集列表
function get_videolist(cid, channel_id, pageNo, pageSize)
	--print(channel_id, pageNo, pageSize)
	--local url = string.format('http://svcdn.pptv.com/show/v2/playlist.json?psize=%s&sid=%s&pindex=%s', pageSize, channel_id, pageNo)
	local url = ''

	if cid == '1' then -- 电影
		url = string.format('http://svcdn.pptv.com/show/v1/playlist.json?psize=10000&cid=%s',channel_id)
	else
		url = string.format('http://svcdn.pptv.com/show/v2/playlist.json?psize=%s&sid=%s&pindex=%s', pageSize, channel_id, pageNo)
	end
	local text = kola.wget(url, false)

	print(url)
	if text == nil then
		return '{}'
	end

	js = cjson.decode(text)

	if js.err ~= 0 then
		return '{}'
	end

	local ret = {}
	ret.totalSet  = js.data.count
	ret.updateSet = #js.data.videos
	ret.size      = 0
	if js.sid == nil then
		ret.totalSet = 1
		ret.updateSet = 1
	end
	if tonumber(pageSize) == 0 then
		return cjson.encode(ret)
	end

	local videos = {}
	for k,v in ipairs(js.data.videos) do
		local video = {}
		if tonumber(v.cid) == tonumber(channel_id) then
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
			video.resolution.parameters[1] = channel_id

			ret.size = ret.size + 1
			videos[ret.size] = video
			if ret.size >= ret.updateSet then
				break
			end
		end
	end

	if #videos > 0 then
		ret.videos = videos
	end

	--print(cjson.encode(ret))
	return cjson.encode(ret)
end

function get_resolution(cid)
	local function video_url_script(cid, ft, rid, default)
		res = {}
		if default then
			res.default = 1
		end
		res.script = 'pptv'
		res['function'] = 'get_video_url'
		res.parameters = {}
		res.parameters[1] = cid
		res.parameters[2] = ft
		res.parameters[3] = rid

		if default then
			default = false
		end
		return res, default
	end

	local url = string.format('http://web-play.pptv.com/webplay3-0-%s.xml&version=4&type=web.fpp', cid)
	local text = kola.wget(url, false)

	ret = {}

	local x = xml.eval(text)
	local v = find(x, "file")
	for a, b in pairs(v) do
		if b.vip == "0" then
			--print(a,b.bitrate, b.rid, b.vip)
			if b.width < "720" then
				ret['标清'], Default = video_url_script(cid, b.ft, b.rid, Default)
			end
			if b.width == "720" and b.width < "720" then
				ret['高清'], Default = video_url_script(cid, b.ft, b.rid, Default)
			end
			if b.width == "1280" and b.width < "720" then
				ret['超清'], Default = video_url_script(cid, b.ft, b.rid, Default)
			end
			if b.width >= "1920" then
				ret['原画质'], Default = video_url_script(cid, b.ft, b.rid, Default)
			end
		end
	end

	return cjson.encode(ret)
end

function get_video_url(cid, ft, rid)
	local url = string.format('http://web-play.pptv.com/webplay3-0-%s.xml&version=4&type=web.fpp', cid)
	local text = kola.wget(url, false)

	local x = xml.eval(text)
	local v = find(x, "root")

	local segments = {}
	local sh=''
	local key=''
	local k=''
	for a, b in ipairs(v) do
		if b[0] == 'dt' and b.ft == ft then

			for i,j in ipairs(b) do
				if j[0] == 'sh' then
					sh = j[1]
				elseif j[0] == 'id' then
					key = j[1]
				elseif j[0] == 'key' then
					k = j[1]
				end
			end
		elseif b[0] == 'dragdata' and b.ft == ft then
			local idx = 1
			for _,sgm in ipairs(b) do
				if sgm[0] == 'sgm' then
					segments[idx] = {}
					segments[idx].url = string.format('%s/%s', sgm.no, rid)
					segments[idx].time = tonumber(sgm.dur)
					idx = idx + 1
				end
			end
		end
	end

	if #segments > 1 then
		for i, sgm in ipairs(segments) do
			segments[i].url = string.format('http://%s/%s?k=%s&type=web.fpp', sh, segments[i].url, k)
		end
		local url = kola.geturl("/video/getplayer?step=3")

		return kola.wpost(url, cjson.encode(segments))
	elseif #segments == 1 then
		return string.format('http://%s/%s?k=%s&type=web.fpp', sh, segments[0].url, k)
	end

	return ''
end
