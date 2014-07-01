#include <iostream>
#include <unistd.h>

#include "http.hpp"
#include "kola.hpp"
#include "resource.hpp"

void test_custommenu()
{
	size_t count;
	CustomMenu *menu = new CustomMenu("/tmp/abc");
	count = menu->GetAlbumCount();
	printf("count=%ld\n", count);

	while(1) {
		for (int i=0; i < count; i++) {
			KolaAlbum *album = menu->GetAlbum(i);
			if (album == NULL)
				continue;
#if 0
			size_t video_count = album->GetVideoCount();
			printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
			string player_url;
			for (int j = 0; j < video_count; j++) {
				IVideo *video = album->GetVideo(j);
				if (video) {
					player_url = video->GetVideoUrl();
					printf("\t%s %s [%s] -> %s\n", video->vid.c_str(), video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
				}
			}
#endif
		}
		break;
	}

	int pos = menu->SeekByAlbumId("4419eb4d34");
	pos = 0;
	for (int i=pos; i < count; i++) {
		KolaAlbum *album = menu->GetAlbum(i);
		if (album == NULL)
			continue;
		size_t video_count = album->GetVideoCount();
		printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
		string player_url;
		for (int j = 0; j < video_count; j++) {
			KolaVideo *video = album->GetVideo(j);
			if (video) {
				player_url = video->GetVideoUrl();
				printf("\t%s %s [%s] -> %s\n", video->vid.c_str(), video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
			}
		}
	}
	delete menu;

	printf("%s End!!!\n", __func__);
}

class Player: public KolaPlayer {
	virtual bool Play(KolaVideo *video) {
		if (video) {
			string player_url = video->GetVideoUrl();
			printf("\t%s %s [%s] -> %s\n", video->vid.c_str(), \
			       video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
		}

		return true;
	}
};

void test_livetv_noepg()
{
	KolaMenu* m = NULL;
	Player player;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();

	m = kola.GetMenu(200);
	if (m == NULL)
		return;

	//m->FilterAdd("类型", "本省台");
	//m->FilterAdd("类型", "央视台");
	//m->FilterAdd("类型", "卫视台");
	//m->FilterAdd("类型", "地方台");
	//m->FilterAdd("类型", "高清台");
	m->PictureCacheType = PIC_DISABLE;
	size_t count = m->GetAlbumCount();
	int pos = 0;

	for (size_t i=pos; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album == NULL)
			continue;
		size_t video_count = album->GetVideoCount();
		bool found = false;
		while (1) {
			KolaEpg *epg = album->NewEPG();

			if (epg) {
				EPG e1, e2;
				epg->Update();
				epg->Wait();
				epg->GetCurrent(e1);
				epg->GetNext(e2);

				if (not e1.empty() or not e2.empty())
					found = true;


				epg->Clear();
				delete epg;
			}
			break;
		}
		if (not found)
			printf("\tname_key['%s'] = ''\n", album->albumName.c_str());
	}

	printf("%s End!!!\n", __func__);
}

void test_livetv_list()
{
	KolaMenu* m = NULL;
	Player player;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();

	m = kola.GetMenu(200);
	if (m == NULL)
		return;

	//m->FilterAdd("类型", "本省台");
	//m->FilterAdd("类型", "央视台");
	//m->FilterAdd("类型", "卫视台");
	//m->FilterAdd("类型", "地方台");
	//m->FilterAdd("类型", "高清台");
	//m->SetPageSize(3);
	//m->GetPage(page);
	//m->FilterAdd("PinYin", "hz");
	//m->SetSort("Name", "1");
	m->PictureCacheType = PIC_DISABLE;
	size_t count = m->GetAlbumCount();
	int pos = 0;

	for (size_t i=pos; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album == NULL)
			continue;
		size_t video_count = album->GetVideoCount();
		printf("%s\n", album->albumName.c_str());
		//printf("[%ld] %-30s [%s]: Video Count %ld\n", i, album->albumName.c_str(), album->vid.c_str(), video_count);
#if 0
		bool found = false;
		while (1) {
			KolaEpg *epg = album->NewEPG();

			if (epg) {
				EPG e1, e2;
				epg->Update();
				epg->Wait();
				epg->GetCurrent(e1);
				epg->GetNext(e2);

				if (not e1.empty()) {
					//printf("\t\tCurrent:[%s] %s", e1.timeString.c_str(), e1.title.c_str());
					found = true;
				}

				if (not e2.empty()) {
					//printf(", Next: [%s] %s", e2.timeString.c_str(), e2.title.c_str());
					found = true;
				}
				//printf("\n\n");

				epg->Clear();
				delete epg;
			}
			break;
		}
		if (not found)
			printf("\tname_key['%s'] = ''\n", album->albumName.c_str());
#endif
	}

	printf("%s End!!!\n", __func__);
}

void test_livetv_epglist()
{
	KolaMenu* m = NULL;
	Player player;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();

	m = kola.GetMenu(200);
	if (m == NULL)
		return;

	//m->FilterAdd("类型", "本省台");
	//m->FilterAdd("类型", "央视台");
	//m->FilterAdd("类型", "卫视台");
	//m->FilterAdd("类型", "地方台");
	//m->FilterAdd("类型", "高清台");
	//m->SetPageSize(3);
	//m->GetPage(page);
	//m->FilterAdd("PinYin", "hz");
	//m->SetSort("Name", "1");
	m->PictureCacheType = PIC_DISABLE;
	size_t count = m->GetAlbumCount();
	int pos = 0;

	for (size_t i=pos; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album == NULL)
			continue;
		size_t video_count = album->GetVideoCount();
		printf("[%ld] %s [%s]: Video Count %ld\n", i, album->albumName.c_str(), album->vid.c_str(), video_count);
		while (1) {
			KolaEpg *epg = album->NewEPG();

			if (epg) {
				EPG e1, e2;
				epg->Update();
				epg->Wait();
				epg->GetCurrent(e1);
				epg->GetNext(e2);

				if (not e1.empty()) {
					printf("\t\tCurrent:[%s] %s", e1.timeString.c_str(), e1.title.c_str());
				}

				if (not e2.empty()) {
					printf(", Next: [%s] %s", e2.timeString.c_str(), e2.title.c_str());
				}
				else
					printf("dddddddddddddddddddddddd\n");
				printf("\n\n");

				epg->Clear();
				delete epg;
			}
			break;
		}
	}

	printf("%s End!!!\n", __func__);
}

