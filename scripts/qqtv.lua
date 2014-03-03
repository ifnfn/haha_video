function kola_main(url)
	local text = kola.wget(url, false)

	if text ~= nil then
		text = kola.pcre('location url="(.*?)"', text)
		return string.sub(text, 1, -2)
	end

	return ""
end

function get_channel(vid)
	if text == nil then
		return '{}'
	end
end
