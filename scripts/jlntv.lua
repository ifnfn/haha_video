function kola_main(url)
	local text = kola.wget(url)
	if text ~= nil then
		text = kola.pcre("var playurl = '(.*)';", text)
		return string.sub(text, 1, -2)
	end

	return ""
end

function get_channel(vid)
	return ""
end
