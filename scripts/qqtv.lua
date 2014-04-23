-- 攻取节目的播放地址
local function get_video_url1(playid)
	local url = playid
	if string.find(playid, "http://") == nil then
		url = string.format('http://zb.v.qq.com:1863/?progid=%s&redirect=0&apptype=live&pla=ios', playid)
	end
	local text = kola.wget(url, false)

	if text then
		text = kola.pcre('location url="(.*?)"', text)
		return kola.strtrim(text)
	end

	return ""
end

local function get_video_url2( playid )
	-- stream:
	--	1 : flv
	-- 	2 : m3u8
	local url = string.format('http://info.zb.qq.com/?stream=1&sdtfrom=003&cnlid=%s&cmd=2&pla=0&flvtype=1', playid)

	local text = kola.wget(url, false)
	if text then
		text = string.gsub(text, ";", "")
		local js = cjson.decode(text)

		if js then
			return js.playurl
		end
	end

	return ""
end

function get_video_url( playid )
	local url = string.format('http://zb.cgi.qq.com/commdatav2?cmd=4&channel_id=%s', playid)

	local text = kola.wget(url, false)
	text = kola.pcre("QZOutput.*=({[\\s\\S]*});", text)
	local js = cjson.decode(text)

	if js then
		--{"ret":"0","flashver":"","p2p":"","http":"1","redirectver":"fplivev1.1"}
		--{"ret":-1,"msg":"no record"}
		if js.ret == "0" then
			return get_video_url2(playid)
		end
	end

	return get_video_url1(playid)
end

local function to_epg(time, title)
	local epg = {}
	local d = os.date("*t", kola.gettime())
	d.hour = tonumber(string.sub(time, 1, string.find(time, ":") - 1))
	d.min  = tonumber(string.sub(time,    string.find(time, ":") + 1))
	d.sec  = 0

	epg.time_string = time
	epg.title       = string.gsub(title, "_$", "") -- strip, trim, 去头尾空格
	epg.time        = os.time(d)
	epg.duration    = 0

	return epg
end

-- 获取节目的EPG
function get_channel(vid)
	local url = string.format('http://v.qq.com/live/tv/%s.html', vid)
	local text = kola.wget(url, false)

	local ret = {}
	if text then
		local i = 1
		for x in rex.gmatch(text, '(<div class=".*sta_unlive j_wanthover">[\\s\\S]*?</div>)') do
			for time, title in rex.gmatch(x, '<span class="time">(.*)</span>\\s*<span title="(.*)" class') do
				ret[i] = to_epg(time, title)
				if i > 1 then
					ret[i-1].duration = os.difftime(ret[i].time, ret[i-1].time)
				end
				i = i + 1
			end
		end
	end

	return cjson.encode(ret)
end