void test_livetv()
{
	KolaMenu* m = NULL;
	Player player;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
#if 0
	for(int i=0, count=(int)kola.MenuCount(); i < count; i++) {
		m = kola.Index(i);
		cout << "Menu: " << m->name << endl;
	}
#endif

	m = kola.GetMenu(200);
	if (m == NULL)
		return;
	foreach(m->Filter.filterKey, i) {
		cout << i->first << ": ";
		foreach(i->second, j)
			cout << "\t:" << *j << endl;
	}
	//m->FilterAdd("类型", "本省台");
	//m->FilterAdd("类型", "央视台");
	//m->FilterAdd("类型", "卫视台");
	//m->FilterAdd("类型", "地方台");
	//m->FilterAdd("类型", "高清台");
	//m->SetPageSize(3);
	//m->GetPage(page);
	//m->FilterAdd("PinYin", "hz");
	//m->SetSort("Name", "1");
	m->PictureCacheType = PIC_DISABLE;
	size_t count = m->GetAlbumCount();
	int pos = 0;
//	pos = m->SeekByAlbumNumber("4");

#if 1
	for (size_t i=pos; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album == NULL)
			continue;
		size_t video_count = album->GetVideoCount();
		printf("[%ld] %s [%s]: Video Count %ld\n", i, album->albumName.c_str(), album->vid.c_str(), video_count);
#if 1
		player.AddAlbum(*album);
		while (1) {
			KolaEpg *epg = player.GetEPG();
			if (epg) {
				EPG e, e1, e2;

				epg->GetCurrent(e1);
				epg->GetNext(e2);
				size_t count = epg->Count();
				for (int i =0;i < count; i++) {
					epg->Get(i, e);
					if (not e.empty()) {
						if (e == e1)
							printf("\t\t * [%s] %s\n", e.timeString.c_str(), e.title.c_str());
						else if (e == e2)
							printf("\t\t **[%s] %s\n", e.timeString.c_str(), e.title.c_str());
						else
							printf("\t\t   [%s] %s\n", e.timeString.c_str(), e.title.c_str());
					}
				}
				printf("\n\n");
				//break;
			}
		}
		sleep(4);
#endif
#if 0
		bool found = false;
		while (1) {
			KolaEpg *epg = album->NewEPG();

			if (epg) {
				EPG e1, e2;
				epg->Update();
				epg->Wait();
				epg->GetCurrent(e1);
				epg->GetNext(e2);

				if (not e1.empty()) {
					printf("\t\tCurrent:[%s] %s", e1.timeString.c_str(), e1.title.c_str());
					found = true;
				}

				if (not e2.empty()) {
					printf(", Next: [%s] %s", e2.timeString.c_str(), e2.title.c_str());
					found = true;
				}
				printf("\n\n");

				epg->Clear();
				delete epg;
			}
			break;
		}
		if (not found)
			printf("\tname_key['%s'] = ''\n", album->albumName.c_str());
#endif
#if 1

		for (size_t j = 0; j < video_count; j++) {
			string player_url;
			KolaVideo *video = album->GetVideo(j);
			if (video) {
				player_url = video->GetVideoUrl();
				printf("\t%s %s [%s] -> %s\n", video->vid.c_str(), video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
			}
		}
#endif
	}
#endif

	printf("%s End!!!\n", __func__);
}

