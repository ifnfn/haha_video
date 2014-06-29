function get_resolution(vid)
	local function get(vid, type)
		local url = string.format('http://his.cdn.brtn.cn/approve/live?channel=%s&type=%s', vid, type)
		res = {}
		res['text'] = url

		return res
	end

	local ret = {}
	local url = string.format('http://his.cdn.brtn.cn/approve/live?channel=%s&type=ios', vid)

	local text = kola.wget(url, false)
	
	if text then
		ret['默认'] = get(vid, 'iptv')
		ret['默认'].default = 1

		if string.find(text, 'iphone') ~= nil then
			ret['标清'] = get(vid, 'iphone')
		end
		if string.find(text, 'ipad') ~= nil then
			ret['高清'] = get(vid, 'ipad')
		end
		if string.find(text, 'iptv') ~= nil then
			ret['超清'] = get(vid, 'iptv')
		end
	end

	return cjson.encode(ret)
end
