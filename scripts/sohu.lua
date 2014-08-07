-- 获取播放地址
function get_video_url(vid, cid)
	--vid = '1623625'
	local url = vid
	if string.find(vid, "http://") == nil then
		url = string.format('http://hot.vrs.sohu.com/vrs_flash.action?vid=%s', vid)
	end

	local text = kola.wget(url, false)
	if text == nil then
		return ""
	end

	local ret = {}
	local js = cjson.decode(text)
	local data     = js.data
	local host     = js['allot']
	local prot     = js['prot']
	ret.vid        = js['id']

	ret.sets = {}
	local urls = {}
	for i, tfile in pairs(data.clipsURL) do
		local x = {}
		x.duration  = data.clipsDuration[i]
		x.size      = data.clipsBytes[i]
		x.new       = data.su[i]
		x.url       = ''
		ret.sets[i] = x
		urls[i] = string.format('http://%s/?prot=%s&file=%s&new=%s', host, prot, tfile, x.new)
	end

	local x = kola.mwget(urls, false)
	if x then
		for i, url in ipairs(x) do
			ret.sets[i].url = url
		end
	end

	ret.totalBytes    = data.totalBytes
	ret.totalBlocks   = data.totalBlocks
	ret.totalDuration = data.totalDuration
	ret.clipsDuration = data.chipsDuration
	ret.width         = data.width
	ret.height        = data.height
	ret.fps           = data.fps
	ret.scap          = data.scap

	ret.highVid       = data.highVid
	ret.norVid        = data.norVid
	ret.oriVid        = data.oriVid
	ret.superVid      = data.superVid
	ret.relativeId    = data.relativeId

	url = kola.geturl("/video/getplayer?step=3&cid=" .. cid)

	return kola.wpost(url, cjson.encode(ret))
end

-- 攻取节目视频清晰度
function get_resolution(vid, cid)
	local function get(vid, cid)
		res = {}
		res.script = 'sohu'
		res['function'] = 'get_video_url'
		res.parameters = {}
		res.parameters[1] = vid
		res.parameters[2] = tostring(cid)

		return res
	end

	local url = vid
	if string.find(vid, "http://") == nil then
		url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=' .. vid
	end

	local text = kola.wget(url, false)
	if text == nil then
		return '{}'
	end
	local js = cjson.decode(text).data

	local ret = {}
	ret['默认'] = get(vid, cid)
	ret['默认'].default = 1

	if js.highVid ~= nil and js.highVid > 0 then
		ret['高清'] = get(js.highVid, cid)
	end

	if js.norVid ~= nil and js.norVid > 0 then
		ret['标清'] = get(js.norVid, cid)
	end

	if js.oriVid ~= nil and js.oriVid > 0 then
		ret['原画质'] = get(js.oriVid, cid)
	end

	if js.superVid ~= nil and js.superVid > 0 then
		ret['超清'] = get(js.superVid, cid)
	end

	return cjson.encode(ret)
end

local function get_album_set(playlistid)
	local url = 'http://hot.vrs.sohu.com/pl/isover_playlist?playlistid=' .. playlistid

	local text = kola.wget(url, false)

	if text == nil then
		return ""
	end

	local ret = {}
	local js = cjson.decode(text)
	ret.totalSet   = js.totalSets
	ret.updateSet  = js.updateSets

	return ret
end

--  获取节目集列表
function get_videolist(vid, playlistid, sohu_vid, pageNo, pageSize)
	local ret = {}

	if tonumber(pageNo) == 0 and tonumber(pageSize) == 0 then
		ret = get_album_set(playlistid)
		return cjson.encode(ret)
	end

	local url = vid
	if string.find(vid, "http://") == nil then
		url = string.format('http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&pagenum=%d&pagesize=%s&playlistid=%s',
			tonumber(pageNo) + 1, pageSize, playlistid)
	end

	local text = kola.wget(url, false)

	if text == nil then
		return ""
	end

	local js = cjson.decode(text)

	ret.full       = 0
	ret.playlistid = js.playlistid
	ret.totalSet   = js.totalSet
	ret.updateSet  = js.updateSet
	ret.page       = js.currentPage
	ret.size       = 0

	local videos = {}

	for i, v in pairs(js.videos) do
		local video = {}
		video.cid         = js.cid
		video.pid         = vid
		video.vid         = tostring(v.vid)
		video.playlistid  = js.playlistid
		video.name        = v.name
		video.showName    = v.ShowName
		video.playLength  = v.playLength
		video.publishTime = v.publishTime
		video.order       = v.order
		video.smallPicUrl = v.smallPicUrl
		video.largePicUrl = v.largePicUrl
		video.resolution = {}
		video.resolution.script = 'sohu'
		video.resolution['function'] = 'get_resolution'
		video.resolution.parameters = {}
		video.resolution.parameters[1] = video.vid
		video.resolution.parameters[2] = tostring(video.cid)

		video.info = {}
		videos[i] = video
		ret.size = ret.size + 1
	end

	if #videos > 0 then
		ret.videos = videos
	end

	--print(cjson.encode(ret))
	return cjson.encode(ret)
end

function get_videolist_bak(vid, playlistid, sohu_vid, pageNo, pageSize)
	local cache_url = string.format('/video/cache_list_%s-%s-%s-%s-%s?time=600', vid, playlistid, sohu_vid, pageNo, pageSize)
	cache_url = kola.geturl(cache_url)

	local value = kola.wget(cache_url)
	if not value then
		value = get_videolist2(vid, playlistid, sohu_vid, pageNo, pageSize)
		kola.wpost(cache_url, ret)
	else
		print("in cached.", cache_url)
	end

	return value
end
