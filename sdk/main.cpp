#include <iostream>
#include <unistd.h>

#include "http.hpp"
#include "kola.hpp"
#include "resource.hpp"

void test_http()
{
	int count = 0;
	MultiHttp task;
	const string f1("http://baike.baidu.com/view/1745213.htm");
	const string f2("http://www.cnblogs.com/ider/archive/2011/08/01/cpp_cast_operator_part5.html");
	const char *s1 = "http://git.nationalchip.com/csky-linux-3.0.8_modify_20121219_guoren.tgz";
	const char *s2 = "http://git.nationalchip.com/csky-linux-3.0.8_modify_20121219_guoren.tgz";
	while (1) {
		Http http1(s1);
		Http http2(s2);
		task.Add(&http1);
		task.Add(&http2);
		sleep(3);
		task.Remove(&http2);
		task.Remove(&http1);
		printf("%d", count++);
	}
}

void test_resource(void)
{
	const string f1("http://baike.baidu.com/view/1745213.htm");
	const string f2("http://www.cnblogs.com/ider/archive/2011/08/01/cpp_cast_operator_part5.html");
	KolaClient &kola = KolaClient::Instance();


	ResourceManager *manage = kola.resManager;
	manage->AddResource(f1);
	manage->AddResource(f2);

	FileResource pic;

	manage->GetFile(pic, f1);
	std::cout << pic.GetName() << std::endl;

	manage->GetFile(pic, f1);
	std::cout << pic.GetName() << std::endl;

	manage->GetFile(pic, f2);
	std::cout << pic.GetName() << std::endl;

	manage->GetFile(pic, f2);
	std::cout << pic.GetName() << std::endl;

	manage->GetFile(pic, f2);
	std::cout << pic.GetName() << std::endl;

	manage->GetFile(pic, f1);
	std::cout << pic.GetName() << std::endl;

	manage->GetFile(pic, f1);
	std::cout << pic.GetName() << std::endl;
}

#if TEST
#include "script.hpp"
void test_script()
{
	LuaScript &lua = LuaScript::Instance();
	const char *argv[] = { "http://live.letv.com/lunbo" };

	string ret = lua.RunScript(1, argv, "letv");
}

#endif

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
		break;
	}

	int pos = menu->SeekByAlbumId("4419eb4d34");
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

void test_livetv()
{
	KolaMenu* m = NULL;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
#if 1
	for(int i=0, count=(int)kola.MenuCount(); i < count; i++) {
		m = kola[i];
		cout << "Menu: " << m->name << endl;
	}
#endif

	//m = kola["直播"];
	m = kola.GetMenuByCid(200);
	//	m = kola[200];
	if (m == NULL)
		return;
	//	m->FilterAdd("类型", "CCTV");

	//	m->SetPageSize(3);
	//	m->GetPage(page);
	//	m->FilterAdd("PinYin", "zjw");
	m->SetSort("Name", "1");
	size_t count = m->GetAlbumCount();
#if 1
	for (size_t i=0; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album == NULL)
			continue;
		size_t video_count = album->GetVideoCount();
		printf("[%ld] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
#if 1
		for (size_t j = 0; j < video_count; j++) {
			string player_url;
			KolaVideo *video = album->GetVideo(j);
			if (video) {
				player_url = video->GetVideoUrl();
				printf("\t%s %s [%s] -> %s\n", video->vid.c_str(), video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
#if 0
				KolaEpg epg;

				string info = video->GetInfo();
				epg.LoadFromText(info);

				EPG e1, e2;
				if (epg.GetCurrent(e1)) {
					printf("\t\tCurrent:[%s] %s", e1.timeString.c_str(), e1.title.c_str());
					if (epg.GetNext(e2))
						printf(", Next: [%s] %s", e2.timeString.c_str(), e2.title.c_str());
					printf("\n\n");
				}
#endif
			}
		}
#endif
	}

	return;
#endif

	printf("%s End!!!\n", __func__);
}

void test_video(const char *menuName)
{
	KolaMenu* m = NULL;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
	m = kola[menuName];

	if (m == NULL)
		return;

	foreach(m->quickFilters, s) {
		cout << *s << endl;
	}
	//m->FilterAdd("类型", "爱情片");
	//m->FilterAdd("产地", "香港,台湾");
	m->SetQuickFilter("推荐电影");

	//m->SetSort("周播放最多");
	//m->SetSort("评分最高");

	printf("%ld album in menu!\n", m->GetAlbumCount());
	m->SetPageSize(40);
	size_t count = m->GetAlbumCount();
#if 0
	while (true) {
		int c=0;
		m->SetQuickFilter("最新电影");
		while (1) {
			AlbumPage &page = m->GetPage();
			printf("[%d]: Video:Count %ld\n", page.pageId, page.Count());
			size_t x = page.Count();

			if (page.Count() == 0)
				break;
			for (int i=0; i < x; i++) {
				KolaAlbum *album = page.GetAlbum(i);
				if (album)
					printf("[%d][%d] %s\n", c, i, album->albumName.c_str());
			}
			c++;
			//            m->CleanPage();
		}
		m->SetQuickFilter("热门电影");
		count = m->GetAlbumCount();
		for (int i=0; i < count; i++) {
			KolaAlbum *album = m->GetAlbum(i);
			if (album)
				printf("[%d] %s\n", i, album->albumName.c_str());
			if (i == 100)
				break;
		}
	}
#endif
	AlbumPage &page = m->GetPage();
#if 1
	for (int i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);
		size_t video_count = album->GetVideoCount();
		printf("[%d]: Video:Count %ld\n", i, video_count);

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
	}
#endif
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
#if 1
	count = page.PictureCount();
	printf("Picture count %ld\n", count);
	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);
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

int main(int argc, char **argv)
{
	//test_http();
	//return 0;

	//    test_resource();
	//	return 0;
	KolaClient &kola = KolaClient::Instance();

	KolaInfo& info = kola.GetInfo();
	cout << info.Resolution.ToString() << endl;
	cout << info.VideoSource.ToString() << endl;

	//while (true)
	{
		cout << kola.GetArea() << endl;
		cout << kola.GetTime() << endl;

		KolaArea area;
		if (kola.GetArea(area)) {
			printf("IP: %s\n", area.ip.c_str());
			printf("ISP: %s\n", area.isp.c_str());
			printf("AREA: %s -> %s -> %s\n",
					area.country.c_str(),
					area.province.c_str(),
					area.city.c_str());
		}
	}

	//test_script();
	//return 0;
//	test_custommenu();
//	return 0;
//	printf("Test LiveTV\n"); test_livetv();
//	return 0;

//	printf("Test Video\n"); test_video("电影");
	printf("Test TV\n");    test_video("电视剧");
	while (true) {
		sleep(1);
	}

	//printf("end\n");
	//test_task(); return 0;
}