void test_picture(const char *menuName)
{
	KolaMenu* m = NULL;

	//KolaClient &kola = KolaClient::Instance();
	KolaClient &kola = KolaClient::Instance("000002");

	kola.UpdateMenu();
	m = kola.GetMenu(menuName);

	if (m == NULL)
		return;

	m->SetQuickFilter("热门电影");
	//m->SetQuickFilter("推荐电影");
	int nPerPageCount=10;
	//m->PictureCacheType = PIC_DISABLE;
	m->PictureCacheType = PIC_LARGE_VER;
	m->SetPageSize(nPerPageCount);
	size_t count = m->GetAlbumCount();
	printf("%ld album in menu!\n", m->GetAlbumCount());
	int i=0;
	vector<KolaAlbum*> vAlbum;
	KolaAlbum *album=NULL;
	while(1){
		album = m->GetAlbum(i++);
		FileResource picture;
		if(NULL==album)
		{
			printf("album is null\n");
			continue;
		}else{
			if(vAlbum.size()>=nPerPageCount){
				m->PictureCacheType = PIC_LARGE_VER;
				vAlbum.clear();
				continue;
			}else{
				vAlbum.push_back(album);
				if(vAlbum.size()==nPerPageCount)
				{
					int nSleepCount=30;//1s=50*20 
					while(nSleepCount--){
						for(int j=0;j<vAlbum.size();j++)
						{
							if (vAlbum[j]->GetPictureFile(picture, PIC_LARGE_VER) == true) {
								if (picture.isCached()) {
									printf("[%ld] %s: size=%ld\n", i*nPerPageCount-vAlbum.size()+j,
											picture.GetName().c_str(),
											picture.GetSize());
								}
							}
						}
						usleep(50000);
					}
				}else{
					if(i>=count){
						i=0;
						int nTmp=10;
						while(nTmp--)
						printf("#######page is return#######\n");
					}
					continue;
				}
			}
		}
		//system("/dvb/meminfo.sh");
	}
	printf("%s End!!!\n", __func__);
}

void test_picture1(const char *menuName)
{
	KolaMenu* m = NULL;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
	m = kola.GetMenu(menuName);

	if (m == NULL)
		return;

	//m->PictureCacheType = PIC_DISABLE;
	size_t count = m->GetAlbumCount();
	FileResource picture[10000];
	for (int i=0; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album) {
			printf("[%d] %s\n", i, album->albumName.c_str());
#if 1
			FileResource &pic = picture[0];
			if (album->GetPictureFile(pic, PIC_LARGE) == true) {
				pic.Wait();
				if (pic.isCached()) {
					printf("[%d] %s: size=%ld\n", i,
					       pic.GetName().c_str(),
					       pic.GetSize());
				}
			}
#endif
		}
//		if (i > 100)
//			break;
	}
}

