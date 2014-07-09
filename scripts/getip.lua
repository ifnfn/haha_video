function get_info()
	local desc = ""
	local url = "http://g3.letv.cn/recommend"
	local text = kola.wget(url, false)
	if text then
		local js = cjson.decode(text)
		desc = js.desc
		time = js.curtime
	end

	return desc, time
end

string.split = function(str, pattern)
	pattern = pattern or "[^%s]+"
	if pattern:len() == 0 then pattern = "[^%s]+" end
	local parts = {__index = table.insert}
	setmetatable(parts, parts)
	str:gsub(pattern, parts)
	setmetatable(parts, nil)
	parts.__index = nil

	return parts
end

function getip_detail_letv()
	desc, time = get_info()
	desc = string.gsub(desc, '-', ',')
	print(desc)
	parts = string.split(desc, "[^,%s]+")
	ret = {}
	ret.ip = js.data.ip
	for i,j in ipairs(parts) do
		if string.find(j, "中国") then
			ret.country = "中国大陆"
		elseif string.find(j, "省") then
			ret.province = string.gsub(j, "省", "")
		elseif string.find(j, "市") then
			ret.city = string.gsub(j, "市", "")
		elseif string.find(j, "电信") or string.find(j, "联通") then
			ret.isp = "中国" .. j
		end
	end
	return cjson.encode(ret)
end

function getip_detail()
	local url = "http://iplocation.geo.qiyi.com/cityjson"
	local text = kola.wget(url, false)
	if text then
		text = rex.match(text, "var returnIpCity =(.*);")
		local js = cjson.decode(text)

		if js.code == "A00000" and js.data.country ~= "" and js.data.province ~= "" then
			return cjson.encode(js.data)
		else
			return getip_detail_letv()
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
	if text then
		local js = cjson.decode(text)
		return tostring(js.stime)
	end

	return ''
end

function kola_main(url)
	print(chipid)
	return getip()
end
