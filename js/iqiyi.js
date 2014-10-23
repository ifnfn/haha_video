var page = require('webpage').create(),
    system = require('system'),
    tvid, vid;

if (system.args.length === 1) {
	tvid = "755750";
	vid = "c746af54906c40ae93faf1949c3cff75";
}
else {
	tvid = system.args[1];
	vid  = system.args[2];
}

//page.open('/Users/silicon/Documents/workspace/kolatvengine/js/video.html', function (status) {
page.open('js/video.html', function (status) {
	if (status !== 'success') {
		console.log('Unable to access network');
	} else {
		var ua = page.evaluate(function(tvid, vid) {
			var playPageInfo={};
			playPageInfo.tvId = tvid;
			playPageInfo.vid  = vid;

			return iqiyi(playPageInfo);

		}, tvid, vid);
		console.log(ua);
	}
	phantom.exit();
});
