#include <iostream>
#include <unistd.h>

#include "kola.hpp"
#include "json.h"
#include "base64.hpp"
#include "script.hpp"


KolaVideo::KolaVideo(json_t *js)
{
	width = height = fps = totalBytes = totalBlocks = 0;
	totalDuration = 0.0;
	order = 0;
	isHigh = 0;
	videoPlayCount = 0;
	videoScore = 0.0;
	playLength = 0.0;

	if (js)
		LoadFromJson(js);
}

KolaVideo::~KolaVideo()
{
}

bool KolaVideo::LoadFromJson(json_t *js)
{
	json_t *sub;

	name           = json_gets(js   , "name"           , "");
	playlistid     = json_gets(js   , "playlistid"     , "");
	pid            = json_gets(js   , "pid"            , "");
	vid            = json_gets(js   , "vid"            , "");
	cid            = json_geti(js   , "cid"            , 0);
	order          = json_geti(js   , "order"          , 0);
	isHigh         = json_geti(js   , "isHigh"         , 0);

	videoPlayCount = json_geti(js   , "videoPlayCount" , 0);
	videoScore     = json_getreal(js, "videoScore"     , 0.0);
	playLength     = json_getreal(js, "playLength"     , 0.0);

	showName       = json_gets(js   , "showName"       , "");
	publishTime    = json_gets(js   , "publishTime"    , "");
	videoDesc      = json_gets(js   , "videoDesc"      , "");

	smallPicUrl    = json_gets(js   , "smallPicUrl"    , "");
	largePicUrl    = json_gets(js   , "largePicUrl"    , "");
	playUrl        = json_gets(js   , "playUrl"        , "");
	directPlayUrl  = json_gets(js   , "directPlayUrl"  , "");
	totalDuration  = json_getreal(js, "totalDuration"  , 0.0);
	width          = json_geti(js   , "width"          , 0);
	height         = json_geti(js   , "height"         , 0);
	totalBlocks    = json_geti(js   , "totalBlocks"    , 0);
	totalBytes     = json_geti(js   , "totalBytes"     , 0);
	fps            = json_geti(js   , "fps"            , 0);

	sub = json_geto(js, "script");
	if (sub) {
		Script.LoadFromJson(sub);
	}

	return true;
}

std::string KolaVideo::GetVideoUrl(void)
{
	if (Script.Exists())
		return Script.Run();
	else
		return directPlayUrl;
}

