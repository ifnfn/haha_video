function server_find(url, list)
	ret = false
	table.foreach(list, function(a, b) if string.find(url, b) then ret = true return end end)
	return ret
end

function kola_main(url, referer, server)
	if server == "基本收视服务器：" then
		--{"u":"rtmp://120.205.13.194/beijingtv/beijingtv.stream", "p":"ck"}
		server_list = { "basic_1.php" }
		if server_find(url, server_list) then
			text = kola.wget(url, referer)
			local data = cjson.decode(text)
			if data.u == '46' then
				url = ''
			else
				url = data.u
			end
		end

		return url
	elseif server == "超速服务器：" then
		server_list = { "sohu.php", "dxtx.php", "dxnm.php", "sxmsp.php"}
		if server_find(url, server_list) then
			text = kola.wget(url, referer)
			url = kola.pcre('<a HREF="(.*)">', text)
		end

		return url
	else

	end

	return ""
end


