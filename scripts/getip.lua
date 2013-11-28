function kola_main(url)
	x =  ""
	url = "http://ip.chinaz.com/IP/?IP=" .. kola.urlencode(url)

	local text = kola.wget(url)
	if text ~= nil then
		x = kola.pcre('来自:<strong>(.*?) .*</strong>|<strong class="red">查询结果.*?</strong>', text)
	end

	return x
end


