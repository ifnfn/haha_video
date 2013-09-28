/**
 * 视频搜索searchvideo
 * xiewulong
 * 2013/1/12
 */
(function(){

	$(function(){
		setWdjXwlInputs();
		setWdjXwlSearch();
		setWdjXwlSearchBtn();
		setWdjXwlVlistLi();
		setWdjXwlFocus();
		setWdjXwlShowVlist();
		//$('#scrollbar1').tinyscrollbar();
	});

	//setWdjXwlJson('http://video.wandoujia.com/api/tv/hot?page=1&size=10&jsonp=?','wdj_xwl_json_2',true);
	//setWdjXwlJson('http://video.wandoujia.com/api/tv/new?page=1&size=8&jsonp=?','wdj_xwl_json_3');
	//setWdjXwlJson('http://video.wandoujia.com/api/movie/hot?page=1&size=10&jsonp=?','wdj_xwl_json_1',true);
	//setWdjXwlJson('http://video.wandoujia.com/api/movie/new?page=1&size=8&jsonp=?','wdj_xwl_json_4');


	function setWdjXwlShowVlist(){
		$('#wdj_xwl_show_vlist_tab a').each(function(i){
			$(this).click(function(){
				$('#wdj_xwl_show_vlist_tab a').removeClass('on');
				$(this).addClass('on');
				$('.wdj_xwl_show .vlist').hide().eq(i).show();
			});
		}).removeClass('on').eq(0).addClass('on');
		$('.wdj_xwl_show .vlist').hide().eq(0).show();

		if(!-[1,]&&!window.XMLHttpRequest){
			$('.wdj_xwl_show .vlist a').hover(function(){
				$(this).children('i').show();
			},function(){
				$(this).children('i').hide();
			});
		}
	}

	function setWdjXwlJson(url,jd,tag){
		if($('#'+jd).size()==0)return false;
		$.getJSON(url,function(d){
			var vs=d.items;
			var html='';
			for(var i in vs){
				if(tag){
					if(i==0){
						html+=	'<p class="first fix">'+
									'<a href="show.html?'+vs[i].id+'" class="thumb"><img src="http://video.wandoujia.com/api/img/'+vs[i].id+'" /><i>'+(parseInt(i)+1)+'</i></a>'+
									'<strong class="fix"><em>'+vs[i].score+'</em><a href="show.html?'+vs[i].id+'">'+vs[i].title+'</a></strong>'+
									'<span></span>'+
								'</p>';
					
					}else{
						html+=	'<p>'+
									'<em>'+vs[i].score+'</em>'+
									'<i>'+(parseInt(i)+1)+'</i>'+
									'<strong><a href="show.html?'+vs[i].id+'">'+vs[i].title+'</a></strong>'+
								'</p>';
					}
				}else{
					html+=	'<li';
					if(i%4==3)html+=' class="pr0"';
					html+=	'>'+
								'<p>'+
									'<a href="show.html?'+vs[i].id+'"><img src="http://video.wandoujia.com/api/img/'+vs[i].id+'" /></a>'+
									'<strong><a href="show.html?'+vs[i].id+'">'+vs[i].time+'</a></strong>'+
									'<i></i>'+
								'</p>'+
								'<span><a href="show.html?'+vs[i].id+'">'+vs[i].title+'</a></span>'+
							'</li>';
				}
			}
			$('#'+jd).html(html).children('p').each(function(i){
				if(i==0&&tag)setWdjXwlJsonVinfo(vs[i].id,this);
			});
			return false;
		});
	}

	function setWdjXwlJsonVinfo(vid,jd){
		$.getJSON('http://video.wandoujia.com/api/detail/'+vid+'?jsonp=?',function(d){
			$(jd).children('span').eq(0).text(d['info']);
		});
	}

	function setWdjXwlFocus(){
		if($('#wdj_xwl_focus').size()==0)return false;
		var focus=$('#wdj_xwl_focus');
		var imgs=focus.children('ul').eq(0).children('li');
		var scroll=focus.children('.wdj_xwl_focus_scroll').eq(0);
		var scroller_wrap=scroll.children('.wdj_xwl_focus_scroller_wrap').eq(0);
		var scroller=scroller_wrap.children('.wdj_xwl_focus_scroller').eq(0);
		var p=scroller.children('p').eq(0);
		var p2=false;
		var btns=p.children('span');
		if(imgs.size()!=btns.size())return false;
		if(imgs.size()>5){
			var p2=p.clone();
			p2.appendTo(scroller);
		}
		if(p2)btns2=p2.children('span');
		scroll.append('<div class="wdj_xwl_focus_scroll_prev"><a href="javascript:;"></a></div><div class="wdj_xwl_focus_scroll_next"><a href="javascript:;"></a></div>');
		//focus.append('<div class="wdj_xwl_focus_desc"><a href="javascript:;"></a><i class="movie"></i></div><div class="wdj_xwl_focus_desc_bg"></div>');
		var btn_prev=scroll.children('.wdj_xwl_focus_scroll_prev');
		var btn_next=scroll.children('.wdj_xwl_focus_scroll_next');
		//var btn_link=focus.children('.wdj_xwl_focus_desc').eq(0).children('a').eq(0);
		var l=imgs.size();
		var w_swrap=scroller_wrap.width();
		var w_p=p.width();
		var w_btns=btns.width()+14;
		var index=0;
		var speed=3000;
		var t=null;
		var left_this=0;
		scroller.width(w_p*2);
		_go(index);

		focus.hover(function(){clearTimeout(t);},function(){t=setTimeout(function(){_go()},speed);});
		btns.hover(function(){_go($(this).index());});
		if(p2)btns2.hover(function(){_go($(this).index());});
		btn_prev.click(function(){_scroll(-1);});
		btn_next.click(function(){_scroll();});
		
		function _go(n){
			if(n===undefined)clearTimeout(t);
			var j=n===undefined?(index+1>=l?0:index+1):n;
			if(n===undefined)imgs.stop().fadeOut().eq(j).stop().fadeIn();
			else imgs.hide().eq(j).show();
			//btn_link.attr('href',imgs.eq(j).children('a').eq(0).attr('href'));
			if(left_this>-(j*w_btns-w_swrap+w_btns))_scroll();
			btns.removeClass('on');
			btns.eq(j).addClass('on');
			if(p2){
				btns2.removeClass('on');
				btns2.eq(j).addClass('on');
			}
			index=j;
			if(n===undefined)t=setTimeout(function(){_go()},speed);
		}

		function _scroll(n){
			var l_scroller=n==-1?left_this+w_btns:left_this-w_btns;
			if(l_scroller>0){
				scroller.css({left:-w_p});
				l_scroller=-w_p+w_btns;
			}
			if(l_scroller<-w_p){
				scroller.css({left:0});
				l_scroller=-w_btns;
			}
			scroller.stop().animate({left:l_scroller});
			left_this=l_scroller;
		}
		
	}

	function setWdjXwlVlistLi(){
		$('.wdj_xwl_vlist li').each(function(i){
			if(i%4==3)$(this).addClass('pr0');
		});
	}

	function setWdjXwlSearchBtn(){
		$('#wdj_xwl_search_ipt').keydown(function(e){
			var e=e||event;
			e.keyCode=='13'&&_search();
		});
		$('#wdj_xwl_search_btn').click(function(){_search();});
		function _search(){
			var input=$('#wdj_xwl_search_ipt');
			if(input.val()==''||input.val()==input.get(0).defaultValue){
				input.focus();
				return false;
			}
			$('#searchform').submit();
			/*
			location.href=url;
			var url='http://topic1.kugou.com/2012/embedweb/app/search.php?p=bean&sword='+input.val();
			var html='<iframe id="wdj_xwl_searchpage" scrolling="no" frameborder="0" width="100%" height="100%" src="'+url+'"></iframe><div class="wdj_xwl_wrap_iframe_notop"></div>';
			$('#wdj_xwl_wrap_index').remove();
			$('#wdj_xwl_wrap_iframe').html(html).height(_height());
			$('#wdj_xwl_searchpage').load(function(){$('#wdj_xwl_wrap_iframe').show();});
			$(window).resize(function(){$('#wdj_xwl_wrap_iframe').height(_height());});
			function _height(){
				var h=$(window).height()-36;
				h=h<0?0:h;
				return h;
			}
			*/
		}	
	}

	function setWdjXwlSearch(){
		if(!-[1,]&&!window.XMLHttpRequest){
			_width();
			$(window).resize(function(){_width();});
			function _width(){
				//document.title=$(window).width()+','+$('#wdj_xwl_search').width();
				if($(window).width()<800)$('#wdj_xwl_search').width(400);
				else if($(window).width()>1200)$('#wdj_xwl_search').width(600);
				else $('#wdj_xwl_search').width('50%');
			}
		}
	}

	function setWdjXwlInputs(){
		$('.wdj_xwl_inputs').each(function(){
			$(this).focus(function(){
				if($(this).val()==this.defaultValue)$(this).val('').addClass('on');
			}).blur(function(){
				if($(this).val()=='')$(this).removeClass('on').val(this.defaultValue);
			});
		});
	}

})();
