function kola_main(url, id)
	local text = kola.wget(url, false)
	if text ~= nil then
		text = kola.pcre("file: '(.*)'", text)
		return string.sub(text, 1, -2) .. id
	end

	return ""
end

function get_channel(vid)
	local ret = {}
	local url = "http://www.dhtv.cn/api/programs/?ac=get&_channel=" .. vid 
	local text = kola.wget(url, false)

	if text == nil then
		return '{}'
	end
	text = string.sub(text, 2, #text - 1)
	if text == nil then
		return '{}'
	end
	text = string.sub(text, 2, #text - 1)

	local d = os.date("*t", kola.gettime())
	local prev_d = d
	local js = cjson.decode(text)
	for k,v in ipairs(js.data) do
		t = v.start
		d.hour=tonumber(string.sub(t, 1, string.find(t, ":") - 1))
		d.min=tonumber(string.sub(t, string.find(t, ":") + 1))
		d.sec= 0
		ret[k] = {}
		ret[k].time_string = string.format('')
		ret[k].time = os.time(d)
		ret[k].duration = 0
		ret[k].title = v.name
		if k > 1 then
			ret[k-1].duration = os.difftime(ret[k].time, ret[k-1].time)
		end
		--print(k, ret[k].time_string, ret[k].duration, ret[k].title)
	end

	return cjson.encode(ret)
end
