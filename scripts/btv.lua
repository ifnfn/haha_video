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

-- 获取节目的EPG
function get_channel(vid)
	local url = string.format("http://itv.brtn.cn/live/getepgday/%s", vid)

	local text = kola.wget(url, false)


	if text == nil then
		return "{}"
	end
	local js = cjson.decode(text)

	local ret = {}
	if js then
		for _, dayepg in ipairs(js.data) do
			local time = kola.gettime()
			if time >= tonumber(dayepg[1].start_time) and time < tonumber(dayepg[#dayepg].end_time) then
				for k, ch in ipairs(dayepg) do
					ret[k] = {}
					start_time = tonumber(ch.start_time)
					end_time = tonumber(ch.end_time)
					ret[k].time_string = os.date("%H:%M", start_time)
					ret[k].time        = tonumber(start_time)
					ret[k].duration    = end_time - start_time
					ret[k].title       = ch.title
					--print(k, ret[k].time_string, ret[k].title)
				end
				break
			end
		end
	end

	return cjson.encode(ret)
end
