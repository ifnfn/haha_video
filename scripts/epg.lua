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

local function to_str(ret)
	if ret then return cjson.encode(ret) end
end

function get_channel_tvmao(albumName)
	local name_key = {
		['CCTV News']      = 'cctv19',
		['CCTV 风云足球']   = 'cctvpayfee1',
		['CCTV 风云音乐']   = 'cctvpayfee2',
		['CCTV 第一剧场']   = 'cctvpayfee3',
		['CCTV 风云剧场']   = 'cctvpayfee4',
		['CCTV 世界地理']   = 'cctvpayfee5',
		['CCTV 电视指南']   = 'cctvpayfee6',
		['CCTV 怀旧剧场']   = 'cctvpayfee7',
		['CCTV 国防军事']   = 'cctvpayfee8',
		['CCTV 女性时尚']   = 'cctvpayfee9',
		['CCTV 戏曲国际']   = 'cctvpayfee11',
		['CCTV 高尔夫网球'] = 'cctvpayfee13',
		['CCTV 文化精品']   = 'cctvpayfee14',
		['留学世界']        = 'cctvpayfee24',
		['CCTV 央视台球']   = 'cctvpayfee36',
		['CCTV 证券资讯']   = 'cctvcj', -- why?
		['CCTV 发现之旅']   = 'cctvfxzl',
		['CCTV 俄语频道']   = 'cctvr',
		['CCTV 阿语频道']   = 'cctva',
		['CCTV 法语频道']   = 'cctvf',
		['CCTV 西语频道']   = 'cctv17',

		-- 卫视
		['安徽']   = 'ahtv1',
		['北京']   = 'btv1',
		['重庆']   = 'ccqtv1',
		['东方']   = 'dongfang1',
		['东南']   = 'fjtv2',
		['广东']   = 'gdtv1',
		['广西']   = 'guanxi1',
		['甘肃']   = 'gstv1',
		['贵州']   = 'guizoutv1',
		['海峡']   = 'hxtv',
		['河北']   = 'hebei1',
		['河南']   = 'hntv1',
		['黑龙江']  = 'hljtv1',
		['湖南']   = 'hunantv1',
		['湖南卫视-高清'] = 'hunantv1',
		['湖北']   = 'hubei1',
		['吉林']   = 'jilin1',
		['江西']   = 'jxtv1',
		['江苏']   = 'jstv1',
		['康巴']   = 'kamba-tv',
		['辽宁']   = 'lntv1',
		['旅游']   = 'tctc1',
		['内蒙古']  = 'nmgtv1',
		['宁夏']   = 'nxtv2',
		['青海']   = 'qhtv1',
		['深圳']   = 'sztv1',
		['山东']   = 'sdtv1',
		['陕西']   = 'shxitv1',
		['山西']   = 'sxtv1',
		['四川']   = 'sctv1',
		['天津']   = 'tjtv1',
		['西藏']   = 'xizangtv2',
		['厦门']   = 'xmtv5',
		['新疆']   = 'xjtv1',
		['香港']   = 'hks',
		['延边']   = 'yanbian1',
		['云南']   = 'yntv1',
		['浙江']   = 'zjtv1',
		['兵团']   = 'bingtuan',
		['华娱']   = 'huayu1',
		['健康']   = 'jkwshk',
		['莲花']   = 'lotusbtv',
		['南方']   = 'nanfang6',
		['农林']   = 'shxitv9',
		['三沙']   = 'sanshatv',
		['凤凰卫视-香港台'] = 'phoenixhk',
		['凤凰卫视-中文台'] = 'phoenix1',
		['凤凰卫视-资讯台'] = 'phoenix-infonews',

		-- 安徽
		['安徽-经济'] = 'ahtv2',
		['安徽-影视'] = 'ahtv3',
		['安徽-综艺'] = 'ahtv4',
		['安徽-公共'] = 'ahtv5',
		['安徽-科教'] = 'ahtv6',
		['安徽-人物'] = 'ahtv7',
		['安徽-国际'] = 'ahtv8',
		['安庆-公共'] = 'aqgg',
		['安庆-黄梅戏'] = nil,
		['安庆-生活']    = nil,
		['安庆-新闻综合'] = 'aqxw',
		['百姓健康']     = 'chtv',
		['蚌埠-公共'] = 'ahbbtv3',
		['蚌埠-生活'] = 'ahbbtv2',
		['蚌埠-新闻'] = 'ahbbtv1',

		['天津-国际'] = 'tjgj',
		['天津-新闻'] = 'tjtv2',
		['天津-文艺'] = 'tjtv3',
		['天津-影视'] = 'tjtv4',
		['天津-都市'] = 'tjtv5',
		['天津-体育'] = 'tjtv6',
		['天津-科教'] = 'tjtv7',
		['天津-少儿'] = 'tjtv8',
		['天津-公共'] = 'tjtv9',

		['北京-文艺'] = 'btv2',
		['北京-科教'] = 'btv3',
		['北京-影视'] = 'btv4',
		['北京-财经'] = 'btv5',
		['北京-体育'] = 'btv6',
		['北京-生活'] = 'btv7',
		['北京-青年'] = 'btv8',
		['北京-新闻'] = 'btv9',
		['北京-卡酷少儿'] = 'btv10',

		['长沙-女性'] = 'changshawumon1',
		['长沙-政法'] = 'changshawumon2',
		['长沙-经贸'] = 'changshawumon3',
		['长沙-新闻'] = 'changshawumon4',
		['长沙-公共'] = 'changshawumon5',

		['长春-综合'] = 'ctv1',
		['长春-娱乐'] = 'ctv2',
		['长春-市民'] = 'ctv3',
		['长春-商业'] = 'ctv4',
		['长春-新知'] = 'ctv5',

		['大庆-新闻'] = 'daqingtv1',
		['大庆-百湖'] = 'daqingtv2',
		['大庆-影视'] = 'daqingtv3',
		['大庆-直播'] = nil, -- ‘daqingtv4’

		['常州-新闻'] = 'changzhou1',
		['常州-都市'] = 'changzhou2',
		['常州-生活'] = 'changzhou3',
		['常州-公共'] = 'changzhou4',

		['沈阳-新闻'] = 'lnsy1',
		['沈阳-经济'] = 'lnsy2',
		['沈阳-公共'] = 'lnsy3',

		['成都-新闻'] = 'chengdu1',
		['成都-经济'] = 'chengdu2',
		['成都-都市'] = 'chengdu3',
		['成都-影视'] = 'chengdu4',
		['成都-公共'] = 'chengdu5',
		['成都-少儿'] = 'cdtv-6',

		['大连-购物'] = nil,
		['大连-新闻'] = 'dalian1',
		['大连-生活'] = 'dalian2',
		['大连-公共'] = 'dalian3',
		['大连-文体'] = 'dalian4',
		['大连-影视'] = 'dalian5',
		['大连-少儿'] = 'dalian6',
		['大连-财经'] = 'dalian7',

		['电子体育'] = 'esports',
		['东方财经'] = 'sitv14',
		['东方电影'] = 'dfmv1',
		['东方购物'] = 'shhai10',

		['东莞-公共'] = 'gddg1',
		['东莞-综合'] = 'gddg2',

		['鄂尔多斯一套'] = nil,
		['鄂尔多斯二套'] = nil,
		['鄂尔多斯三套'] = nil,
		['鄂尔多斯四套'] = nil,

		['恩施-公共'] = nil,
		['恩施-新闻'] = nil,
		['恩施-综艺'] = nil,

		['福建-综合'] = 'fjtv1',
		['福建-公共'] = 'fjtv3',
		['福建-新闻'] = 'fjtv4',
		['福建-电视剧']   = 'fjtv5',
		['福建-都市'] = 'fjtv6',
		['福建-经济'] = 'fjtv7',
		['福建-体育'] = 'fjtv8',
		['福建-少儿'] = 'fjtv9',

		['福州-新闻'] = 'fztv1',
		['福州-生活'] = 'fztv3',
		['福州-影视'] = 'fztv2',
		['福州-少儿'] = 'fztv-baby',

		['高尔夫.网球'] = nil,
		['高尔夫'] = nil,

		['广东-会展'] = 'huizahn',
		['广东-现代教育'] = nil,
		['广东-珠江电影'] = 'gdtv2',
		['广东-体育'] = 'gdtv3',
		['广东-公共'] = 'gdtv4',
		['广东-珠江'] = 'gdtv5',
		['广东-新闻'] = 'gdtv6',
		['广东-嘉佳卡通'] = 'gdtv7',

		['广西-国际'] = 'gxgj',
		['广西-交通'] = nil,
		['广西-综艺'] = 'guanxi2',
		['广西-都市'] = 'guanxi3',
		['广西-影视'] = 'guanxi5',
		['广西-公共'] = 'guanxi4',
		['广西-资讯'] = 'guanxi7',

		['广州-综合'] = 'gztv1',
		['广州-新闻'] = 'gztv2',
		['广州-竞赛'] = 'gztv3',
		['广州-影视'] = 'gztv4',
		['广州-英语'] = 'gztv5',
		['广州-经济'] = 'gztv6',
		['广州-少儿'] = 'gztv7',

		['贵阳-经济'] = 'gytv2',
		['贵州-购物'] = nil,
		['贵州-经济'] = nil,

		['海南-文体']    = 'hnwt',
		['海南-综合']    = 'hainantv1',
		['海南-新闻']    = 'hainantv2',
		['海南-公共']    = 'hainantv3',
		['海南-青少科教'] = 'hainantv5',
		['海南-影视剧']   = 'hnysj',

		['邯郸-公共'] = nil,
		['邯郸-民生'] = nil,
		['邯郸-新闻'] = nil,

		['杭州-综合'] = 'htv1',
		['杭州-西湖明珠'] = 'htv2',
		['杭州-生活'] = 'htv3',
		['杭州-影视'] = 'htv4',
		['杭州-少儿'] = 'htv5',
		['杭州-导视'] = 'htv6',
		['杭州-房产'] = nil,  --'htv66'

		['河北-经济'] = 'hebei2',
		['河北-都市'] = 'hebei3',
		['河北-影视'] = 'hebei4',
		['河北-少儿'] = 'hebei5',
		['河北-公共'] = 'hebei6',
		['河北-农民'] = 'hebei7',

		['合肥-教育'] = nil,
		['合肥-新闻'] = 'hefeitv1',
		['合肥-生活'] = 'hefeitv2',
		['合肥-教育'] = 'hefeitv3',
		['合肥-财经'] = 'hefeitv4',
		['合肥-影院'] = 'hefeitv5',
		['合肥-文体'] = 'wentibolan',

		['河南-都市']    = 'hntv2',
		['河南-民生']    = 'hntv3',
		['河南-法制']    = 'hntv4',
		['河南-电视剧']  = 'hntv5',
		['河南-新闻']    = 'hntv6',
		['河南-欢腾购物'] = 'hntv7',
		['河南-公共']    = 'hntv8',
		['河南-新农村']  = 'hntv9',
		['河南-国际']    = 'hngj',

		['菏泽-新闻'] = 'hztv1',
		['菏泽-经济'] = 'hztv2',
		['菏泽-综艺'] = 'hztv3',

		['黑龙江-影视'] = 'hljtv2',
		['黑龙江-文艺'] = 'hljtv3',
		['黑龙江-都市'] = 'hljtv4',
		['黑龙江-新闻'] = 'hljtv5',
		['黑龙江-公共'] = 'hljtv6',
		['黑龙江-第七'] = 'hljtv7',
		['黑龙江-导视'] = 'hljdaoshi',

		['湖北-碟市'] = nil,
		['湖北-综合'] = 'hubei2',
		['湖北-影视'] = 'hubei3',
		['湖北-教育'] = 'hubei4',
		['湖北-体育'] = 'hubei5',
		['湖北-公共'] = 'hubei7',
		['湖北-经视'] = 'hubei8',
		['睛彩-湖北'] = nil,
		['湖北-垄上'] = 'jztv2',

		['湖南-经视'] = 'hnetv1',
		['湖南-经视HD'] = 'hnetv1',
		['湖南-都市'] = 'hnetv2',
		['湖南-金鹰纪实'] = 'hnetv3',
		['湖南-金鹰卡通'] = 'hunantv2',
		['湖南-娱乐'] = 'hunantv3',
		['湖南-电视剧'] = 'hunantv4',
		['湖南-公共'] = 'hunantv5',
		['湖南-潇湘电影'] = 'hunantv6',
		['湖南-国际'] = 'hunantv7',
		['湖南-先锋纪录'] = 'documentary-channel',
		['湖南-先锋乒羽'] = 'xfby',

		['黄石-新闻'] = 'hbhstv1',
		['黄石-公共'] = 'hbhstv2',
		['黄石-都市'] = 'hbhstv3',
		['黄石-移动'] = nil,
		['黄石-综合'] = nil,

		['惠州-新闻'] = 'gdhztv1',
		['惠州-公共'] = 'gdhztv2',

		['吉林-东北戏曲'] = nil,
		['吉林-篮球'] = nil,
		['吉林-都市'] = 'jilin2',
		['吉林-生活'] = 'jilin3',
		['吉林-影视'] = 'jilin4',
		['吉林-乡村'] = 'jilin5',
		['吉林-公共'] = 'jilin6',
		['吉林-综艺'] = 'jilin7',

		['山东-国际'] = nil,
		['山东-教育'] = 'sdetv1',
		['山东-齐鲁'] = 'sdtv2',
		['山东-体育'] = 'sdtv3',
		['山东-农科'] = 'sdtv4',
		['山东-公共'] = 'sdtv5',
		['山东-少儿'] = 'sdtv6',
		['山东-影视'] = 'sdtv7',
		['山东-综艺'] = 'sdtv8',
		['山东-生活'] = 'sdtv9',

		['济南-泉天下'] = nil,
		['济南-新闻'] = 'jntv1',
		['济南-新闻高清'] = 'jntv1',
		['济南-都市'] = 'jntv2',
		['济南-影视'] = 'jntv3',
		['济南-娱乐'] = 'jntv4',
		['济南-生活'] = 'jntv5',
		['济南-商务'] = 'jntv6',
		['济南-少儿'] = 'jntv7',

		['家庭理财'] = 'jiatinglicai',
		['建始-综合'] = nil,

		['江门-公共'] = 'jmtv1',
		['江门-综合'] = 'jmtv2',
		['江门-教育'] = 'jmtv3',

		['江苏-综艺'] = 'jstv2',
		['江苏-城市'] = 'jstv3',
		['江苏-影视'] = 'jstv4',
		['江苏-靓妆'] = 'jstv5',
		['江苏-体育'] = 'jstv6',
		['江苏-优漫卡通'] = 'jstv7',
		['江苏-公共'] = 'jstv8',
		['江苏-教育'] = 'jstv9',
		['江苏-国际'] = 'jstv10',
		['江苏-学习'] = nil,
		['江苏-好享购物'] = nil,

		['江西-都市']    = 'jxtv2',
		['江西-经济']    = 'jxtv3',
		['江西-影视']    = 'jxtv4',
		['江西-公共']    = 'jxtv5',
		['江西-少儿']    = 'jxtv6',
		['江西-红色经典'] = 'jxtv7',
		['江西-电视指南'] = 'jxtv-guide',
		['江西-风尚购物'] = 'fstvgo',
		['江西-移动电视'] = nil,

		['江阴-民生'] = nil,
		['江阴-新闻'] = nil,

		['金华-都市'] = nil,
		['金华-教育'] = 'jinhuatv2',
		['金华-经济'] = 'jinhuatv3',
		['金华-新闻'] = 'jinhuatv1',

		['睛彩平顶山'] =  nil,
		['经典电影'] = nil,

		['荆门-新闻'] = 'hbjmtv1',
		['荆门-公共'] = 'hbjmtv4',
		['荆门-经视'] = 'hbjmtv3',
		['荆门-农谷'] = 'hbjmtv2',

		['劲爆体育'] = 'sitv4',
		['快乐宠物'] = 'pets-tv',
		['快乐垂钓'] = 'kuailechuidiao',
		['湖南-快乐购'] = 'happigo',

		['昆明-公共频道'] = nil,
		['昆明-新闻综合'] = 'kmtv1',
		['昆明-科学教育'] = 'kmedu',
		['昆明-阳光频道'] = 'kmtv2',
		['昆明-健康频道'] = 'kmtv3',
		['昆明-经济生活'] = 'kmtv4',
		['昆明-影视频道'] = 'kmtv5',
		['昆明-春城频道'] = 'kmtv6',

		['温州-新闻综合'] = 'wztv1',
		['温州-经济科教'] = 'wztv2',
		['温州-都市生活'] = 'wztv3',
		['温州-公共民生'] = 'wztv4',
		['温州-瓯江先锋'] = 'wztv5',

		['乌鲁木齐-新闻(汉)'] = 'utv1',
		['乌鲁木齐-新闻(维)'] = 'utv2',
		['乌鲁木齐-影视'] = 'utv3',
		['乌鲁木齐-生活'] = 'utv4',
		['乌鲁木齐-文体'] = 'utv5',
		['乌鲁木齐-儿童'] = 'utv6',

		['柳州-新闻'] = 'gxlztv1',
		['柳州-科教'] = 'gxlztv2',
		['柳州-公共'] = 'gxlztv3',
		['魅力时尚'] = nil,
		['魅力时装'] = nil,
		['魅力音乐'] = 'sitv5',

		['MTV音乐'] = nil,

		['南昌-新闻'] = 'nanchang1',
		['南昌-公共'] = 'nanchang2',
		['南昌-资讯'] = 'nanchang3',
		['南昌-都市'] = 'nanchang4',

		['南方-经济'] = 'nanfang1',
		['南方-综艺'] = 'nanfang3',
		['南方-影视'] = 'nanfang4',
		['南方-少儿'] = 'nanfang5',

		['南京-新闻'] = 'njtv1',
		['南京-影视'] = 'njtv2',
		['南京-教科'] = 'njtv3',
		['南京-生活'] = 'njtv4',
		['南京-娱乐'] = 'njtv5',
		['南京-十八'] = 'njtv6',
		['南京-少儿'] = 'njtv7',

		['南宁-新闻'] = 'nanningtv1',
		['南宁-影视'] = 'nanningtv2',
		['南宁-都市'] = 'nanningtv3',
		['南宁-公共'] = 'nanningtv4',

		['宁波-新闻'] = 'nbtv1',
		['宁波-社会'] = 'nbtv2',
		['宁波-都市'] = 'nbtv3',
		['宁波-影视剧'] = 'nbtv4',
		['宁波-少儿'] = 'nbtv5',

		['宁夏-公共'] = 'nxtv1',
		['宁夏-经济'] = 'nxtv3',
		['宁夏-影视'] = 'nxtv4',
		['宁夏-少儿'] = 'nxtv5',

		['欧洲足球'] = 'europefootball',

		['衢州-公共'] = nil,
		['衢州-经济'] = nil,
		['衢州-生活'] = nil,
		['衢州-新闻'] = nil,
		['全纪实'] = 'sitv11',
		['热播剧场'] = nil,
		['三佳购物'] = 'ttcjmall',

		['厦门-新闻'] = 'xmtv1',
		['厦门-纪实'] = 'xmtv2',
		['厦门-生活'] = 'xmtv3',
		['厦门-影视'] = 'xmtv4',

		['陕西-新闻'] = 'shxitv2',
		['陕西-都市'] = 'shxitv3',
		['陕西-生活'] = 'shxitv4',
		['陕西-体育'] = 'shxitv8',
		['陕西-新闻'] = nil,

		['上海-炫动卡通'] = 'toonmax1',
		['上海-教育']    = 'shedu1',
		['上海-新闻']    = 'shhai1',
		['上海-第一财经'] = 'shhai2',
		['上海-生活时尚'] = 'shhai3',
		['上海-星尚']     = 'shhai3',
		['上海-电视剧']   = 'shhai4',
		['上海-五星体育'] = 'shhai5',
		['上海-纪实频道'] = 'shhai6',
		['上海-新娱乐']   = 'shhai7',
		['上海-艺术人文'] = 'shhai8',
		['上海-外语ICS'] = 'shhai9',

		['绍兴-影视'] = 'shaoxin1',
		['绍兴-公共'] = 'shaoxin2',
		['绍兴-新闻'] = 'shaoxin3',

		['深圳-都市']  = 'sztv2',
		['深圳-电视剧']= 'sztv3',
		['深圳-财经']  = 'sztv4',
		['深圳-娱乐']  = 'sztv5',
		['深圳-体育']  = 'sztv6',
		['深圳-少儿']  = 'sztv7',
		['深圳-公共']  = 'sztv8',
		['深圳-DV生活']= 'sztv11',

		['石家庄-新闻'] = 'shijiazhuang1',
		['石家庄-娱乐'] = 'shijiazhuang2',
		['石家庄-生活'] = 'shijiazhuang3',
		['石家庄-都市'] = 'shijiazhuang4',

		------------------------------------------------
		['收藏天下'] = 'shoucangtiaxia',
		['四海钓鱼'] = 'bamc4',
		['天元围棋'] = 'tianyuanweiqi',
		['职业指南'] = 'bamc16',
		['TVB8']    = 'tvb8',
		------------------------------------------------

		['四川-旅游'] = 'sctv2',
		['四川-经济'] = 'sctv3',
		['四川-新闻'] = 'sctv4',
		['四川-影视'] = 'sctv5',
		['四川-儿童'] = 'sctv7',
		['四川-公共'] = 'sctv9',

		['苏州-新闻'] = 'suzhoutv1',
		['苏州-经济'] = 'suzhoutv2',
		['苏州-生活'] = 'suzhoutv3',
		['苏州-电影'] = 'suzhoutv4',
		['苏州-资讯'] = 'suzhoutv5',

		['遂宁-公共'] = nil,
		['遂宁-影视'] = nil,
		['遂宁-新闻'] = nil,
		['遂宁-直播'] = nil,

		['泰州-新闻'] = 'tztv1',

		['唐山-新闻'] = 'tssv1',
		['唐山-生活'] = 'tssv2',
		['唐山-影视'] = 'tssv3',
		['唐山-公共'] = 'tssv4',

		['通化-公共'] = nil,
		['通化-科教'] = nil,
		['通化-新闻'] = nil,

		['威海-新闻'] = 'weihai1',
		['威海-公共'] = 'weihai2',

		['芜湖-新闻'] = 'wuhutv1',
		['芜湖-生活'] = 'wuhutv2',
		['芜湖-徽商'] = 'wuhutv3',
		['芜湖-教育'] = 'wuhutv3',

		['无锡-新闻'] = 'wuxi1',
		['无锡-娱乐'] = 'wuxi2',
		['无锡-经济'] = 'wuxi4',
		['无锡-生活'] = 'wuxi5',
		['无锡-都市'] = 'wuxi7',

		['武汉-新闻'] = 'whtv1',
		['武汉-文艺'] = 'whtv2',
		['武汉-科教'] = 'whtv3',
		['武汉-影视'] = 'whtv4',
		['武汉-体育'] = 'whtv5',
		['武汉-外语'] = 'whtv6',
		['武汉-海外'] = 'whtv6',
		['武汉-少儿'] = 'whtv7',
		['武汉-少儿'] = 'whtv7',

		['西安-新闻'] = 'xian1',
		['西安-白鸽'] = 'xian2',
		['西安-资讯'] = 'xian3',
		['西安-影视'] = 'xian4',
		['西安-健康'] = 'xian5',
		['西安-综艺'] = 'xian6',

		['西藏藏语'] = 'xizangtv1',

		['西宁-生活'] = 'xining-life',
		['西宁-新闻'] = 'xining-news',
		['西宁-夏都房车'] = nil,
		['西宁-文化先锋'] = nil,

		['新疆-卫星频道(汉)'] = 'xjtv1',
		['新疆-卫星频道(维)'] = 'xjtv2',
		['新疆-卫星频道(哈)'] = 'xjtv3',
		['新疆-综艺(汉)'] = 'xjtv4',
		['新疆-综艺(维)'] = 'xjtv5',
		['新疆-影视(汉)'] = 'xjtv6',
		['新疆-经济(汉)'] = 'xjtv7',
		['新疆-综艺(哈)'] = 'xjtv8',
		['新疆-经济(维)'] = 'xjtv9',
		['新疆-体育(汉)']= 'xjtv10',
		['新疆-法制信息'] = 'xjtv11',
		['新疆-少儿'] = 'xjtv12',

		['徐州-新闻'] = 'xztv1',
		['徐州-经济'] = 'xztv2',
		['徐州-文艺'] = 'xztv3',
		['徐州-公共'] = 'xztv4',

		['雅安-新闻'] = nil,
		['雅安-雨城电视台'] = nil,

		['盐城一台'] = 'yanchengtv1',
		['盐城二台'] = 'yanchengtv2',
		['盐城三台'] = 'yanchengtv3',
		['盐城四台'] = 'yanchengxk', -- TODO

		['壹电视新闻台'] = 'nexttv-news',

		['宜宾-新闻'] = 'scybtv1',
		['宜宾-公共'] = 'scybtv2',

		['义乌-新闻'] = 'zjyiwu1',
		['义乌-商贸'] = 'zjyiwu2',
		['义乌-电视剧'] = 'zjyiwu3',
		['义乌-公共'] = nil,

		['银川-文体'] = 'yinchuang1',
		['银川-生活'] = 'yinchuang2',
		['银川-公共'] = 'yinchuang3',

		['英语辅导'] = 'english-teaching',
		['优优宝贝'] = 'bamc3',
		['游戏风云hd'] = 'sitv2',
		['游戏竞技'] = 'gtv-youxi',

		['云南-都市'] = nil,
		['云南-经济'] = 'yntv2',
		['云南-旅游'] = 'yntv3',
		['云南-娱乐'] = 'yntv4',
		['云南-影视剧']   = 'yntv5',
		['云南-公共'] = 'yntv6',
		['云南-少儿'] = 'yntv8',
		['云南-国际'] = 'yntv9',

		['孕育指南'] = 'cctvpayfee32',

		['枣庄-公共'] = 'zaozhuang2',
		['枣庄-新闻'] = 'zaozhuang3',
		['枣庄-生活'] = nil,
		['枣庄-教育'] = 'ZAOZHUANG1',

		['张家港-生活'] = nil,
		['张家港-新闻'] = nil,

		['浙江-钱江']   = 'zjtv2',
		['浙江-经视']   = 'zjtv3',
		['浙江-青少科教']= 'zjtv4',
		['浙江-科教']   = 'zjtv4',
		['浙江-影视']   = 'zjtv5',
		['浙江-6频道']  = 'zjtv6',
		['浙江-公共']   = 'zjtv7',
		['浙江-少儿']   = 'zjtv8',
		['浙江-国际']   = 'zjtv9',
		['浙江-新农村'] = nil,
		['浙江-购物']    = nil,
		['浙江-民生休闲'] = nil,
		['浙江-留学世界'] = 'CCTVPAYFEE24',

		['郑州-儿童'] = 'zhengzhoutv5',
		['郑州-商都'] = 'zhengzhoutv2',
		['郑州-时政'] = 'zhengzhoutv1',
		['郑州-文体'] = 'ZHENGZHOUTV3',
		['郑州-影视'] = 'ZHENGZHOUTV6',

		['中国教育一'] = 'cetv1',
		['中国教育二'] = 'cetv2',
		['中国教育三'] = 'cetv3',

		['重庆-汽摩'] = nil,
		['重庆-手持电视'] = nil,
		['重庆-移动'] = nil,
		['重庆-财经'] = 'cqtvxcj',
		['重庆-新财经'] = 'cqtvxcj',
		['重庆-影视'] = 'ccqtv2',
		['重庆-新闻'] = 'ccqtv3',
		['重庆-科教'] = 'ccqtv4',
		['重庆-都市'] = 'ccqtv5',
		['重庆-娱乐'] = 'ccqtv6',
		['重庆-生活'] = 'ccqtv7',
		['重庆-时尚'] = 'ccqtv8',
		['重庆-公共'] = 'ccqtv9',
		['重庆-少儿'] = 'ccqtv10',

		['珠海-生活服务'] = 'zhtv2',
		['珠海-新闻综合'] = 'zhtv1',

		['山西-黄河'] = '',
		['山西-经济'] = 'sxtv2',
		['山西-影视'] = 'sxtv3',
		['山西-科教'] = 'sxtv4',
		['山西-公共'] = 'sxtv5',
		['山西-少儿'] = 'sxtv6',

		['太原-新闻'] = 'sxtytv1',
		['太原-百姓'] = 'sxtytv2',
		['太原-法制'] = 'sxtytv3',
		['太原-影视'] = 'sxtytv4',
		['太原-文体'] = 'sxtytv5',

		['青岛-新闻'] = 'sdqd1',
		['青岛-生活'] = 'sdqd2',
		['青岛-影视'] = 'sdqd3',
		['青岛-财经'] = 'sdqd4',
		['青岛-都市'] = 'sdqd5',
		['青岛-青少旅游'] = 'sdqd6',
		['青岛-党建'] = 'sdqd7',
		['青岛-休闲'] = nil,

		['辽宁-都市'] = 'lntv2',
		['辽宁-影视剧']   = 'lntv3',
		['辽宁-购物'] = 'lntv4',
		['辽宁-教育青少'] = 'lntv5',
		['辽宁-生活'] = 'lntv6',
		['辽宁-公共'] = 'lntv7',
		['辽宁-北方'] = 'lntv8',
		['辽宁-经济'] = 'LNTV-FINANCE',
		['绵阳-公共'] = nil,
		['绵阳-交通'] = nil,
		['绵阳-教育'] = 'scmytv4',
		['绵阳-科技'] = 'scmytv3',
		['绵阳-旅游'] = 'scmytv5',
		['绵阳-新农村'] = nil,
		['绵阳-综合'] = 'scmytv1',
		['绵阳-都市'] = 'scmytv2',

		['南充-综合'] = 'scnctv1',
		['南充-公共'] = 'scnctv2',
		['南充-科教'] = 'scnctv3',
		['南充-文娱'] = 'scnctv4',
		['南充-资讯'] = 'scnctv5',

		['舟山-公共'] = nil,
		['舟山-就业'] = nil,
		['舟山-旅游'] = nil,
		['舟山-生活'] = 'zjzs-life',
		['舟山-新闻'] = 'zjzs-zh',
		['舟山-影视'] = 'zjzs-movie',

		['哈尔滨-新闻'] = 'hrbtv1',
		['哈尔滨-都市'] = 'hrbtv2',
		['哈尔滨-生活'] = 'hrbtv3',
		['哈尔滨-娱乐'] = 'hrbtv4',
		['哈尔滨-影视'] = 'hrbtv5',

		['盐城-电视二套'] = 'yanchengtv1',
		['盐城-电视三套'] = 'yanchengtv3',
		['盐城-电视一套'] = 'yanchengtv3',
		['盐城-七一小康'] = 'yanchengtv4',

		['扬州-新闻'] = 'yztv1',
		['扬州-城市'] = 'yztv2',
		['扬州-生活'] = 'yztv3',

		['淮安-新闻'] = 'hatv1',
		['淮安-公共'] = 'hatv2',
		['淮安-影视'] = 'hatv3',
		['家有购物'] = 'jiayougo',
		['荆州-新闻'] = 'jztv1',
		['兰州-公共'] = 'lanzhoutv4',
		['兰州-生活'] = 'lanzhoutv3',
		['兰州-体育'] = 'lanzhoutv2',
		['兰州-新闻'] = 'lanzhoutv1',
		['南通-党建'] = 'ntdj',
		['南通-明珠'] = 'jhmz',
		['南通-社教'] = 'nttv2',
		['南通-新闻'] = 'nttv1',
		['南通-信息'] = 'nttv4',
		['南通-娱乐'] = 'nttv3',
		['青海-都市'] = 'qhtv2',
		['青海-综合'] = 'qhtv3',
		['青海-影视'] = 'qhtv4',
		['烟台-经济'] = 'yantai2',
		['烟台-新闻'] = 'yantai1',
		['烟台-电视剧'] = 'yantai3',
		['烟台-都市'] = 'yantai4',
		['烟台-电影'] = 'yantai5',
		['阳光卫视'] = 'chinasun1'
	}

	vid = get_vid(name_key, albumName)

	if vid == nil and string.find(albumName, "CCTV") then
		aname = string.gsub(albumName, "-", "")
		vid = rex.match(aname, '(CCTV\\d+)')
		if vid == nil then
			return nil
		end
	end

	if vid == nil then
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

	return to_str(ret)
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

	return to_str(ret)
end

function get_channel(albumName)
	--print(albumName)
	local channel_function = {
			get_channel_tvmao,
			--get_channel_letv,
	}

	for _, cfunc in ipairs(channel_function) do
		ret = cfunc(albumName)
		if ret then
			return ret
		end
	end

	return '{}'
end