void test_sort(const char *menuName)
{
#if 1
	KolaMenu* m = NULL;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
	m = kola.GetMenu(menuName);
	m->SetSort("日播放最多");
	size_t count = m->GetAlbumCount();
	for (int i=0; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album) {
			StringList sources;
			printf("[%d] %s\n", i, album->albumName.c_str());
			cout << sources.ToString() << endl;
		}

		if (i == 20)
			break;
	}

	m->SetSort("总播放最多");
	count = m->GetAlbumCount();
	for (int i=0; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album)
			printf("[%d] %s\n", i, album->albumName.c_str());
		if (i == 20)
			break;
	}
	m->SetSort("评分最高");
	count = m->GetAlbumCount();
	for (int i=0; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album)
			printf("[%d] %s\n", i, album->albumName.c_str());
		if (i == 20)
			break;
	}
	m->SetSort("最新发布");
	count = m->GetAlbumCount();
	for (int i=0; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album)
			printf("[%d] %s\n", i, album->albumName.c_str());
		if (i == 20)
			break;
	}
#endif
}

void test_video(const char *menuName)
{
	KolaMenu* m = NULL;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
	m = kola.GetMenu(menuName);
	//m->PictureCacheType = PIC_DISABLE;

	if (m == NULL)
		return;
	foreach(m->Filter.filterKey, i) {
		cout << i->first << ": ";
		foreach(i->second, j)
		cout << "\t:" << *j << endl;
	}

	foreach(m->quickFilters, s) {
		cout << *s << endl;
	}
	//m->FilterAdd("类型", "爱情片");
	//m->FilterAdd("产地", "香港,台湾");
	//m->FilterAdd("年份", "2013");
	//m->SetQuickFilter("推荐电影");
	//m->SetQuickFilter("日韩电影");

	//m->SetSort("日播放最多");
	//m->SetSort("总播放最多");
	//m->SetSort("评分最高");
	//m->SetSort("最新发布");
	//m->SetSort("名称");
	//m->FilterAdd("PinYin", "dsn");

	printf("%ld album in menu!\n", m->GetAlbumCount());
	m->SetPageSize(40);
#if 1
	Player player;
	size_t count = m->GetAlbumCount();

	for (int i = 0; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		FileResource picture;

		if (album == NULL)
			continue;

		printf("[%d]: albumName: %s[%s]\n",
			i, album->albumName.c_str(), album->vid.c_str());
#if 0
		StringList sources;
		album->GetSource(sources); // 获取节目的节目来源列表
		cout << sources.ToString() << endl;
		album->SetSource("爱奇艺");
#endif

#if 1
		size_t video_count = album->GetVideoCount();
		printf("[%d]: albumName: %s[%s], PlayNum:%d, VideoCount: %ld, TotalCount: %ld\n",
		       i, album->albumName.c_str(), album->vid.c_str(), album->dailyPlayNum, video_count, album->GetTotalSet());
#endif
#if 0
		if (album->GetPictureFile(picture, PIC_LARGE) == true) {
//			picture.Wait();
			if (picture.isCached()) {
				printf("[%d] %s: size=%ld\n", i,
				       picture.GetName().c_str(),
				       picture.GetSize());
				count--;
			}
		}
#endif
#if 1
		for (size_t j = 0; j < video_count; j++) {
			string player_url;
			KolaVideo *video = album->GetVideo(j);
			if (video) {
				StringList res;
				player_url = video->GetVideoUrl();
				printf("\t%s %s %s [%s] -> %s\n",
						video->pid.c_str(), video->vid.c_str(),
						video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
				video->GetResolution(res);
				printf("Resolution: %s\n", res.ToString().c_str());
			}
			else
				printf("video ============== NULL\n");
		}
#endif
	}
#endif

#if 0
	PictureIterator x(&page, PIC_LARGE);

	while (x.size() > 0) {
		FileResource picture;
		int index = x.Get(picture);
		if (index >=0 && picture.isCached()) {
			printf("[%d] %s: size=%ld\n", index,
					picture.GetName().c_str(),
					picture.GetSize());
		}
	}
#endif

#if 0
	size_t count = page.PictureCount();
	printf("Picture count %ld\n", count);
	for (size_t i = 0; i < page.Count(); i++) {
		IAlbum *album = page.GetAlbum(i);
		FileResource picture;

		if (album->GetPictureFile(picture, PIC_LARGE) == true) {
			if (picture.isCached()) {
				printf("[%ld] %s: size=%ld\n", i,
						picture.GetName().c_str(),
						picture.GetSize());
				count--;
			}
		}
	}
#endif

	printf("%s End!!!\n", __func__);
}

void test_info(KolaClient &kola)
{
	KolaInfo info;
	if (kola.GetInfo(info)) {
		cout << info.Resolution.ToString() << endl;
		cout << info.VideoSource.ToString() << endl;
	}

}

void test_area(KolaClient &kola)
{
	cout << kola.GetTime() << endl;

	KolaArea area;
	if (kola.GetArea(area)) {
		printf("IP: %s\n", area.ip.c_str());
		printf("ISP: %s\n", area.isp.c_str());
		printf("AREA: %s -> %s -> %s\n",
		       area.country.c_str(),
		       area.province.c_str(),
		       area.city.c_str());

		printf("json: %s\n", area.toJson().c_str());
	}
}

void test_weather(KolaClient &kola)
{
#if 0
	StringList data;

	kola.weather.GetProvince(data);
	cout << data.ToString() << endl;

	data.clear();
	kola.weather.GetCity("安徽", data);
	cout << data.ToString() << endl;

	data.clear();
	kola.weather.GetCounty("安徽", "安庆", data);
	cout << data.ToString() << endl;
#endif
	while (true) {
		kola.weather.SetArea("广东-清远");
		//kola.weather.Update();
		kola.weather.Update();

		while (not kola.weather.UpdateFinish()) {
			Weather *w = kola.weather.Today();
			if (w) {
				printf("[%s] %s: %s %s %s %s %s,%s, PM2.5: %s\n",
				       w->city.ToString("", "", "-").c_str(),
				       w->date.c_str(),
				       w->day.temp.c_str(),
				       w->day.code.c_str(),
				       w->day.weather.c_str(),
				       w->day.windDirection.c_str(),
				       w->day.windPower.c_str(),
				       w->day.picture.c_str(),
				       kola.weather.PM25.c_str()
				       );
				break;
			}
		}

		//kola.weather.SetArea("");
		//kola.weather.Update();

		while (not kola.weather.UpdateFinish()) {
			Weather *w = kola.weather.Today();
			if (w) {
				printf("[%s] %s: %s %s %s %s %s,%s, PM2.5: %s\n",
				       w->city.ToString("", "", "-").c_str(),
				       w->date.c_str(),
				       w->day.temp.c_str(),
				       w->day.code.c_str(),
				       w->day.weather.c_str(),
				       w->day.windDirection.c_str(),
				       w->day.windPower.c_str(),
				       w->day.picture.c_str(),
				       kola.weather.PM25.c_str()
				       );
				break;
			}
		}
	}
}

void test_update(KolaClient &kola)
{
	KolaUpdate update;

	update.CheckVersion("zhuzhg", "v1111");
	update.Download("ppt2854.rar", "/tmp/ppt2854.rar");
}

int main(int argc, char **argv)
{
	KolaClient &kola = KolaClient::Instance("000002");

	kola.InternetReady();
#if 0
	test_info(kola);
	test_area(kola);
	test_weather(kola);
	test_update(kola);
#endif
//	test_picture1("电影"); return 0;
//	test_custommenu(); return 0;
//	printf("Test LiveTV(No EPG\n"); test_livetv_noepg(); return 0;
//	printf("Test LiveTV(TV List\n"); test_livetv_list(); return 0;
//	printf("Test LiveTV(TV List\n"); test_livetv_epglist(); return 0;
	printf("Test LiveTV(TV List\n"); test_livetv(); return 0;

//	printf("Test Video\n"); test_video("综艺"); return 0;
	//printf("Test Video\n"); test_video("动漫"); return 0;
	printf("Test Video\n"); test_video("电影"); return 0;
//	printf("Test TV\n");    test_video("电视剧"); return 0;

	printf("end\n");
	//test_task();

	return 0;
}
