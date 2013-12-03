function kola_main(url)
	--print(url)
	text = kola.wget(url)
	if text ~= nil then
		local js = cjson.decode(text)
		if js ~= nil then
			url = js.location
		else
			url = ""
		end

	end

	return url
end
