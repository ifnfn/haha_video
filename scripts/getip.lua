function get_info()
	local desc = ""
	local url = "http://g3.letv.cn/recommend"
	local text = kola.wget(url, false)
	if text ~= nil then
		local js = cjson.decode(text)
		desc = js.desc
		time = js.curtime
	end

	return desc, time
end

function getip_detail()
	local url = "http://iplocation.geo.qiyi.com/cityjson"
	local text = kola.wget(url, false)
	if text ~= nil then
		text = kola.pcre("var returnIpCity =(.*);", text)
		local js = cjson.decode(text)

		if js.code == "A00000" then
			return cjson.encode(js.data)
		end
	end

	return ""
end

function getip(url)
	local desc = ""
	local time = ""
	desc, time = get_info()

	return desc
end

function gettime()
	--a = io.popen("ls /etc")
	--print(a:read("*all"))
	--a.close()
	local url ="http://api.letv.com/time"
	local text = kola.wget(url, false)
	if text ~= nil then
		local js = cjson.decode(text)
		return tostring(js.stime)
	end

	return ''
end

function kola_main(url)
	return getip()
end
