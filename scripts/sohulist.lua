function get_album_set(playlistid)
	local url = 'http://hot.vrs.sohu.com/pl/isover_playlist?playlistid=' .. playlistid

	local text = kola.wget(url)

	if text == nil then
		return ""
	end

	local ret = {}
	local js = cjson.decode(text)
	ret.total      = js.totalSets
	ret.updateSet  = js.updateSets

	return ret
end

function kola_main(vid, playlistid, sohu_vid, pageNo, pageSize)
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

	local text = kola.wget(url)

	if text == nil then
		return ""
	end

	local js = cjson.decode(text)

	ret.full       = 0
	ret.playlistid = js.playlistid
	ret.total      = js.totalSet
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
		video.resolution.script = 'sohu_resolution'
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
