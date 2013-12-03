function kola_main(url, id)
	local text = kola.wget(url)
	text = kola.pcre("streamer\' : '(.*)'\\+\\_info.source,", text)
	if text ~= nil then
		return string.sub(text, 1, -2) .. id
	end

	return ""
end
