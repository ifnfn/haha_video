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

	function trim (s) return (string.gsub(s, "^%s*(.-)%s*$", "%1")) end
	epg.time_string = time
	epg.title       = kola.strtrim(title)
	--epg.title       = trim(title) -- strip, trim, 去头尾空格
	epg.time        = strtotime(time)
	epg.duration    = 0

	return epg
end

local function find(var, tag, key, value)
	-- check input:
	if type(var)~="table" then return end
	if type(tag)=="string" and #tag==0 then tag=nil end
	if type(key)~="string" or #key==0 then key=nil end
	if type(value)=="string" and #value==0 then value=nil end
	-- compare this table:
	if tag~=nil then
		if var[0]==tag and ( value == nil or var[key]==value ) then
			setmetatable(var,{__index=xml, __tostring=xml.str})
			return var
		end
	else
		if value == nil or var[key]==value then
			setmetatable(var,{__index=xml, __tostring=xml.str})
			return var
		end
	end
	-- recursively parse subtags:
	for k,v in ipairs(var) do
		if type(v)=="table" then
			local ret = find(v, tag, key,value)
			if ret ~= nil then return ret end
		end
	end
end

local function get_vid(key_map, albumName)
	local vid = nil
	local new_vid = key_map[albumName]
	if new_vid then
		vid = new_vid
	elseif string.find(albumName, 'HD') or string.find(albumName, '卫视') then
		albumName = string.gsub(albumName, 'HD', '')
		albumName = string.gsub(albumName, '卫视', '')
		return get_vid(key_map, albumName)
	end

	return vid
end

function get_channel_wasu(albumName)
	local name_key = {}
    name_key[''] = ''

    vid = get_vid(name_key, albumName)

	if vid == nil then
		return nil
	end

	local url = string.format('http://chyd-playbill.wasu.tv/live_playbill/servlet/RequestCheck?channelName=%s', vid)
	local text = kola.wget(url, false)

	local today = os.date("%d日", kola.gettime())
	local x = xml.eval(text)
	local v = find(x, "month")
	for a, b in pairs(v) do
		if b.value == today then
			local ret = {}
			local idx = 1
			local day = find(b, "day")
			for _ , program in pairs(day) do
				if program.value then
					time, title = rex.match(program.value, '(.*)\\s+(.*)')
					ret[idx] = to_epg(time, title)
					if idx > 1 then
						ret[idx - 1].duration = os.difftime(ret[idx].time, ret[idx - 1].time)
					end
					idx = idx + 1
				end
			end
			return cjson.encode(ret)
		end
	end
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
	if ret then
		return cjson.encode(ret)
	end
end

function get_channel_cutv(albumName)
	local name_key = {}
	name_key['深圳-都市频道'] = 'ZwxzUXr'
	name_key['深圳-电视剧']   = '4azbkoY'
	name_key['深圳-财经生活'] = '3vlcoxP'
	name_key['深圳-娱乐频道'] = '1q4iPng'
	name_key['深圳-少儿频道'] = '1SIQj6s'
	name_key['深圳-公共频道'] = '2q76Sw2'

    vid = get_vid(name_key, albumName)

	if vid == nil then
		return nil
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

	if ret then
		return cjson.encode(ret)
	end
end

