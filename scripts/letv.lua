function get_html(url)
	local result = ""
	c = cURL.easy_init()
	c:setopt_url(url)
	local ok = c:perform({writefunction = function(str)
		result = result .. str
	end})
	return ok, result
end

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
