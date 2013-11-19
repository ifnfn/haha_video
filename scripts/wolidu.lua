function server_find(url, list)
	ret = false
	table.foreach(list, function(a, b) if string.find(url, b) then ret = true return end end)
	return ret
end

function kola_main(url, referer, server)
	if server_find(url, { "basic_1.php" }) then
		text = kola.wget(url, referer)
		--{"u":"rtmp://120.205.13.194/beijingtv/beijingtv.stream", "p":"ck"}
		local data = cjson.decode(text)
		if data.u == '46' then
			return ''
		else
			return data.u
		end
	elseif server_find(url, {"sohu.php", "dxtx.php", "dxnm.php", "sxmsp.php"}) then
		text = kola.wget(url, referer)
		url = kola.pcre('<a HREF="(.*)">', text)
	end

	return url
end


