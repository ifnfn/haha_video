function get(vid, cid)
	res = {}
	res.script = 'sohu'
	res.parameters = {}
	res.parameters[1] = vid
	res.parameters[2] = tostring(cid)

	return res
end

function kola_main(vid, cid)
	local url = vid
	if string.find(vid, "http://") == nil then
		url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=' .. vid
	end

	local text = kola.wget(url)
	local js = cjson.decode(text).data

	local ret = {}
	ret['默认'] = get(vid, cid)
	ret['默认'].default = 1

	if js.highVid ~= nil then
		ret['高清'] = get(js.highVid, cid)
	end

	if js.norVid ~= nil then
		ret['标清'] = get(js.norVid, cid)
	end

	if js.oriVid ~= nil then
		ret['原画质'] = get(js.oriVid, cid)
	end

	if js.superVid ~= nil then
		ret['超清'] = get(js.superVid, cid)
	end

	return cjson.encode(ret)
end
