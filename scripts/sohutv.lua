function kola_main(url, cid)
	local text = kola.wget(url)

	local ret = {}
	local js = cjson.decode(text)
	local live = js.data.live

	text = kola.wget(live)
	js = cjson.decode(text)

	if js.msg == "OK" then
		url = js.url
	else
		url = ""
	end

	return url
end
