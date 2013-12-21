function kola_main(pid, pageNo, pageSize)
	local ret = {}
	--local url = string.format("http://live.gslb.letv.com/gslb?stream_id=%s&ext=m3u8&sign=live_tv&format=1", url)
	--print(url)
	
	local url = string.format('http://app.letv.com/ajax/getFocusVideo.php?p=1&top=%d&max=%s&pid=%s',
			tonumber(pageNo) * tonumber(pageSize), pageSize, pid)

	local url = string.format('http://app.letv.com/ajax/getFocusVideo.php?p=1&top=0&max=1000&pid=%s',
			pid)
	local text = kola.wget(url)

	text = string.sub(text, 2, -2)
	
	ret.size = 0
	local videos = {}
	local js = cjson.decode(text)
	for k,v in ipairs(js) do
		print(v.vid, v.title)
		local video = {}

		video.cid         = js.cid
		video.pid         = pid
		video.vid         = tostring(v.vid)
		video.playlistid  = pid
		video.name        = v.title
		video.showName    = v.title
		if v.duration ~= nil then
			--video.playLength  = tonumber(v.duration) * 60
		end
		video.order       = v.key
		video.smallPicUrl = v.pic
		video.largePicUrl = v.pic
		video.resolution = {}
		video.resolution.script = 'letv_resolution'
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

	print(cjson.encode(ret))
	return cjson.encode(ret)
end

