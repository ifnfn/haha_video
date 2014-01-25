function kola_main(vid, a)
	local url = string.format("http://vcbox.cntv.chinacache.net/cache/hds%s.f4m", vid)
	local text = kola.wget(url)
	if text ~= nil then
		--print("Found:", url)
		return ''
	end
	url = string.format('http://vcbox.cntv.chinacache.net/cache/%s_/seg1/index.f4m', a)
	local text = kola.wget(url)
	if text ~= nil then
		--print("Found:", url)
		return ''
	end

	print("video", vid, a)
	return ''
end

function get_channel(vid)
	return ""
end