function get_channel_tvmao(albumName)
	local name_key = {}
	-- 央视
	name_key['CCTV News']      = 'cctv19'
	name_key['CCTV 风云足球']   = 'cctvpayfee1'
	name_key['CCTV 风云音乐']   = 'cctvpayfee2'
	name_key['CCTV 第一剧场']   = 'cctvpayfee3'
	name_key['CCTV 风云剧场']   = 'cctvpayfee4'
	name_key['CCTV 世界地理']   = 'cctvpayfee5'
	name_key['CCTV 电视指南']   = 'cctvpayfee6'
	name_key['CCTV 怀旧剧场']   = 'cctvpayfee7'
	name_key['CCTV 国防军事']   = 'cctvpayfee8'
	name_key['CCTV 女性时尚']   = 'cctvpayfee9'
	name_key['CCTV 戏曲国际']   = 'cctvpayfee11'
	name_key['CCTV 高尔夫网球'] = 'cctvpayfee13'
	name_key['CCTV 文化精品']   = 'cctvpayfee14'
	name_key['留学世界']        = 'cctvpayfee24'
	name_key['CCTV 央视台球']   = 'cctvpayfee36'
	name_key['CCTV 证券资讯']   = "cctvcj" -- why?
	name_key['CCTV 发现之旅']   = 'cctvfxzl'
	name_key['CCTV 俄语频道']   = 'cctvr'
	name_key['CCTV 阿语频道']   = 'cctva'
	name_key['CCTV 法语频道']   = 'cctvf'
	name_key['CCTV 西语频道']   = 'cctv17'

	-- 卫视
	name_key['安徽']   = 'ahtv1'
	name_key['北京']   = 'btv1'
	name_key['重庆']   = 'ccqtv1'
	name_key['东方']   = 'dongfang1'
	name_key['东南']   = 'fjtv2'
	name_key['广东']   = 'gdtv1'
	name_key['广西']   = 'guanxi1'
	name_key['甘肃']   = 'gstv1'
	name_key['贵州']   = 'guizoutv1'
	name_key['海峡']   = 'hxtv'
	name_key['河北']   = 'hebei1'
	name_key['河南']   = 'hntv1'
	name_key['黑龙江']  = 'hljtv1'
	name_key['湖南']   = 'hunantv1'
	name_key['湖北']   = 'hubei1'
	name_key['吉林']   = 'jilin1'
	name_key['江西']   = 'jxtv1'
	name_key['江苏']   = 'jstv1'
	name_key['康巴']   = 'kamba-tv'
	name_key['辽宁']   = 'lntv1'
	name_key['旅游']   = 'tctc1'
	name_key['内蒙古']  = 'nmgtv1'
	name_key['宁夏']   = 'nxtv2'
	name_key['青海']   = 'qhtv1'
	name_key['深圳']   = 'sztv1'
	name_key['陕西']   = 'shxitv1'
	name_key['山西']   = 'sxtv1'
	name_key['四川']   = 'sctv1'
	name_key['天津']   = 'tjtv1'
	name_key['西藏']   = 'xizangtv2'
	name_key['厦门']   = 'xmtv5'
	name_key['新疆']   = 'xjtv1'
	name_key['香港']   = 'hks'
	name_key['延边']   = 'yanbian1'
	name_key['云南']   = 'yntv1'
	name_key['浙江']   = 'zjtv1'
	name_key['兵团']   = 'bingtuan'
	name_key['凤凰卫视香港台']   = 'phoenixhk'
	name_key['凤凰卫视中文台']   = ''
	name_key['凤凰卫视资讯台']   = 'phoenix-infonews'
	name_key['华娱']   = 'huayu1'
	name_key['健康']   = 'jkwshk'
	name_key['莲花']   = 'lotusbtv'
	name_key['南方']   = 'nanfang6'
	name_key['农林']   = 'shxitv9'
	name_key['卡酷少儿']   = 'btv10'
	name_key['三沙']   = 'sanshatv'
	name_key['炫动卡通']   = 'toonmax1'


	-- 安徽
	name_key['安徽经济'] = 'ahtv2'
	name_key['安徽影视'] = 'ahtv3'
	name_key['安徽综艺'] = 'ahtv4'
	name_key['安徽公共'] = 'ahtv5'
	name_key['安徽科教'] = 'ahtv6'
	name_key['安徽人物'] = 'ahtv7'
	name_key['安徽国际'] = 'ahtv8'
	name_key['安庆公共'] = 'aqgg'
	name_key['安庆黄梅戏'] = nil
	name_key['安庆生活']    = nil
	name_key['安庆新闻综合'] = 'aqxw'
	name_key['百姓健康']     = 'chtv'
	name_key['蚌埠公共频道'] = 'ahbbtv3'
	name_key['蚌埠生活频道'] = 'ahbbtv2'
	name_key['蚌埠新闻综合'] = 'ahbbtv1'

	name_key['天津新闻'] = 'tjtv2'
	name_key['天津文艺'] = 'tjtv3'
	name_key['天津影视'] = 'tjtv4'
	name_key['天津都市'] = 'tjtv5'
	name_key['天津体育'] = 'tjtv6'
	name_key['天津科教'] = 'tjtv7'
	name_key['天津少儿'] = 'tjtv8'
	name_key['天津公共'] = 'tjtv9'

	name_key['北京文艺'] = 'btv2'
	name_key['北京科教'] = 'btv3'
	name_key['北京影视'] = 'btv4'
	name_key['北京财经'] = 'btv5'
	name_key['北京体育'] = 'btv6'
	name_key['北京生活'] = 'btv7'
	name_key['北京青年'] = 'btv8'
	name_key['北京新闻'] = 'btv9'

	name_key['长沙女性'] = 'changshawumon1'
	name_key['长沙政法'] = 'changshawumon2'
	name_key['长沙经贸'] = 'changshawumon3'
	name_key['长沙新闻'] = 'changshawumon4'
	name_key['长沙公共'] = 'changshawumon5'

	name_key['长春综合频道'] = 'ctv1'
	name_key['长春娱乐频道'] = 'ctv2'
	name_key['长春新知频道'] = 'ctv5'
	name_key['常州新闻综合'] = 'changzhou1'
	name_key['常州都市频道'] = 'changzhou2'
	name_key['常州生活频道'] = 'changzhou3'
	name_key['常州公共频道'] = 'changzhou4'

	name_key['沈阳公共频道'] = 'lnsy3'
	name_key['沈阳经济频道'] = 'lnsy2'
	name_key['沈阳新闻综合'] = 'lnsy1'
	name_key['成都新闻综合'] = 'chengdu1'
	name_key['成都经济资讯'] = 'chengdu2'
	name_key['成都都市生活'] = 'chengdu3'
	name_key['成都影视文艺'] = 'chengdu4'
	name_key['成都公共频道'] = 'chengdu5'
	name_key['成都少儿']     = 'cdtv-6'

	name_key['大连乐天购物'] = nil
	name_key['大连新闻频道'] = 'dalian1'
	name_key['大连生活频道'] = 'dalian2'
	name_key['大连公共频道'] = 'dalian3'
	name_key['大连文体频道'] = 'dalian4'
	name_key['大连影视频道'] = 'dalian5'
	name_key['大连少儿频道'] = 'dalian6'
	name_key['大连财经频道'] = 'dalian7'

	name_key['电子体育'] = 'esports'
	name_key['东方财经'] = 'sitv14'
	name_key['东方电影'] = 'dfmv1'
	name_key['东方购物'] = 'shhai10'
	name_key['东莞公共'] = 'gddg1'
	name_key['东莞综合'] = 'gddg2'
	name_key['鄂尔多斯二套'] = nil
	name_key['鄂尔多斯三套'] = nil
	name_key['鄂尔多斯一套'] = nil
	name_key['恩施公共频道'] = nil
	name_key['恩施新闻频道'] = nil
	name_key['恩施综艺频道'] = nil
	name_key['法国1'] = nil

	name_key['福建综合'] = 'fjtv1'
	name_key['福建公共'] = 'fjtv3'
	name_key['福建新闻'] = 'fjtv4'
	name_key['福建电视剧'] = 'fjtv5'
	name_key['福建都市时尚'] = 'fjtv6'
	name_key['福建经济'] = 'fjtv7'
	name_key['福建体育'] = 'fjtv8'
	name_key['福建少儿'] = 'fjtv9'

	name_key['福州新闻'] = 'fztv1'
	name_key['福州生活'] = 'fztv3'
	name_key['福州影视'] = 'fztv2'
	name_key['福州少儿'] = 'fztv-baby'

	name_key['高尔夫.网球'] = nil
	name_key['高尔夫'] = nil
	name_key['广东会展频道'] = 'huizahn'
	name_key['广东现代教育'] = nil
	name_key['珠江电影'] = 'gdtv2'
	name_key['广东体育'] = 'gdtv3'
	name_key['广东公共'] = 'gdtv4'
	name_key['珠江频道'] = 'gdtv5'
	name_key['广东新闻'] = 'gdtv6'

	name_key['广西国际']    = 'gxgj'
	name_key['广西交通']    = nil
	name_key['广西综艺']    = 'guanxi2'
	name_key['广西都市频道'] = 'guanxi3'
	name_key['广西影视']    = 'guanxi5'
	name_key['广西公共']    = 'guanxi4'
	name_key['广西资讯']    = 'guanxi7'

	name_key['广州综合'] = 'gztv1'
	name_key['广州新闻'] = 'gztv2'
	name_key['广州竞赛'] = 'gztv3'
	name_key['广州影视'] = 'gztv4'
	name_key['广州英语'] = 'gztv5'
	name_key['广州经济'] = 'gztv6'
	name_key['广州少儿'] = 'gztv7'
	name_key['嘉佳卡通'] = 'gdtv7'

	name_key['贵阳经济生活'] = 'gytv2'
	name_key['贵州家有购物1'] = nil
	name_key['贵州经济频道'] = nil

	name_key['海南文体']    = 'hnwt'
	name_key['海南综合']    = 'hainantv1'
	name_key['海南新闻']    = 'hainantv2'
	name_key['海南公共']    = 'hainantv3'
	name_key['海南青少科教'] = 'hainantv5'
	name_key['海南影视剧']   = 'hnysj'

	name_key['邯郸公共'] = nil
	name_key['邯郸民生都市'] = nil
	name_key['邯郸新闻综合'] = nil

	name_key['杭州综合'] = 'htv1'
	name_key['杭州明珠'] = 'htv2'
	name_key['杭州生活'] = 'htv3'
	name_key['杭州影视'] = 'htv4'
	name_key['杭州少儿'] = 'htv5'
	name_key['杭州导视'] = 'htv6'
	name_key['杭州房产'] = 'htv66'

	name_key['河北经济'] = 'hebei2'
	name_key['河北都市'] = 'hebei3'
	name_key['河北影视'] = 'hebei4'
	name_key['河北少儿科教'] = 'hebei5'
	name_key['河北公共'] = 'hebei6'
	name_key['河北农民'] = 'hebei7'

	name_key['合肥教育'] = nil
	name_key['合肥新闻频道'] = 'hefeitv1'
	name_key['合肥生活频道'] = 'hefeitv2'
	name_key['合肥法制教育'] = 'hefeitv3'
	name_key['合肥财经频道'] = 'hefeitv4'
	name_key['合肥影院频道'] = 'hefeitv5'
	name_key['合肥文体博览'] = 'wentibolan'

	name_key['河南都市']    = 'hntv2'
	name_key['河南民生']    = 'hntv3'
	name_key['河南政法']    = 'hntv4'
	name_key['河南电视剧']  = 'hntv5'
	name_key['河南新闻']    = 'hntv6'
	name_key['河南欢腾购物'] = 'hntv7'
	name_key['河南公共']    = 'hntv8'
	name_key['河南新农村']  = 'hntv9'
	name_key['河南国际']    = 'hngj'

	name_key['黑龙江影视'] = 'hljtv2'
	name_key['黑龙江文艺'] = 'hljtv3'
	name_key['黑龙江都市'] = 'hljtv4'
	name_key['黑龙江新闻'] = 'hljtv5'
	name_key['黑龙江公共'] = 'hljtv6'
	name_key['黑龙江少儿'] = 'hljtv7'
	name_key['黑龙江导视频道'] = 'hljdaoshi'

	name_key['湖北碟市'] = ''
	name_key['湖北公共'] = 'hubei7'
	name_key['湖北教育'] = 'hubei4'
	name_key['湖北经视'] = 'hubei8'
	name_key['湖北体育生活'] = 'hubei5'
	name_key['湖北影视'] = 'hubei3'
	name_key['湖北综合'] = 'hubei2'
	name_key['睛彩湖北'] = nil
	name_key['湖北垄上'] = 'jztv2'

	name_key['湖南经视'] = 'hnetv1'
	name_key['湖南都市'] = 'hnetv2'
	name_key['金鹰纪实'] = 'hnetv3'
	name_key['金鹰卡通'] = 'hunantv2'
	name_key['湖南娱乐'] = 'hunantv3'
	name_key['湖南电视剧'] = 'hunantv4'
	name_key['湖南公共'] = 'hunantv5'
	name_key['潇湘电影'] = 'hunantv6'
	name_key['湖南国际'] = 'hunantv7'

	name_key['黄石都市'] = 'hbhstv3'
	name_key['黄石新闻'] = 'hbhstv1'
	name_key['黄石移动'] = nil
	name_key['黄石综合'] = nil

	name_key['惠州一套'] = 'gdhztv1'
	name_key['惠州二套'] = 'gdhztv2'

	name_key['吉林东北戏曲'] = nil
	name_key['吉林篮球'] = nil
	name_key['吉林都市'] = 'jilin2'
	name_key['吉林生活'] = 'jilin3'
	name_key['吉林影视'] = 'jilin4'
	name_key['吉林乡村'] = 'jilin5'
	name_key['吉林公共'] = 'jilin6'
	name_key['吉林综艺文化'] = 'jilin7'

	name_key['济南泉天下'] = nil
	name_key['济南新闻'] = 'jntv1'
	name_key['济南都市'] = 'jntv2'
	name_key['济南影视'] = 'jntv3'
	name_key['济南娱乐'] = 'jntv4'
	name_key['济南生活'] = 'jntv5'
	name_key['济南商务'] = 'jntv6'
	name_key['济南少儿'] = 'jntv7'

	name_key['家庭理财'] = 'jiatinglicai'
	name_key['建始综合频道'] = nil

	name_key['江苏综艺'] = 'jstv2'
	name_key['江苏城市'] = 'jstv3'
	name_key['江苏影视'] = 'jstv4'
	name_key['江苏靓妆'] = 'jstv5'
	name_key['靓妆频道'] = 'jstv5'
	name_key['江苏休闲'] = 'jstv6'
	name_key['江苏体育休闲'] = 'jstv6'
	name_key['优漫卡通'] = 'jstv7'
	name_key['江苏公共'] = 'jstv8'
	name_key['江苏教育'] = 'jstv9'
	name_key['江苏国际'] = 'jstv10'
	name_key['江苏学习'] = nil
	name_key['江苏好享购物'] = nil

	name_key['江西都市']    = 'jxtv2'
	name_key['江西经视']    = 'jxtv3'
	name_key['江西影视']    = 'jxtv4'
	name_key['江西公共']    = 'jxtv5'
	name_key['江西少儿']     = 'jxtv6'
	name_key['江西红色经典'] = 'jxtv7'
	name_key['江西电视指南'] = 'jxtv-guide'
	name_key['江西风尚购物'] = 'fstvgo'
	name_key['江西移动电视'] = nil

	name_key['江阴民生'] = nil
	name_key['江阴新闻'] = nil

	name_key['金华综合'] = 'jinhuatv1'
	name_key['金华都市'] = nil
	name_key['金华公共'] = nil

	name_key['睛彩平顶山'] =  nil
	name_key['经典电影'] = nil
	name_key['荆州新闻综合'] = 'jztv1'
	name_key['劲爆体育'] = 'sitv4'
	name_key['快乐宠物'] = 'pets-tv'
	name_key['快乐垂钓'] = 'kuailechuidiao'
	name_key['快乐购'] = 'happigo'

	name_key['昆明2'] = nil
	name_key['昆明3'] = nil
	name_key['昆明6'] = nil

	name_key['昆明新闻频道'] = 'kmtv1'

	name_key['乐视电视剧'] = nil
	name_key['乐视电影'] = nil
	name_key['乐视动漫'] = nil
	name_key['乐视风尚'] = nil
	name_key['乐视高尔夫'] = nil
	name_key['乐视高清'] = nil
	name_key['乐视跟播'] = nil
	name_key['乐视韩剧'] = nil
	name_key['乐视纪录'] = nil
	name_key['乐视MV'] = nil
	name_key['乐视亲子'] = nil
	name_key['乐视体育'] = nil
	name_key['乐视网球'] = nil
	name_key['乐视文娱'] = nil
	name_key['乐视戏曲'] = nil
	name_key['乐视自制剧'] = nil
	name_key['乐视足球'] = nil
	name_key['乐思购'] = nil

	name_key['柳州新闻频道'] = 'gxlztv1'
	name_key['柳州科教频道'] = 'gxlztv2'
	name_key['柳州公共频道'] = 'gxlztv3'
	name_key['美嘉购物'] = nil
	name_key['魅力时尚'] = nil
	name_key['魅力时装'] = nil
	name_key['魅力音乐'] = 'sitv5'

	name_key['绵阳公共频道'] = nil
	name_key['绵阳交通信息'] = nil
	name_key['绵阳教育资讯'] = nil
	name_key['绵阳科技频道'] = nil
	name_key['绵阳旅游信息'] = nil
	name_key['绵阳新农村信息'] = nil
	name_key['绵阳综合频道'] = nil
	name_key['绵阳综合信息'] = nil

	name_key['MTV音乐'] = nil

	name_key['南昌新闻综合'] = 'nanchang1'
	name_key['南昌公共频道'] = 'nanchang2'
	name_key['南昌资讯政法'] = 'nanchang3'
	name_key['南昌都市频道'] = 'nanchang4'

	name_key['南充公共频道'] = nil -- 'scnctv2'
	name_key['南充文娱频道'] = nil -- 'scnctv4'
	name_key['南充新闻频道'] = 'scnctv1'
	name_key['南充资讯频道'] = nil -- 'scnctv5'

	name_key['南方经视'] = 'nanfang1'
	name_key['南方综艺'] = 'nanfang3'
	name_key['南方影视'] = 'nanfang4'
	name_key['南方少儿'] = 'nanfang5'

	name_key['南京教科频道'] = 'njtv3'
	name_key['南京少儿频道'] = 'njtv7'
	name_key['南京生活频道'] = 'njtv4'
	name_key['南京十八频道'] = 'njtv6'
	name_key['南京新闻综合'] = 'njtv1'
	name_key['南京影视'] = 'njtv2'
	name_key['南京娱乐频道'] = 'njtv5'

	name_key['南宁新闻综合'] = 'nanningtv1'
	name_key['南宁影视娱乐'] = 'nanningtv2'
	name_key['南宁都市生活'] = 'nanningtv3'
	name_key['南宁公共频道'] = 'nanningtv4'

	name_key['宁波新闻综合'] = 'nbtv1'
	name_key['宁波社会生活'] = 'nbtv2'
	name_key['宁波文化娱乐'] = 'nbtv3'
	name_key['宁波影视剧']   = 'nbtv4'
	name_key['宁波少儿频道'] = 'nbtv5'

	name_key['宁夏公共'] = 'nxtv1'
	name_key['宁夏经济'] = 'nxtv3'
	name_key['宁夏影视'] = 'nxtv4'
	name_key['宁夏少儿'] = 'nxtv5'

	name_key['欧洲足球'] = 'europefootball'

	name_key['衢州公共生活'] = nil
	name_key['衢州经济信息'] = nil
	name_key['衢州生活娱乐'] = nil
	name_key['衢州新闻综合'] = nil
	name_key['全纪实'] = 'sitv11'
	name_key['热播剧场'] = nil
	name_key['三佳购物'] = 'ttcjmall'

	name_key['厦门新闻'] = 'xmtv1'
	name_key['厦门纪实'] = 'xmtv2'
	name_key['厦门生活'] = 'xmtv3'
	name_key['厦门影视'] = 'xmtv4'

	name_key['陕西都市青春'] = 'shxitv3'
	name_key['陕西公共频道'] = 'shxitv2'
	name_key['陕西生活频道'] = 'shxitv4'
	name_key['陕西体育休闲'] = 'shxitv8'
	name_key['陕西新闻资讯'] = nil

	name_key['上海教育']    = 'shedu1'
	name_key['上海新闻综合'] = 'shhai1'
	name_key['第一财经']     = 'shhai2'
	name_key['上海生活时尚'] = 'shhai3'
	name_key['上海星尚']     = 'shhai3'
	name_key['上海电视剧']   = 'shhai4'
	name_key['五星体育']     = 'shhai5'
	name_key['上海纪实']     = 'shhai6'
	name_key['上海新娱乐']   = 'shhai7'
	name_key['上海艺术人文'] = 'shhai8'
	name_key['上海外语频道'] = 'shhai9'
	name_key['上海外语']    = 'shhai9'

	name_key['绍兴文化影视'] = 'shaoxin1'
	name_key['绍兴公共频道'] = 'shaoxin2'
	name_key['绍兴新闻综合'] = 'shaoxin3'

	name_key['深圳都市']    = 'sztv2'
	name_key['深圳电视剧']   = 'sztv3'
	name_key['深圳财经生活'] = 'sztv4'
	name_key['深圳娱乐']     = 'sztv5'
	name_key['深圳体育健康'] = 'sztv6'
	name_key['深圳少儿']     = 'sztv7'
	name_key['深圳公共']     = 'sztv8'
	name_key['深圳dv生活']   = 'sztv11'

	name_key['石家庄新闻综合'] = 'shijiazhuang1'
	name_key['石家庄娱乐'] = 'shijiazhuang2'
	name_key['石家庄生活'] = 'shijiazhuang3'
	name_key['石家庄都市'] = 'shijiazhuang4'

	------------------------------------------------
	name_key['收藏天下'] = 'shoucangtiaxia'
	name_key['四海钓鱼'] = 'bamc4'
	name_key['天元围棋'] = 'tianyuanweiqi'
	name_key['先锋纪录'] = 'documentary-channel'
	name_key['先锋乒羽'] = 'xfby'
	name_key['职业指南'] = 'bamc16'
	name_key['TVB8'] = 'TVB8'
	------------------------------------------------

	name_key['四川经视']     = nil
	name_key['四川文化旅游'] = 'sctv2'
	name_key['四川财经']     = 'sctv3'
	name_key['四川新闻资讯'] = 'sctv4'
	name_key['四川影视文艺'] = 'sctv5'
	name_key['四川妇女儿童'] = 'sctv7'
	name_key['四川公共']    = 'sctv9'

	name_key['苏州新闻综合'] = 'suzhoutv1'
	name_key['苏州社会经济'] = 'suzhoutv2'
	name_key['苏州文化生活'] = 'suzhoutv3'
	name_key['苏州电影娱乐'] = 'suzhoutv4'
	name_key['苏州生活资讯'] = 'suzhoutv5'

	name_key['遂宁公共公益'] = nil
	name_key['遂宁互动影视 '] = nil
	name_key['遂宁新闻综合'] = nil
	name_key['遂宁直播频道'] = nil

	name_key['泰州新闻综合'] = 'tztv1'

	name_key['唐山新闻'] = 'tssv1'
	name_key['唐山生活'] = 'tssv2'
	name_key['唐山影视'] = 'tssv3'
	name_key['唐山公共'] = 'tssv4'

	name_key['TGA游戏频道'] = nil
	name_key['通化公共'] = nil
	name_key['通化科教'] = nil
	name_key['通化新闻频道'] = nil
	name_key['VST电影台'] = nil
	name_key['VST纪录片'] = nil

	name_key['威海新闻综合'] = 'weihai1'
	name_key['威海公共频道'] = 'weihai2'

	name_key['芜湖新闻综合'] = 'wuhutv1'
	name_key['芜湖生活频道'] = 'wuhutv2'
	name_key['芜湖徽商频道'] = 'wuhutv3'

	name_key['无锡新闻综合'] = 'wuxi1'
	name_key['无锡娱乐']     = 'wuxi2'
	name_key['无锡经济频道'] = 'wuxi4'
	name_key['无锡生活频道'] = 'wuxi5'

	name_key['武汉新闻频道'] = 'whtv1'
	name_key['武汉文艺频道'] = 'whtv2'
	name_key['武汉科教生活'] = 'whtv3'
	name_key['武汉影视频道'] = 'whtv4'
	name_key['武汉体育频道'] = 'whtv5'
	name_key['武汉外语频道'] = 'whtv6'
	name_key['武汉少儿频道'] = 'whtv7'

	name_key['西安新闻综合'] = 'xian1'
	name_key['西安白鸽都市'] = 'xian2'
	name_key['西安商务资讯'] = 'xian3'
	name_key['西安文化影视'] = 'xian4'
	name_key['西安健康快乐'] = 'xian5'
	name_key['西安音乐综艺'] = 'xian6'

	name_key['西藏藏语'] = 'xizangtv1'

	name_key['西宁生活频道'] = 'xining-life'
	name_key['西宁新闻频道'] = 'xining-news'

	name_key['新疆哈萨克语新闻综合'] = 'xjtv3'
	name_key['新疆少儿'] = 'xjtv12'
	name_key['新疆维语新闻综合'] = 'xjtv2'
	name_key['新疆维语综艺'] = 'xjtv5'

	name_key['新影视'] = nil
	name_key['新娱乐'] = nil

	name_key['徐州新闻综合'] = 'xztv1'
	name_key['徐州经济生活'] = 'xztv2'
	name_key['徐州文艺影视'] = 'xztv3'
	name_key['徐州公共频道'] = 'xztv4'

	name_key['雪梨TV'] = nil
	name_key['雅安新闻综合'] = nil
	name_key['雅安雨城电视台'] = nil

	name_key['盐城一台'] = 'yanchengtv1'
	name_key['盐城二台'] = 'yanchengtv2'
	name_key['盐城三台'] = 'yanchengtv3'
	name_key['盐城四台'] = 'yanchengxk' -- TODO

	name_key['壹电视新闻台'] = 'nexttv-news'

	name_key['宜宾新闻综合'] = 'scybtv1'
	name_key['宜宾公共生活'] = 'scybtv2'

	name_key['义乌新闻综合'] = 'zjyiwu1'
	name_key['义乌商贸频道'] = 'zjyiwu2'
	name_key['义乌电视剧'] = 'zjyiwu3'
	name_key['义乌公共'] = nil

	name_key['银川文体'] = 'yinchuang1'
	name_key['银川生活'] = 'yinchuang2'
	name_key['银川公共'] = 'yinchuang3'

	name_key['英语辅导'] = 'english-teaching'
	name_key['优优宝贝'] = 'bamc3'
	name_key['游戏风云hd'] = 'sitv2'
	name_key['游戏竞技'] = 'gtv-youxi'

	name_key['云南都市'] = nil
	name_key['云南少儿'] = 'yntv8'

	name_key['孕育指南'] = 'cctvpayfee32'

	name_key['枣庄公共频道'] = 'zaozhuang2'
	name_key['枣庄新闻综合'] = 'zaozhuang3'

	name_key['张家港生活'] = nil
	name_key['张家港新闻'] = nil

	name_key['浙江钱江都市']   = 'zjtv2'
	name_key['浙江经视']      = 'zjtv3'
	name_key['浙江科教']      = 'zjtv4'
	name_key['浙江教育科教']   = 'zjtv4'
	name_key['浙江影视娱乐']   = 'zjtv5'
	name_key['浙江6频道']     = 'zjtv6'
	name_key['浙江公共新农村'] = 'zjtv7'
	name_key['浙江少儿']      = 'zjtv8'
	name_key['浙江国际']      = 'zjtv9'
	name_key['浙江浙东新农村'] = nil
	name_key['浙江购物']      = nil
	name_key['浙江民生休闲']   = nil

	name_key['郑州妇女儿童频道'] = 'zhengzhoutv5'
	name_key['郑州商都频道'] = 'zhengzhoutv2'
	name_key['郑州时政频道'] = 'zhengzhoutv1'

	name_key['中国教育1'] = 'cetv1'
	name_key['中国教育2'] = 'cetv2'
	name_key['中国教育3'] = 'cetv3'

	name_key['重庆汽摩'] = nil
	name_key['重庆手持电视'] = nil
	name_key['重庆移动'] = nil
	name_key['重庆新财经'] = 'cqtvxcj'
	name_key['重庆影视'] = 'ccqtv2'
	name_key['重庆新闻'] = 'ccqtv3'
	name_key['重庆科教'] = 'ccqtv4'
	name_key['重庆都市'] = 'ccqtv5'
	name_key['重庆娱乐'] = 'ccqtv6'
	name_key['重庆生活'] = 'ccqtv7'
	name_key['重庆时尚'] = 'ccqtv8'
	name_key['重庆公共农村'] = 'ccqtv9'
	name_key['重庆少儿'] = 'ccqtv10'

	name_key['舟山公共频道'] = nil
	name_key['舟山就业服务'] = nil
	name_key['舟山群岛旅游'] = nil
	name_key['舟山生活频道'] = nil
	name_key['舟山新闻综合'] = nil

	name_key['周星驰专区'] = ''
	name_key['珠海1台'] = 'zhtv1'
	name_key['珠海2台'] = 'zhtv2'
	name_key['珠海生活服务'] = 'zhtv2'
	name_key['珠海新闻综合'] = 'zhtv2'

	vid = get_vid(name_key, albumName)

	if vid == nil and string.find(albumName, "CCTV") then
		aname = string.gsub(albumName, "-", "")
		vid = rex.match(aname, '(CCTV\\d+)')
		if vid == nil then
			return nil
		end
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

	if ret then
		return cjson.encode(ret)
	end
