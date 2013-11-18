function get_timestamp()
	local ret = kola.wget('http://epgsrv01.ucatv.com.cn/api/getUnixTimestamp')
	if ret ~= nil then
		local time_js = cjson.decode(ret)
		return  tonumber(time_js.time)
	end

	return 0
end

function kola_main(id)
	id = "178"
	local url = string.format('http://epgsrv01.ucatv.com.cn/api/getCDNByChannelId/%s', id)
	local text = kola.wget(url)
	if text ~= nil then
		print(text)
		--{"id":"163","channel_name":"CCTV1-Suma","customer_name":"xjyx","streams":{
		--	"500k_flv":{
		--		"videodatarate":"468","audiodatarate":"91","width":"640","height":"480","drm":"0",
		--		"cdnlist":["tvie01.ucatv.com.cn"]}
		--	}
		--}
		--http://tvie01.ucatv.com.cn/channels/xjyx/CCTV1-Suma/flv:500k_flv/live?1384488300960
		local data = cjson.decode(text)

		k = ''
		v = ''
		channel_name = data.channel_name
		table.foreach(data.streams, function(a, b) k=a v=b return true end)

		print(k, v.cdnlist[1])
		print(os.time())

		--table.foreach(data.result.datarates, function(a, b) k=a v=b return true end)
		--timestamp = tonumber(data.result.timestamp)
		--timestamp = math.floor(timestamp/1000) * 1000
		url = string.format('http://%s/channels/%s/%s/flv:%s/live?%s',
				v.cdnlist[1], data.customer_name, data.channel_name, k, get_timestamp())
		print(url)

		return url
	end

	return ""
--	return kola.pcre("(window.google.*)", text)
end


