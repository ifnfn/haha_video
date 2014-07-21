local function curl_json(url, regular)
	local text = kola.wget(url, false)
	if text then
		if regular and regular ~= '' then
			text = rex.match(text, regular)
		end
		if text and text ~= '' then
			return cjson.decode(text)
		end
	end
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

local function get_ip_sina()
	local ret = {}
	local js = curl_json('http://int.dpool.sina.com.cn/iplookup/iplookup.php?format=js', '({.*?})')
	if js then
		ret.ip = ''
		ret.country  = js.country
		ret.province = js.province
		ret.city     = js.city
		ret.isp      = js.isp
	end
	return ret
end

local function get_ip_taobao()
	local ret = {}
	local js = curl_json('http://ip.taobao.com/service/getIpInfo.php?ip=myip')
	if js then
		ret.ip       = js.data.ip
		ret.country  = js.data.country
		ret.province = js.data.region
		ret.city     = js.data.city
		ret.isp      = js.data.isp
	end
	return ret
end

local function getip_qiyi()
	local ret = {}
	local js = curl_json('http://iplocation.geo.qiyi.com/cityjson', "var returnIpCity =(.*?);")
	if js and js.code == 'A00000' and js.data.country ~= '' and js.data.province ~= '' then
		ret = js.data
	end
	return ret
end

local function get_ip_letv()
	local ret = {}
	local js = curl_json("http://g3.letv.cn/recommend")
	if js then
		ret.ip = js.host
		local desc = string.gsub(js.desc, '-', ',')
		parts = string.split(desc, "[^,%s]+")
		for i,j in ipairs(parts) do
			if string.find(j, "中国") then
				ret.country = "中国大陆"
			elseif string.find(j, "省") then
				ret.province = j
			elseif string.find(j, "市") then
				ret.city = j
			elseif string.find(j, "电信") or string.find(j, "联通") then
				ret.isp = "中国" .. j
			end
		end
	end
	return ret
end

function getip_detail()
	local func_maps = {
		get_ip_taobao,
		get_ip_letv,
		getip_qiyi,
		get_ip_sina,
	}

	local ret = {}

	for k,func in pairs(func_maps) do
		ret = func()
		if _G.next(ret) ~= nil then
			if ret.country and ret.province then
				if string.find(ret.country, "中国") then
					ret.country = "中国大陆"
				end
				ret.province = string.gsub(ret.province, '省', '')
				ret.province = string.gsub(ret.province, '自治区', '')
				ret.province = string.gsub(ret.province, '维吾尔', '')
				ret.province = string.gsub(ret.province, '壮族', '')
				ret.province = string.gsub(ret.province, '回族', '')

				if ret.city then
					ret.city = string.gsub(ret.city, '市', '')
				end

				return cjson.encode(ret)
			end
		end
	end
	return ''
end

function gettime()
	local js = curl_json('http://api.letv.com/time')
	if js then
		return tostring(js.stime)
	end
	return '0'
end
