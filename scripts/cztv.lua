function kola_main(id)
	local url = string.format("http://api.cztv.com/api/getCDNByChannelId/%s?domain=api.cztv.com", id)
	local text = kola.wget(url)

	if text ~= nil then
		local data_obj = cjson.decode(text)
		if data_obj != nil then
			local k = ''
			local v = ''
			table.foreach(data_obj.result.datarates, function(a, b) k=a v=b return true end)
			timestamp = tonumber(data_obj.result.timestamp)
			timestamp = math.floor(timestamp / 1000) * 1000
			return string.format('http://%s/channels/%d/%s.flv/live?%s', v[1], 102, k, tostring(timestamp))
		end
	end

	return ""
end
