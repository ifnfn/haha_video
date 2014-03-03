--function get_timestamp()
--	return kola.gettime()
--end

function kola_main(url)
	local text = kola.wget(url, false)

	if text ~= nil and text ~= "TVie Exception: No streams." then
		local d = os.date("*t", kola.gettime())
		local data_obj = cjson.decode(text)
		if data_obj == nil then
			return ''
		end
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
			local channel_name = data_obj['channel_name']
			local customer_name = data_obj['customer_name']
			local streams = data_obj['streams']
			local video_url = ''
			for k,v in pairs(streams) do
				--video_url = string.format('http://%s/channels/%s/%s/flv:%s/live?%d',
				--	v.cdnlist[1], customer_name, channel_name, k, get_timestamp())
				video_url = string.format('http://%s/channels/%s/%s/flv:%s/live',
					v.cdnlist[1], customer_name, channel_name, k)
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
	text = kola.wget(url, false)
	if text ~= nil and text ~= "TVie Exception: No streams." then
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
		end
	end

	return cjson.encode(ret)
end
