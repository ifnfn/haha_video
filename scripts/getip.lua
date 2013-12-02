function get_info()
	desc = ""
	url = "http://g3.letv.cn/recommend"
	local text = kola.wget(url)
	print(text)
	if text ~= nil then
		local js = cjson.decode(text)
		desc = js.desc
		time = js.curtime
	end

	return desc, time
end

function getip(url)
	desc, time = get_info()

	return desc
end

function gettime()
	url ="http://api.letv.com/time"
	local text = kola.wget(url)
	if text ~= nil then
		local js = cjson.decode(text)
		time = js.stime
	else
		time = os.time()
	end

	return tostring(time)
end

function kola_main(url)
	print(get_ip())

end
