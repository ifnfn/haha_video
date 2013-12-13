function kola_main(url)
	local text = kola.wget(url)
	if text ~= nil then
		return kola.pcre("var playurl = '(.*)';", text)
	end

	return ""
end

function get_channel(vid)
	return ""
end
