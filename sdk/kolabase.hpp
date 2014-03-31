//
//  kola_base.hpp
//  kolatv
//
//  Created by Silicon on 14-3-12.
//  Copyright (c) 2014年 Silicon. All rights reserved.
//

#ifndef kolatv_kola_base_hpp
#define kolatv_kola_base_hpp

class KolaVideo: public IVideo {
public:
	virtual void Parser(json_t *js);

	virtual void GetResolution(StringList& res);
	virtual void SetResolution(string &res);
	virtual string GetVideoUrl();
	virtual string GetSubtitle(const char *lang) {return "";}
private:
	string directPlayUrl;
};

class KolaAlbum: public IAlbum {
public:
	KolaAlbum();
	virtual ~KolaAlbum();

	virtual void Parser(json_t *js);

	virtual size_t GetTotalSet();
	virtual size_t GetVideoCount();
	virtual size_t GetSource(StringList &sources); // 获取节目的节目来源列表
	virtual bool SetSource(string source);         // 设置节目来源，为""时，使用默认来源
	virtual bool GetPictureFile(FileResource& picture, enum PicType type);
	virtual IVideo *GetVideo(size_t id);
private:
	void VideosClear();
	bool LowVideoGetPage(size_t pageNo, size_t pageSize);
	virtual string &GetPictureUrl(enum PicType type=PIC_AUTO);

	int cid;
	vector<IVideo*> videoList;

	size_t totalSet;         // 总集数
	size_t updateSet;        // 当前更新集
	string videoPlayUrl;

	string largePicUrl;      // 大图片网址
	string smallPicUrl;      // 小图片网址
	string largeHorPicUrl;
	string smallHorPicUrl;
	string largeVerPicUrl;
	string smallVerPicUrl;

	bool   directVideos;
	size_t videoPageSize;
	size_t videoPageId;
	map<string, Variant> SourceList;
	string CurrentSource;   // 设置节目来源
};



#endif
