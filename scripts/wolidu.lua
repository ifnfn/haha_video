function get_timestamp()
	local ret = kola.wget('http://epgsrv01.ucatv.com.cn/api/getUnixTimestamp')
	if ret ~= nil then
		local time_js = cjson.decode(ret)
		return  tonumber(time_js.time)
	end

	return 0
end

function server_find(url, list)
	ret = false
	table.foreach(list, function(a, b) if string.find(url, b) then ret = true return end end)
	return ret
end

function kola_main1(url, referer, server)
	url = "http://wolidou.gotoip3.com/zjm.php?u=cctv8"
	referer = "http://www.wolidou.com/tvp/217/play217_2_0.html"
	text = kola.wget(url, referer)
	print(text)
end

function kola_main(url, referer, server)
	--print(url, referer, server)
	server_list = {
		"sohu.php", "dxtx.php", "dxnm.php", "sxmsp.php", "jstv.php", "moon.php", "dxcctv.php",
		'dxnm.php', 'dxifeng.php', 'basicflv.php', "yu.php", "sdsj.php", "zjm.php", "zjm.php"
	}
	if server_find(url, { "basic_1.php" }) then
		text = kola.wget(url, referer)
		--{"u":"rtmp://120.205.13.194/beijingtv/beijingtv.stream", "p":"ck"}
		local data = cjson.decode(text)
		if data.u == '46' then
			return ''
		else
			return data.u
		end
	elseif server_find(url, server_list) then
		if server_find(url, {"www.wolidou.com/s/"}) then
			t = tostring(get_timestamp())
			ux = {}
			ux[1] = 'http://www.wolidou.com/s/key.php?f=k&t=' .. t
			ux[2] = url .. "&ts=" .. t
			text = kola.wget(ux, referer)
			url = cjson.decode(text).wolidou
		else
			text = kola.wget(url, referer)
			url = kola.pcre('<a HREF="(.*)">', text)
		end

		if url == "http://www.wolidou.com/live.mp4" then
			url = ""
		end
	end

	return url
end