end

function get_channel_pptv(albumName)
    vid = get_vid(name_key, albumName)

	local time = kola.gettime()
	local url = string.format('http://live.pptv.com/api/tv_menu?cb=kola&date=%s&id=%s&canBack=0', 
			os.date("%Y-%m-%d", time), vid)

	local ret = {}
	local text = kola.wget(url, false)
	if text then
		text = rex.match(text, 'kola\\((.*)\\)')

		local js = cjson.decode(text)
		local i = 1
		local d = os.date("*t", time)
		for time,title in rex.gmatch(js.html, "</i>(\\w*:\\w*)</span></a>\\s*.*?title\\s*=\\s*['\"](.*?)['\"]") do
			d.hour = tonumber(string.sub(time, 1, string.find(time, ":") - 1))
			d.min  = tonumber(string.sub(time, string.find(time, ":") + 1))

			ret[i] = {}
			ret[i].time_string = time
			ret[i].time        = os.time(d)
			ret[i].title       = title
			ret[i].duration    = 0
			if i > 1 then
				ret[i-1].duration = os.difftime(ret[i].time, ret[i-1].time)
			end
			i = i + 1
		end
	end

	if ret then
		return cjson.encode(ret)
	end
end

-- 获取节目的EPG
function get_channel_jstv(albumName)
	local name_key = {}
    name_key[''] = ''
    vid = get_vid(name_key, albumName)

	vid = tonumber(vid)
	local url = 'http://newplayerapi.jstv.com/rest/getstation_8.html'
	local ret = {}

	text = kola.wget(url, false)
	if text then
		local js = cjson.decode(text)

		for id, ch in ipairs(js.paramz.channels) do
			if ch.id == vid then
				local len = #ch.guides
				for i, gui in ipairs(ch.guides) do
					k = len - i + 1
					ret[k] = to_epg(gui.bctime, gui.name)
					if k < len then
						ret[k].duration = os.difftime(ret[k+1].time, ret[k].time)
					end
				end

				break
			end
		end
	end

	if ret then
		return cjson.encode(ret)
	end
