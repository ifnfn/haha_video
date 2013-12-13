function kola_main(vid, cid)
	--local url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=' .. vid
	local text = kola.wget(url)

	if text == nil then
		return ""
	end

	local ret = {}
	local data_obj = cjson.decode(text)
	if data_obj ~= nil then
		local data = data_obj.data
		if data == nil then
			return ret
		end

		local host = data_obj['allot']
		local prot = data_obj['prot']
		ret.vid    = data_obj['id']

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

		x = kola.mwget(urls)
		for i, url in pairs(x) do
			ret.sets[i].url = url
		end

		ret.totalBytes    = data.totalBytes
		ret.totalBlocks   = data.totalBlocks
		ret.totalDuration = data.totalDuration
		ret.clipsDuration = data.chipsDuration
		ret.width         = data.width
		ret.height        = data.height
		ret.fps           = data.fps
		ret.scap          = data.scap

		ret.highVid    = data_obj.highVid
		ret.norVid     = data_obj.norVid
		ret.oriVid     = data_obj.oriVid
		ret.superVid   = data_obj.superVid
		ret.relativeId = data_obj.relativeId
	end

	url = kola.getserver() .. "/video/getplayer?step=3&cid=" .. cid

	return kola.wpost(url, cjson.encode(ret))
end
