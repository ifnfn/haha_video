	/* 判断URL是否需要解析,并解析处理 */
	function start_proxy_url(tvurl) {
		var links = tvurl;
		if (links.indexOf("pa:") > -1) {
			links = get_pacntvurl(links);
		}
		else if (links.indexOf("cntv.") > -1) {
			links = get_cntvurl_auth(links);
		}
		else if (links.indexOf("pptv:") > -1) {
			links = links.replace('pptv:', '').replaceAll('/', '');
			links = get_pptvurl(links);
		}
		else if (links.indexOf("imgotv:") > -1) {
			links = links.replace('imgotv:', '').replaceAll('/', '');
			links = get_imgourl(links);
		}
		else if (links.indexOf(".letv") > -1) {
			links = get_letvcdnUrl(links + "?k=" + myvst.livekey());
		}
		else if (links.indexOf(".sdtv") > -1) {
			links = get_sdtvUrl(links + "?k=" + myvst.livekey());
		}
		if (links.length < 7) {
			links = "http://v.youku.com/player/getM3U8/vid/XNTY5NDQ2NzM2/type/hd2/video.m3u8";
		}
		myvst.playFinalUri(links);
	}

	/* 山东TV */
	function get_sdtvUrl(_url) {
		var xml = myvst.curl(_url);
		var purl = vst_cut(xml, "<m3u8>", "</m3u8>");
		return purl;
	}
	
	/* 乐视IP纠正 */
	function get_letvcdnUrl(_url) {
		var ipurl = _url.replace('.letv', '');
		var xml = myvst.curl(_url, "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.2; GGwlPlayer/QQ243944493) Gecko/20100115 Firefox/3.6");
		if (xml.indexOf("</nodelist>") > -1) {
			var nodelist = vst_cut(xml, '<nodelist>', '</nodelist>');
			var urllist = nodelist.split("</node>");
			var urlnum = urllist.length - 1;
			for(var i=0; i < urlnum;i++) {
				ipurl = "http://" + vst_cut(urllist[i], "http://", "]");
			}
		}
		if (ipurl.indexOf("banquantishi") > -1) {
			ipurl = "http://url.52itv.cn/live";
		}
		return ipurl;
	}
	
	/* PPTV直播 */
	function get_pptvurl(vid) {
		var kk = "";
		var pphtml = myvst.curl("http://v.pptv.com/show/h1G4Np4EdLIVkics.html", "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53", "http://live.pptv.com/");
		if (pphtml != null && pphtml.indexOf("kk%3D") > -1) {
			kk = vst_cut(pphtml, 'kk%3D', '"');
		}
		if (!isNaN(vid)) {
			return "http://web-play.pptv.com/web-m3u8-" + vid + ".m3u8?type=m3u8.web.pad&playback=0&kk=" + kk + "&o=v.pptv.com";
		}
		var xml = myvst.curl("http://jump.synacast.com/live2/" + vid);
		var ip = vst_cut(xml, '<server_host>', '</server_host>');
		var delay = vst_cut(xml, '<delay_play_time>', '</delay_play_time>');
		var purl = "http://" + ip + "/live/5/30/" + vid + ".m3u8?type=m3u8.web.pad&playback=0&kk=" + kk + "&o=v.pptv.com";
		return purl;
	}
		
	/* 解析芒果直播TV */
	function get_imgourl(vid) {
		var links = "http://interface.hifuntv.com/mgtv/BasicIndex/ApplyPlayVideo?Tag=26&BussId=1000000&VideoType=1&MediaAssetsId=channel&CategoryId=1000&VideoIndex=0&Version=3.0.11.1.2.MG00_Release&VideoId=" + vid;
		var json = myvst.curl(links);
		var purl = vst_cut(json, 'url="', '"');
		return purl;
	}
	
	/* CNTV地址获取 */
	function get_pacntvurl(pid) {
		var hlsurl = "";
		var header = myvst.curl("http://vdn.live.cntv.cn/api2/live.do?client=iosapp&channel=" + pid, "cbox/5.0.0 CFNetwork/609.1.4 Darwin/13.0.0");
		hlsurl = vst_cut(header, '"hls1":"', '"');
		if (hlsurl.length < 15 || hlsurl.indexOf('dianpian.mp4') > -1 || hlsurl.indexOf('.m3u8') < 1 || hlsurl.indexOf('cntv.cloudcdn.net') > -1) {
			hlsurl = vst_cut(header, '"hls2":"', '"');
		}
		if (hlsurl.length < 15 || hlsurl.indexOf('dianpian.mp4') > -1 || hlsurl.indexOf('.m3u8') < 1 || hlsurl.indexOf('cntv.cloudcdn.net') > -1) {
			hlsurl = vst_cut(header, '"hls3":"', '"');
		}
		if (hlsurl.length < 15 || hlsurl.indexOf('dianpian.mp4') > -1 || hlsurl.indexOf('.m3u8') < 1 || hlsurl.indexOf('cntv.cloudcdn.net') > -1) {
			hlsurl = vst_cut(header, '"hls5":"', '"');
		}
		if (hlsurl.length < 15 || hlsurl.indexOf('dianpian.mp4') > -1 || hlsurl.indexOf('.m3u8') < 1 || hlsurl.indexOf('cntv.cloudcdn.net') > -1) {
			hlsurl = 'http://url.52itv.cn/live';
		}
		return hlsurl.replace("m3u8 ?", "m3u8?").replace(":8000:8000", ":8000").trim();
	}
	
	/* CNTV地址自动转换AUTH */
	function get_cntvurl_auth(url) {
		var authkey = '';
		var header = myvst.curl("http://vdn.live.cntv.cn/api2/live.do?channel=pa://cctv_p2p_hdcctv1", "cbox/5.0.0 CFNetwork/609.1.4 Darwin/13.0.0");
		if (header.indexOf('AUTH=') > -1) {
			authkey = '?AUTH=ip' + vst_cut(header, 'AUTH=ip', '"');
		}
		return url + authkey;
	}
	
	/* 取URL文件名 */
	function getFileName(url, n){
		while (url.indexOf("/") > -1) {
			url = url.substring(url.indexOf("/") + 1, url.length);
		}
		if (n > 0) {
			url = url.split("?")[0];
		}
		return url;
	}
	
	/* 截取指定字符串 */
	function vst_cut(str, start, end) {
		if (str.indexOf(start) > -1) {
			var string = str.split(start)[1];
			if (string.indexOf(end) > -1) {
				return string.split(end)[0];
			}
			else {
				return string;
			}
		}
		return str;
	}
	
	String.prototype.trim = function() {
		return this.replace(/<\/?.+?>/g, '').replace(/[\r\n]/g, '').replace(/(^\s*)|(\s*$)/g, ''); 
	}
	
	/* 替换字符串 */
	String.prototype.replaceAll = function(AFindText, ARepText){ 
		var raRegExp = new RegExp(AFindText.replace(/([\(\)\[\]\{\}\^\$\+\-\*\?\.\"\'\|\/\\])/g,"\\$1"), "ig"); 
		return this.replace(raRegExp, ARepText);
	}
	
	/* 取浏览器参数 */
	function request(paras) { 
		var url = location.href;   
		var paraString = url.substring(url.indexOf("?")+1, url.length).split("&");   
		var paraObj = {};
		for (i=0; j=paraString[i]; i++) {
			paraObj[j.substring(0,j.indexOf("=")).toLowerCase()] = j.substring(j.indexOf("=")+1,j.length);   
		}
		var returnValue = paraObj[paras.toLowerCase()];   
		if(typeof(returnValue) == "undefined") {   
			return "";   
		} else {
			return returnValue;   
		}   
	}
	 
	/* 启动解析 */
	start_proxy_url(myvst.getLiveUrl());