end

function get_channel_letv(albumName)
	local name_key = {}
    name_key[''] = ''
    vid = get_vid(name_key, albumName)

	local time = kola.gettime()
	local url = string.format("http://st.live.letv.com/live/playlist/%s/%s.json?_=%d", os.date("%Y%m%d", time), vid, time)

	local ret = {}
	text = kola.wget(url, false)
	if text then
		local js = cjson.decode(text)
		for k,v in ipairs(js.content) do
			--print(k,v.playtime, v.duration, v.title)
			ret[k] = to_epg(v.playtime, v.title)
			ret[k].duration = v.duration
		end
	end

	if ret then
		return cjson.encode(ret)
	end
end

function get_channel_qqtv(albumName)
	local name_key = {}
    name_key[''] = ''
    vid = get_vid(name_key, albumName)

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

	if ret then
		return cjson.encode(ret)
	end
end

function get_channel_smgbbtv(albumName)
	local name_key = {}
    name_key[''] = ''
    vid = get_vid(name_key, albumName)

	local ret = {}
	local url = string.format('http://l.smgbb.cn/schedule.ashx?channel=%s', vid)
	print(url)
	local text = kola.wget(url, false)

	if text then
		local js = cjson.decode(text)
		for k, v in ipairs(js.schedule) do
			ret[k] = {}
			ret[k].time_string = v.time
			ret[k].time        = tonumber(v.start)
			ret[k].duration    = tonumber(v['end']) - tonumber(v['start'])
			ret[k].title       = v.title
			--print(k, ret[k].time_string, ret[k].duration, ret[k].title)
		end
	end

	if ret then
		return cjson.encode(ret)
	end
