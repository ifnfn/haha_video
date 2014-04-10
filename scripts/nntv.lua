-- 获取节目的EPG
function get_channel(vid)
	--vid = tonumber(vid)
	local url = 'http://www.nntv.cn/epg/zhtv_epg.json'
	local ret = {}

	text = kola.wget(url, false)
	if text then
		text = kola.pcre("jsonp_program\\((.*)\\)", text)
		local js = cjson.decode(text)

		local k = 1
		for id, ch in ipairs(js) do
		    -- "name": "帮得行动（重播）_",
		    -- "start_time": "2014-01-24 00:17:00",
		    -- "end_time": "2014-01-24 07:00:00"
			if ch.column == vid then
				start_time = kola.date(ch.start_time)
				end_time = kola.date(ch.end_time)
				ret[k] = {}
				--ret[k].title = string.gsub(ch.name, "_$", "")
				ret[k].title       = string.gsub(ch.name, "^%s*(.-)%s*_*$", "%1")
				ret[k].time_string = os.date("%H:%M", start_time)
				ret[k].time        = start_time
				ret[k].duration    = end_time - start_time
				k = k + 1
			end
		end
	end

	--print(cjson.encode(ret))
	return cjson.encode(ret)
end
