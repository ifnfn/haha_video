function kola_main(vid, cid)
	local url = vid
	if string.sub(vid, "http://") == nil then
		url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=' .. vid
	end

	local text = kola.wget(url)

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

	ret.highVid       = js.highVid
	ret.norVid        = js.norVid
	ret.oriVid        = js.oriVid
	ret.superVid      = js.superVid
	ret.relativeId    = js.relativeId

	url = kola.getserver() .. "/video/getplayer?step=3&cid=" .. cid

	return kola.wpost(url, cjson.encode(ret))
end