end

-- 获取节目的EPG
function get_channel_sohutv(albumName)
	local name_key = {}
    name_key[''] = ''
    vid = get_vid(name_key, albumName)

	local url = string.format("http://poll.hd.sohu.com/live/stat/menu-segment.json?&sid=%s", vid)

	--print(url)
	local ret = {}
	local text = kola.wget(url, false)
	if text then
		local js = cjson.decode(text)
		for k,v in ipairs(js.attachment[1].MENU_LIST) do
			ret[k] = to_epg(v.START_TIME, v.NAME)
			if k > 1 then
				ret[k-1].duration = os.difftime(ret[k].time, ret[k-1].time)
			end
			--print(k, ret[k].time_string, ret[k].duration, ret[k].title)
		end
	end

	return cjson.encode(ret)
end

function get_channel_btv(albumName)
	local name_key = {}
    name_key[''] = ''
    vid = get_vid(name_key, albumName)
	local url = string.format("http://itv.brtn.cn/live/getepgday/%s", vid)

	local text = kola.wget(url, false)


	if text == nil then
		return "{}"
	end
	local js = cjson.decode(text)

	local ret = {}
	if js then
		for _, dayepg in ipairs(js.data) do
			local time = kola.gettime()
			if time >= tonumber(dayepg[1].start_time) and time < tonumber(dayepg[#dayepg].end_time) then
				for k, ch in ipairs(dayepg) do
					ret[k] = {}
					start_time = tonumber(ch.start_time)
					end_time = tonumber(ch.end_time)
					ret[k].time_string = os.date("%H:%M", start_time)
					ret[k].time        = tonumber(start_time)
					ret[k].duration    = end_time - start_time
					ret[k].title       = ch.title
					--print(k, ret[k].time_string, ret[k].title)
				end
				break
			end
		end
	end

	return cjson.encode(ret)
end

-- 获取节目的EPG
function get_channel_jxtv(url)
	local text = kola.wget(url)
	local ret = {}
	local idx = 1
	for time,title in rex.gmatch(text, '<b>(.*)</b><span class="name">(.*)</span>') do
		ret[idx] = to_epg(time, title)

		if idx > 1 then
			ret[idx-1].duration = os.difftime(ret[idx].time, ret[idx - 1].time)
		end
		idx = idx + 1
	end

	return cjson.encode(ret)
end

function get_channel_nbtv(vid, id)
	local url = string.format("%s/0/%d", vid, kola.gettime())

	local ret = {}
	text = kola.wget(url, false)
	if text and text ~= "TVie Exception: No streams." then
		local d = os.date("*t", kola.gettime())
		local prev_d = d
		local js = cjson.decode(text)
		for k,v in ipairs(js.result[1]) do
			ret[k] = {}
			s = tonumber(v.start_time)
			ret[k].time_string = os.date("%H:%M", s)
			ret[k].time        = s
			ret[k].duration    = tonumber(v.end_time) - s
			ret[k].title       = v.name
		end
	end

	return cjson.encode(ret)
end

-- 获取节目的EPG
function get_channel_nbtv(vid)
	--vid = tonumber(vid)
	local url = 'http://www.nntv.cn/epg/zhtv_epg.json'
	local ret = {}

	text = kola.wget(url, false)
	if text then
		text = kola.pcre("jsonp_program\\((.*)\\)", text)
		local js = cjson.decode(text)

		local k = 1
		for id, ch in ipairs(js) do
		    -- "name": "帮得行动（重播）_",
		    -- "start_time": "2014-01-24 00:17:00",
		    -- "end_time": "2014-01-24 07:00:00"
			if ch.column == vid then
				start_time = kola.date(ch.start_time)
				end_time = kola.date(ch.end_time)
				ret[k] = {}
				--ret[k].title = string.gsub(ch.name, "_$", "")
				ret[k].title       = string.gsub(ch.name, "^%s*(.-)%s*_*$", "%1")
				ret[k].time_string = os.date("%H:%M", start_time)
				ret[k].time        = start_time
				ret[k].duration    = end_time - start_time
				k = k + 1
			end
		end
	end

	--print(cjson.encode(ret))
	return cjson.encode(ret)
end

-- 获取节目的EPG
function get_channel_wztv(vid)
	local ret = {}
	local url = "http://www.dhtv.cn/api/programs/?ac=get&_channel=" .. vid
	local text = kola.wget(url, false)

	if text == nil then
		return '{}'
	end
	text = string.sub(text, 2, #text - 1)
	if text == nil then
		return '{}'
	end
	text = string.sub(text, 2, #text - 1)

	local js = cjson.decode(text)
	for k,v in ipairs(js.data) do
		ret[k] = to_epg(v.start, v.name)
		if k > 1 then
			ret[k-1].duration = os.difftime(ret[k].time, ret[k-1].time)
		end
	end

	return cjson.encode(ret)
end
function get_channel(albumName)
	--print(albumName)
	local channel_function = {
			get_channel_tvmao,
			--get_channel_jstv,
			--get_channel_pptv,
			--get_channel_cutv,
			--get_channel_cntv,
			--get_channel_wasu,
			--get_channel_qqtv,
			--get_channel_sohutv,
			--get_channel_smgbbtv
	}

	for _, cfunc in ipairs(channel_function) do
		ret = cfunc(albumName)
		if ret then
			return ret
		end
	end

	return '{}'
end
