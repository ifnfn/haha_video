local function to_epg(time, title)
	local function strtotime(t)
		local d = os.date("*t", kola.gettime())

		d.hour, d.min = kola.strsplit(":", time, 2)
		d.hour = tonumber(d.hour)
		d.min  = tonumber(d.min)
		d.sec  = 0

		return os.time(d)
	end

	local epg = {}

	epg.time_string = time
	epg.title       = string.gsub(title, "_$", "") -- strip, trim, 去头尾空格
	epg.time        = strtotime(time)
	epg.duration    = 0

	return epg
end

-- CNTV 中央台的 EPG
function get_channel_cntv(albumName)
	local id = string.match(albumName, ".*-(%d+) ")
	local vid = string.format("cctv%s", id)

	local ret = {}
	local idx = 1
	local url = string.format('http://tv.cntv.cn/index.php?action=epg-list&date=%s&channel=%s', os.date("%Y-%m-%d", kola.gettime()), vid)
	local text = kola.wget(url, false)

	for time, title in rex.gmatch(text, '<a target="_blank" href=".*" class="p_name_a">(.*) (.*?)</a>') do
		-- print(time, title)
		ret[idx] = to_epg(time, title)

		if idx > 1 then
			ret[idx - 1].duration = os.difftime(ret[idx].time, ret[idx - 1].time)
		end
		idx = idx + 1
	end

	for time, title in rex.gmatch(text, '<a class="p_name" href="###">(.*) (.*?)</a>') do
		-- print(time, title)
		ret[idx] = to_epg(time, title)

		if idx > 1 then
			ret[idx - 1].duration = os.difftime(ret[idx].time, ret[idx - 1].time)
		end
		idx = idx + 1
	end
	return cjson.encode(ret)
end

function get_channel_cutv(albumName)
	local name_key = {}
	name_key['深圳-都市频道'] = 'ZwxzUXr'
	name_key['深圳-电视剧']   = '4azbkoY'
	name_key['深圳-财经生活'] = '3vlcoxP'
	name_key['深圳-娱乐频道'] = '1q4iPng'
	name_key['深圳-少儿频道'] = '1SIQj6s'
	name_key['深圳-公共频道'] = '2q76Sw2'

	vid = name_key[albumName]

	if not vid then
		return '{}'
	end

	local url = string.format('http://cls.cutv.com/live/ajax/getprogrammelist2/id/%s/callback/callTslEpg', vid)
	local text = kola.wget(url, false)
	local ret = {}

	--print(url)
	if text then
		text = kola.pcre("callTslEpg\\((.*)\\)", text)
		local js = cjson.decode(text)

		if js and js.list then
			for id, ch in ipairs(js.list) do
				local date = ch.daytime / 1000
				if date == kola.getdate() then
					for k,a in ipairs(ch.programme) do
						local start_time = date + a.s / 1000
						ret[k] = {}
						ret[k].time_string = os.date("%H:%M", start_time)
						ret[k].time        = start_time
						ret[k].duration    = 0
						ret[k].title       = a.t
						if k > 1 then
							ret[k-1].duration = os.difftime(ret[k].time, ret[k-1].time)
						end
					end
				end
			end
		end
	end

	return cjson.encode(ret)
end

function get_channel_tvmao(albumName)
	local name_key = {}
	name_key['江苏-城市频道'] = 'jstv3'
	name_key['江苏-综艺频道'] = 'jstv2'
	name_key['江苏-公共频道'] = 'jstv8'
	name_key['江苏-影视频道'] = 'jstv4'
	name_key['江苏-休闲频道'] = 'jstv6'
	name_key['江苏-国际频道'] = 'jstv10'
	name_key['江苏-教育频道'] = 'jstv9'
	name_key['江苏-学习频道'] = ''
	name_key['江苏-好享购物'] = ''

	name_key['湖南卫视']     = 'hunantv1'
	name_key['沈阳-新闻频道'] = 'lnsy1'

    --name_key['吉林-东北戏曲'] = ''
    --name_key['吉林-家有购物'] = ''
    name_key['吉林卫视']     = 'jilin1'
    name_key['吉林-都市频道'] = 'jilin2'
    name_key['吉林-生活频道'] = 'jilin3'
    name_key['吉林-影视频道'] = 'jilin4'
    name_key['吉林-乡村频道'] = 'jilin5'
    name_key['吉林-公共新闻'] = 'jilin6'
    name_key['吉林-综艺文化'] = 'jilin7'

	--name_key['沈阳-经济频道'] = 'lnsy2'
	--name_key['沈阳-公共频道'] = 'lnsy3'
	--name_key['沈阳-生活频道'] = 'lnsy5'

	vid = name_key[albumName]

	if vid == nil or vid == '' then
		return '{}'
	end

	local url = string.format('http://www.tvmao.com/epg/program.jsp?c=%s', vid)
	local text = kola.wget(url, false)

	local ret = {}
	local idx = 1

	for time,title in rex.gmatch(text, '<li><span class="[apn][mt]">(.*)</span>(.*)</li>') do
		title = string.gsub(title, '<div class="tvgd".*</div>', '')
		title = string.gsub(title, '<a title=.*</a>', '')
		title = string.gsub(title, '<.->', '')
		ret[idx] = to_epg(time, title)

		if idx > 1 then
			ret[idx - 1].duration = os.difftime(ret[idx].time, ret[idx - 1].time)
		end
		idx = idx + 1
	end
	return cjson.encode(ret)
end
