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
	name_key['华娱']   = 'huayu1'
	name_key['健康']   = 'jkwshk'
	name_key['莲花']   = 'lotusbtv'
	name_key['南方']   = 'nanfang6'
	name_key['农林']   = 'shxitv9'
	name_key['卡酷少儿']   = 'btv10'
	name_key['三沙']   = 'sanshatv'
	name_key['炫动卡通']   = 'toonmax1'
	name_key['凤凰卫视-香港台'] = 'phoenixhk'
	name_key['凤凰卫视-中文台'] = ''
	name_key['凤凰卫视-资讯台'] = 'phoenix-infonews'

	-- 安徽
	name_key['安徽-经济生活'] = 'ahtv2'
	name_key['安徽-影视频道'] = 'ahtv3'
	name_key['安徽-综艺频道'] = 'ahtv4'
	name_key['安徽-公共频道'] = 'ahtv5'
	name_key['安徽-科教频道'] = 'ahtv6'
	name_key['安徽-人物频道'] = 'ahtv7'
	name_key['安徽-国际频道'] = 'ahtv8'
	name_key['安庆-公共频道'] = 'aqgg'
	name_key['安庆-黄梅戏'] = nil
	name_key['安庆-生活']    = nil
	name_key['安庆-新闻综合'] = 'aqxw'
	name_key['百姓健康']     = 'chtv'
	name_key['蚌埠-公共频道'] = 'ahbbtv3'
	name_key['蚌埠-生活频道'] = 'ahbbtv2'
	name_key['蚌埠-新闻综合'] = 'ahbbtv1'

	name_key['天津-新闻'] = 'tjtv2'
	name_key['天津-文艺'] = 'tjtv3'
	name_key['天津-影视'] = 'tjtv4'
	name_key['天津-都市'] = 'tjtv5'
	name_key['天津-体育'] = 'tjtv6'
	name_key['天津-科教'] = 'tjtv7'
	name_key['天津-少儿'] = 'tjtv8'
	name_key['天津-公共'] = 'tjtv9'

	name_key['北京-文艺'] = 'btv2'
	name_key['北京-科教'] = 'btv3'
	name_key['北京-影视'] = 'btv4'
	name_key['北京-财经'] = 'btv5'
	name_key['北京-体育'] = 'btv6'
	name_key['北京-生活'] = 'btv7'
	name_key['北京-青年'] = 'btv8'
	name_key['北京-新闻'] = 'btv9'

	name_key['长沙-女性'] = 'changshawumon1'
	name_key['长沙-政法'] = 'changshawumon2'
	name_key['长沙-经贸'] = 'changshawumon3'
	name_key['长沙-新闻'] = 'changshawumon4'
	name_key['长沙-公共'] = 'changshawumon5'

	name_key['长春-综合频道'] = 'ctv1'
	name_key['长春-娱乐频道'] = 'ctv2'
	name_key['长春-新知频道'] = 'ctv5'
	name_key['常州-新闻综合'] = 'changzhou1'
	name_key['常州-都市频道'] = 'changzhou2'
	name_key['常州-生活频道'] = 'changzhou3'
	name_key['常州-公共频道'] = 'changzhou4'

	name_key['沈阳-公共频道'] = 'lnsy3'
	name_key['沈阳-经济频道'] = 'lnsy2'
	name_key['沈阳-新闻综合'] = 'lnsy1'
	name_key['成都-新闻综合'] = 'chengdu1'
	name_key['成都-经济资讯'] = 'chengdu2'
	name_key['成都-都市生活'] = 'chengdu3'
	name_key['成都-影视文艺'] = 'chengdu4'
	name_key['成都-公共频道'] = 'chengdu5'
	name_key['成都-少儿频道'] = 'cdtv-6'

	name_key['大连-乐天购物'] = nil
	name_key['大连-新闻频道'] = 'dalian1'
	name_key['大连-生活频道'] = 'dalian2'
	name_key['大连-公共频道'] = 'dalian3'
	name_key['大连-文体频道'] = 'dalian4'
	name_key['大连-影视频道'] = 'dalian5'
	name_key['大连-少儿频道'] = 'dalian6'
	name_key['大连-财经频道'] = 'dalian7'

	name_key['电子体育'] = 'esports'
	name_key['东方财经'] = 'sitv14'
	name_key['东方电影'] = 'dfmv1'
	name_key['东方购物'] = 'shhai10'

	name_key['东莞-公共频道'] = 'gddg1'
	name_key['东莞-综合频道'] = 'gddg2'

	name_key['鄂尔多斯一套'] = nil
	name_key['鄂尔多斯二套'] = nil
	name_key['鄂尔多斯三套'] = nil
	name_key['鄂尔多斯四套'] = nil

	name_key['恩施-公共频道'] = nil
	name_key['恩施-新闻频道'] = nil
	name_key['恩施-综艺频道'] = nil

	name_key['福建-综合'] = 'fjtv1'
	name_key['福建-公共'] = 'fjtv3'
	name_key['福建-新闻'] = 'fjtv4'
	name_key['福建-电视剧'] = 'fjtv5'
	name_key['福建-都市时尚'] = 'fjtv6'
	name_key['福建-经济'] = 'fjtv7'
	name_key['福建-体育'] = 'fjtv8'
	name_key['福建-少儿'] = 'fjtv9'

	name_key['福州-新闻'] = 'fztv1'
	name_key['福州-生活'] = 'fztv3'
	name_key['福州-影视'] = 'fztv2'
	name_key['福州-少儿'] = 'fztv-baby'

	name_key['高尔夫.网球'] = nil
	name_key['高尔夫'] = nil

	name_key['广东-会展频道'] = 'huizahn'
	name_key['广东-现代教育'] = nil
	name_key['广东-珠江电影'] = 'gdtv2'
	name_key['广东-体育频道'] = 'gdtv3'
	name_key['广东-公共频道'] = 'gdtv4'
	name_key['广东-珠江频道'] = 'gdtv5'
	name_key['广东-新闻频道'] = 'gdtv6'

	name_key['广西-国际频道'] = 'gxgj'
	name_key['广西-交通频道'] = nil
	name_key['广西-综艺频道'] = 'guanxi2'
	name_key['广西-都市频道'] = 'guanxi3'
	name_key['广西-影视频道'] = 'guanxi5'
	name_key['广西-公共频道'] = 'guanxi4'
	name_key['广西-资讯频道'] = 'guanxi7'

	name_key['广州-综合频道'] = 'gztv1'
	name_key['广州-新闻频道'] = 'gztv2'
	name_key['广州-竞赛频道'] = 'gztv3'
	name_key['广州-影视频道'] = 'gztv4'
	name_key['广州-英语频道'] = 'gztv5'
	name_key['广州-经济频道'] = 'gztv6'
	name_key['广州-少儿频道'] = 'gztv7'

	name_key['贵阳-经济生活'] = 'gytv2'
	name_key['贵州-家有购物1'] = nil
	name_key['贵州-经济频道'] = nil

	name_key['海南-文体']    = 'hnwt'
	name_key['海南-综合']    = 'hainantv1'
	name_key['海南-新闻']    = 'hainantv2'
	name_key['海南-公共']    = 'hainantv3'
	name_key['海南-青少科教'] = 'hainantv5'
	name_key['海南-影视剧']   = 'hnysj'

	name_key['邯郸-公共频道'] = nil
	name_key['邯郸-民生都市'] = nil
	name_key['邯郸-新闻综合'] = nil

	name_key['杭州-综合'] = 'htv1'
	name_key['杭州-明珠'] = 'htv2'
	name_key['杭州-生活'] = 'htv3'
	name_key['杭州-影视'] = 'htv4'
	name_key['杭州-少儿'] = 'htv5'
	name_key['杭州-导视'] = 'htv6'
	name_key['杭州-房产'] = 'htv66'

	name_key['河北-经济频道'] = 'hebei2'
	name_key['河北-都市频道'] = 'hebei3'
	name_key['河北-影视频道'] = 'hebei4'
	name_key['河北-少儿科教'] = 'hebei5'
	name_key['河北-公共频道'] = 'hebei6'
	name_key['河北-农民频道'] = 'hebei7'

	name_key['合肥-教育频道'] = nil
	name_key['合肥-新闻频道'] = 'hefeitv1'
	name_key['合肥-生活频道'] = 'hefeitv2'
	name_key['合肥-法制教育'] = 'hefeitv3'
	name_key['合肥-财经频道'] = 'hefeitv4'
	name_key['合肥-影院频道'] = 'hefeitv5'
	name_key['合肥-文体博览'] = 'wentibolan'

	name_key['河南-都市']    = 'hntv2'
	name_key['河南-民生']    = 'hntv3'
	name_key['河南-政法']    = 'hntv4'
	name_key['河南-电视剧']  = 'hntv5'
	name_key['河南-新闻']    = 'hntv6'
	name_key['河南-欢腾购物'] = 'hntv7'
	name_key['河南-公共']    = 'hntv8'
	name_key['河南-新农村']  = 'hntv9'
	name_key['河南-国际']    = 'hngj'

	name_key['黑龙江-影视频道'] = 'hljtv2'
	name_key['黑龙江-文艺频道'] = 'hljtv3'
	name_key['黑龙江-都市频道'] = 'hljtv4'
	name_key['黑龙江-新闻频道'] = 'hljtv5'
	name_key['黑龙江-公共频道'] = 'hljtv6'
	name_key['黑龙江-少儿频道'] = 'hljtv7'
	name_key['黑龙江-导视频道'] = 'hljdaoshi'

	name_key['湖北-碟市'] = ''
	name_key['湖北-综合频道'] = 'hubei2'
	name_key['湖北-影视频道'] = 'hubei3'
	name_key['湖北-教育频道'] = 'hubei4'
	name_key['湖北-体育生活'] = 'hubei5'
	name_key['湖北-公共频道'] = 'hubei7'
	name_key['湖北-经视频道'] = 'hubei8'
	name_key['睛彩-湖北'] = nil
	name_key['湖北-垄上'] = 'jztv2'

	name_key['湖南-经视'] = 'hnetv1'
	name_key['湖南-经视HD'] = 'hnetv1'
	name_key['湖南-都市'] = 'hnetv2'
	name_key['湖南-金鹰纪实'] = 'hnetv3'
	name_key['湖南-金鹰卡通'] = 'hunantv2'
	name_key['湖南-娱乐'] = 'hunantv3'
	name_key['湖南-电视剧'] = 'hunantv4'
	name_key['湖南-公共'] = 'hunantv5'
	name_key['湖南-潇湘电影'] = 'hunantv6'
	name_key['湖南-国际'] = 'hunantv7'

	name_key['黄石-都市'] = 'hbhstv3'
	name_key['黄石-新闻'] = 'hbhstv1'
	name_key['黄石-移动'] = nil
	name_key['黄石-综合'] = nil

	name_key['惠州一套'] = 'gdhztv1'
	name_key['惠州二套'] = 'gdhztv2'

	name_key['吉林-东北戏曲'] = nil
	name_key['吉林-篮球'] = nil
	name_key['吉林-都市'] = 'jilin2'
	name_key['吉林-生活'] = 'jilin3'
	name_key['吉林-影视'] = 'jilin4'
	name_key['吉林-乡村'] = 'jilin5'
	name_key['吉林-公共新闻'] = 'jilin6'
	name_key['吉林-综艺文化'] = 'jilin7'

	name_key['济南-泉天下'] = nil
	name_key['济南-新闻频道'] = 'jntv1'
	name_key['济南-都市频道'] = 'jntv2'
	name_key['济南-影视频道'] = 'jntv3'
	name_key['济南-娱乐频道'] = 'jntv4'
	name_key['济南-生活频道'] = 'jntv5'
	name_key['济南-商务频道'] = 'jntv6'
	name_key['济南-少儿频道'] = 'jntv7'

	name_key['家庭理财'] = 'jiatinglicai'
	name_key['建始-综合频道'] = nil

	name_key['江苏-综艺'] = 'jstv2'
	name_key['江苏-城市'] = 'jstv3'
	name_key['江苏-影视'] = 'jstv4'
	name_key['江苏-靓妆频道'] = 'jstv5'
	name_key['江苏-休闲'] = 'jstv6'
	name_key['江苏-体育休闲'] = 'jstv6'
	name_key['江苏-优漫卡通'] = 'jstv7'
	name_key['江苏-公共'] = 'jstv8'
	name_key['江苏-教育'] = 'jstv9'
	name_key['江苏-国际'] = 'jstv10'
	name_key['江苏-学习'] = nil
	name_key['江苏-好享购物'] = nil

	name_key['江西-都市']    = 'jxtv2'
	name_key['江西-经视']    = 'jxtv3'
	name_key['江西-影视']    = 'jxtv4'
	name_key['江西-公共']    = 'jxtv5'
	name_key['江西-少儿']     = 'jxtv6'
	name_key['江西-红色经典'] = 'jxtv7'
	name_key['江西-电视指南'] = 'jxtv-guide'
	name_key['江西-风尚购物'] = 'fstvgo'
	name_key['江西-移动电视'] = nil

	name_key['江阴-民生'] = nil
	name_key['江阴-新闻'] = nil

	name_key['金华-综合'] = 'jinhuatv1'
	name_key['金华-都市'] = nil
	name_key['金华-公共'] = nil

	name_key['睛彩平顶山'] =  nil
	name_key['经典电影'] = nil
	name_key['荆州-新闻综合'] = 'jztv1'
	name_key['劲爆体育'] = 'sitv4'
	name_key['快乐宠物'] = 'pets-tv'
	name_key['快乐垂钓'] = 'kuailechuidiao'
	name_key['快乐购'] = 'happigo'

	name_key['昆明2'] = nil
	name_key['昆明3'] = nil
	name_key['昆明6'] = nil

	name_key['昆明-新闻频道'] = 'kmtv1'

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

	name_key['柳州-新闻频道'] = 'gxlztv1'
	name_key['柳州-科教频道'] = 'gxlztv2'
	name_key['柳州-公共频道'] = 'gxlztv3'
	name_key['魅力时尚'] = nil
	name_key['魅力时装'] = nil
	name_key['魅力音乐'] = 'sitv5'

	name_key['绵阳-公共频道'] = nil
	name_key['绵阳-交通信息'] = nil
	name_key['绵阳-教育资讯'] = nil
	name_key['绵阳-科技频道'] = nil
	name_key['绵阳-旅游信息'] = nil
	name_key['绵阳-新农村信息'] = nil
	name_key['绵阳-综合频道'] = nil
	name_key['绵阳-综合信息'] = nil

	name_key['MTV音乐'] = nil

	name_key['南昌-新闻综合'] = 'nanchang1'
	name_key['南昌-公共频道'] = 'nanchang2'
	name_key['南昌-资讯政法'] = 'nanchang3'
	name_key['南昌-都市频道'] = 'nanchang4'

	name_key['南充-公共频道'] = nil -- 'scnctv2'
	name_key['南充-文娱频道'] = nil -- 'scnctv4'
	name_key['南充-新闻频道'] = 'scnctv1'
	name_key['南充-资讯频道'] = nil -- 'scnctv5'
	name_key['南充-科教频道'] = nil

	name_key['南方-经视频道'] = 'nanfang1'
	name_key['南方-综艺频道'] = 'nanfang3'
	name_key['南方-影视频道'] = 'nanfang4'
	name_key['南方-少儿频道'] = 'nanfang5'

	name_key['南京-新闻综合'] = 'njtv1'
	name_key['南京-影视频道'] = 'njtv2'
	name_key['南京-教科频道'] = 'njtv3'
	name_key['南京-生活频道'] = 'njtv4'
	name_key['南京-娱乐频道'] = 'njtv5'
	name_key['南京-十八频道'] = 'njtv6'
	name_key['南京-少儿频道'] = 'njtv7'

	name_key['南宁-新闻综合'] = 'nanningtv1'
	name_key['南宁-影视娱乐'] = 'nanningtv2'
	name_key['南宁-都市生活'] = 'nanningtv3'
	name_key['南宁-公共频道'] = 'nanningtv4'

	name_key['宁波-新闻综合'] = 'nbtv1'
	name_key['宁波-社会生活'] = 'nbtv2'
	name_key['宁波-文化娱乐'] = 'nbtv3'
	name_key['宁波-影视剧']   = 'nbtv4'
	name_key['宁波-少儿频道'] = 'nbtv5'

	name_key['宁夏-公共'] = 'nxtv1'
	name_key['宁夏-经济'] = 'nxtv3'
	name_key['宁夏-影视'] = 'nxtv4'
	name_key['宁夏-少儿'] = 'nxtv5'

	name_key['欧洲足球'] = 'europefootball'

	name_key['衢州-公共生活'] = nil
	name_key['衢州-经济信息'] = nil
	name_key['衢州-生活娱乐'] = nil
	name_key['衢州-新闻综合'] = nil
	name_key['全纪实'] = 'sitv11'
	name_key['热播剧场'] = nil
	name_key['三佳购物'] = 'ttcjmall'

	name_key['厦门-新闻'] = 'xmtv1'
	name_key['厦门-纪实'] = 'xmtv2'
	name_key['厦门-生活'] = 'xmtv3'
	name_key['厦门-影视'] = 'xmtv4'

	name_key['陕西-都市青春'] = 'shxitv3'
	name_key['陕西-公共频道'] = 'shxitv2'
	name_key['陕西-生活频道'] = 'shxitv4'
	name_key['陕西-体育休闲'] = 'shxitv8'
	name_key['陕西-新闻资讯'] = nil

	name_key['上海-教育']    = 'shedu1'
	name_key['上海-新闻综合'] = 'shhai1'
	name_key['上海-第一财经'] = 'shhai2'
	name_key['上海-生活时尚'] = 'shhai3'
	name_key['上海-星尚']     = 'shhai3'
	name_key['上海-电视剧']   = 'shhai4'
	name_key['上海-五星体育'] = 'shhai5'
	name_key['上海-纪实频道'] = 'shhai6'
	name_key['上海-新娱乐']   = 'shhai7'
	name_key['上海-艺术人文'] = 'shhai8'
	name_key['上海-外语频道'] = 'shhai9'

	name_key['绍兴-文化影视'] = 'shaoxin1'
	name_key['绍兴-公共频道'] = 'shaoxin2'
	name_key['绍兴-新闻综合'] = 'shaoxin3'

	name_key['深圳-都市']    = 'sztv2'
	name_key['深圳-电视剧']   = 'sztv3'
	name_key['深圳-财经生活'] = 'sztv4'
	name_key['深圳-娱乐']     = 'sztv5'
	name_key['深圳-体育健康'] = 'sztv6'
	name_key['深圳-少儿']     = 'sztv7'
	name_key['深圳-公共']     = 'sztv8'
	name_key['深圳-DV生活']   = 'sztv11'

	name_key['石家庄-新闻综合'] = 'shijiazhuang1'
	name_key['石家庄-娱乐'] = 'shijiazhuang2'
	name_key['石家庄-生活'] = 'shijiazhuang3'
	name_key['石家庄-都市'] = 'shijiazhuang4'

	------------------------------------------------
	name_key['收藏天下'] = 'shoucangtiaxia'
	name_key['四海钓鱼'] = 'bamc4'
	name_key['天元围棋'] = 'tianyuanweiqi'
	name_key['先锋纪录'] = 'documentary-channel'
	name_key['先锋乒羽'] = 'xfby'
	name_key['职业指南'] = 'bamc16'
	name_key['TVB8'] = 'TVB8'
	------------------------------------------------

	name_key['四川-经济频道'] = 'sctv3'
	name_key['四川-文化旅游'] = 'sctv2'
	name_key['四川-新闻资讯'] = 'sctv4'
	name_key['四川-影视文艺'] = 'sctv5'
	name_key['四川-妇女儿童'] = 'sctv7'
	name_key['四川-公共频道'] = 'sctv9'

	name_key['苏州-新闻综合'] = 'suzhoutv1'
	name_key['苏州-社会经济'] = 'suzhoutv2'
	name_key['苏州-文化生活'] = 'suzhoutv3'
	name_key['苏州-电影娱乐'] = 'suzhoutv4'
	name_key['苏州-生活资讯'] = 'suzhoutv5'

	name_key['遂宁-公共公益'] = nil
	name_key['遂宁-互动影视 '] = nil
	name_key['遂宁-新闻综合'] = nil
	name_key['遂宁-直播频道'] = nil

	name_key['泰州-新闻综合'] = 'tztv1'

	name_key['唐山-新闻'] = 'tssv1'
	name_key['唐山-生活'] = 'tssv2'
	name_key['唐山-影视'] = 'tssv3'
	name_key['唐山-公共'] = 'tssv4'

	name_key['TGA游戏频道'] = nil
	name_key['VST电影台'] = nil
	name_key['VST纪录片'] = nil

	name_key['通化-公共频道'] = nil
	name_key['通化-科教频道'] = nil
	name_key['通化-新闻频道'] = nil

	name_key['威海-新闻综合'] = 'weihai1'
	name_key['威海-公共频道'] = 'weihai2'

	name_key['芜湖-新闻综合'] = 'wuhutv1'
	name_key['芜湖-生活频道'] = 'wuhutv2'
	name_key['芜湖-徽商频道'] = 'wuhutv3'

	name_key['无锡-新闻综合'] = 'wuxi1'
	name_key['无锡-娱乐频道'] = 'wuxi2'
	name_key['无锡-经济频道'] = 'wuxi4'
	name_key['无锡-生活频道'] = 'wuxi5'
	name_key['无锡-都市综合'] = nil

	name_key['武汉-新闻频道'] = 'whtv1'
	name_key['武汉-文艺频道'] = 'whtv2'
	name_key['武汉-科教生活'] = 'whtv3'
	name_key['武汉-影视频道'] = 'whtv4'
	name_key['武汉-体育频道'] = 'whtv5'
	name_key['武汉-外语频道'] = 'whtv6'
	name_key['武汉-少儿频道'] = 'whtv7'

	name_key['西安-新闻综合'] = 'xian1'
	name_key['西安-白鸽都市'] = 'xian2'
	name_key['西安-商务资讯'] = 'xian3'
	name_key['西安-文化影视'] = 'xian4'
	name_key['西安-健康快乐'] = 'xian5'
	name_key['西安-音乐综艺'] = 'xian6'

	name_key['西藏藏语'] = 'xizangtv1'

	name_key['西宁-生活频道'] = 'xining-life'
	name_key['西宁-新闻频道'] = 'xining-news'
	name_key['西宁-夏都房车'] = nil
	name_key['西宁-文化先锋'] = nil

	name_key['新疆-哈萨克语新闻综合'] = 'xjtv3'
	name_key['新疆-少儿'] = 'xjtv12'
	name_key['新疆-维语新闻综合'] = 'xjtv2'
	name_key['新疆-维语综艺'] = 'xjtv5'

	name_key['新影视'] = nil
	name_key['新娱乐'] = nil

	name_key['徐州-新闻综合'] = 'xztv1'
	name_key['徐州-经济生活'] = 'xztv2'
	name_key['徐州-文艺影视'] = 'xztv3'
	name_key['徐州-公共频道'] = 'xztv4'

	name_key['雪梨TV'] = nil
	name_key['雅安-新闻综合'] = nil
	name_key['雅安-雨城电视台'] = nil

	name_key['盐城一台'] = 'yanchengtv1'
	name_key['盐城二台'] = 'yanchengtv2'
	name_key['盐城三台'] = 'yanchengtv3'
	name_key['盐城四台'] = 'yanchengxk' -- TODO

	name_key['壹电视新闻台'] = 'nexttv-news'

	name_key['宜宾-新闻综合'] = 'scybtv1'
	name_key['宜宾-公共生活'] = 'scybtv2'

	name_key['义乌-新闻综合'] = 'zjyiwu1'
	name_key['义乌-商贸频道'] = 'zjyiwu2'
	name_key['义乌-电视剧'] = 'zjyiwu3'
	name_key['义乌-公共文艺'] = nil

	name_key['银川-文体'] = 'yinchuang1'
	name_key['银川-生活'] = 'yinchuang2'
	name_key['银川-公共'] = 'yinchuang3'

	name_key['英语辅导'] = 'english-teaching'
	name_key['优优宝贝'] = 'bamc3'
	name_key['游戏风云hd'] = 'sitv2'
	name_key['游戏竞技'] = 'gtv-youxi'

	name_key['云南-都市频道'] = nil
	name_key['云南-少儿频道'] = 'yntv8'

	name_key['孕育指南'] = 'cctvpayfee32'

	name_key['枣庄-公共频道'] = 'zaozhuang2'
	name_key['枣庄-新闻综合'] = 'zaozhuang3'
	name_key['枣庄-生活教育'] = nil

	name_key['张家港-生活'] = nil
	name_key['张家港-新闻'] = nil

	name_key['浙江-钱江频道']   = 'zjtv2'
	name_key['浙江-经视']      = 'zjtv3'
	name_key['浙江-青少科教']   = 'zjtv4'
	name_key['浙江-教育科教']   = 'zjtv4'
	name_key['浙江-影视娱乐']   = 'zjtv5'
	name_key['浙江-6频道']      = 'zjtv6'
	name_key['浙江-公共新农村'] = 'zjtv7'
	name_key['浙江-少儿频道']   = 'zjtv8'
	name_key['浙江-国际频道']   = 'zjtv9'
	name_key['浙江-新农村']     = nil
	name_key['浙江-购物']      = nil
	name_key['浙江-民生休闲']   = nil

	name_key['郑州-妇女儿童'] = 'zhengzhoutv5'
	name_key['郑州-商都频道'] = 'zhengzhoutv2'
	name_key['郑州-时政频道'] = 'zhengzhoutv1'

	name_key['中国教育一'] = 'cetv1'
	name_key['中国教育二'] = 'cetv2'
	name_key['中国教育三'] = 'cetv3'

	name_key['重庆-汽摩'] = nil
	name_key['重庆-手持电视'] = nil
	name_key['重庆-移动'] = nil
	name_key['重庆-新财经'] = 'cqtvxcj'
	name_key['重庆-影视'] = 'ccqtv2'
	name_key['重庆-新闻'] = 'ccqtv3'
	name_key['重庆-科教'] = 'ccqtv4'
	name_key['重庆-都市'] = 'ccqtv5'
	name_key['重庆-娱乐'] = 'ccqtv6'
	name_key['重庆-生活'] = 'ccqtv7'
	name_key['重庆-时尚'] = 'ccqtv8'
	name_key['重庆-公共农村'] = 'ccqtv9'
	name_key['重庆-少儿'] = 'ccqtv10'

	name_key['舟山-公共频道'] = nil
	name_key['舟山-就业服务'] = nil
	name_key['舟山-群岛旅游'] = nil
	name_key['舟山-生活频道'] = nil
	name_key['舟山-新闻综合'] = nil

	name_key['珠海-生活服务'] = 'zhtv2'
	name_key['珠海-新闻综合'] = 'zhtv1'

	name_key["太原-新闻频道"] = "sxtytv1"
	name_key["太原-百姓频道"] = "sxtytv2"
	name_key["太原-法制频道"] = "sxtytv3"
	name_key["太原-影视频道"] = "sxtytv4"
	name_key["太原-文体频道"] = "sxtytv5"

	name_key['青岛-新闻综合'] = 'SDQD1'
	name_key['青岛-生活服务'] = 'SDQD2'
	name_key['青岛-影视频道'] = 'SDQD3'
	name_key['青岛-财经资讯'] = 'SDQD4'
	name_key['青岛-都市频道'] = 'SDQD5'
	name_key['青岛-青少旅游'] = 'SDQD6'
	name_key['青岛-党建频道'] = 'SDQD7'
	name_key['青岛-休闲频道'] = nil

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

function get_channel(albumName)
	--print(albumName)
	local channel_function = {
			get_channel_tvmao,
			--get_channel_pptv,
			--get_channel_letv,
			--get_channel_qqtv,
			--get_channel_btv
	}

	for _, cfunc in ipairs(channel_function) do
		ret = cfunc(albumName)
		if ret then
			return ret
		end
	end

	return '{}'
end
