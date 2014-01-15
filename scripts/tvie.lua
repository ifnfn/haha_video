function get_timestamp()
	local ret = kola.wget('http://epgsrv01.ucatv.com.cn/api/getUnixTimestamp', false)
	if ret ~= nil then
		local time_js = cjson.decode(ret)
		return  tonumber(time_js.time)
	end

	return 0
end

function kola_main(url)
	local text = kola.wget(url)

	if text ~= nil then
		local data_obj = cjson.decode(text)
		if type(data_obj.result) == "table" then
			if (data_obj ~= nil) and type(data_obj.result.datarates) == "table" then
				local k = ''
				local v = ''
				local video_url = ''
				local timestamp = tonumber(data_obj.result.timestamp)
				timestamp = math.floor(timestamp / 1000) * 1000

				for k,v in pairs(data_obj.result.datarates) do
					video_url = string.format('http://%s/channels/%d/%s.flv/live?%s', v[1], 102, k, tostring(timestamp))
					break
				end

				return video_url
			end
		elseif type(data_obj.streams) == "table" then
			--{
			--	"id":"179",
			--	"channel_name":"JiangSu-HD-Envivio",
			--	"customer_name":"xjyx",
			--	"streams":{
			--		"JS_HD_Envivio":{
			--			"videodatarate":"782",
			--			"audiodatarate":"31",
			--			"width":"720",
			--			"height":"576",
			--			"drm":"0",
			--			"cdnlist":["tvie01.ucatv.com.cn"]
			--		}
			--	}
			--}

			local channel_name = data_obj['channel_name']
			local customer_name = data_obj['customer_name']
			local streams = data_obj['streams']
			local video_url = ''
			for k,v in pairs(streams) do
				video_url = string.format('http://%s/channels/%s/%s/flv:%s/live?%d',
					v.cdnlist[1], customer_name, channel_name, k, get_timestamp())
				break
			end

			return video_url
		end
	end

	return ""
end

function get_channel(vid)
	local url = string.format("%s/0/%d", vid, kola.gettime())

	local ret = {}
	text = kola.wget(url)
	if text ~= nil then
		local d = os.date("*t", kola.gettime())
		local prev_d = d
		local js = cjson.decode(text)
		for k,v in ipairs(js.result[1]) do
			ret[k] = {}
			s = tonumber(v.start_time)
			ret[k].time_string = os.date("%H:%M", s)
			ret[k].time = s
			ret[k].duration = tonumber(v.end_time) - s
			ret[k].title = v.name
			--print(k, ret[k].time_string, ret[k].duration, ret[k].title)
		end
	end

	return cjson.encode(ret)
end
