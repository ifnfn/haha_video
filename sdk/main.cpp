#include <iostream>
#include <unistd.h>

#include "script.hpp"
#include "kola.hpp"

void test_script()
{
	LuaScript &lua = LuaScript::Instance();
	const char *argv[] = { "http://live.letv.com/lunbo" };

	std::string ret = lua.RunScript(1, argv, "letv");
}

void test_task()
{
	int c = 100;
	std::vector<Task*> tasks;
	for (int i=0; i < c; i ++)
		tasks.push_back(new Task());
	for (int i=0; i < c; i ++)
		tasks[i]->Start();
	for (int i=0; i <c ; i++) {
		delete tasks[i];
	}
//	tasks.clear();
	printf("end\n");
}

void test_custommenu()
{
	CustomMenu *menu = new CustomMenu("abc");

	menu->SetPageSize(4);
	menu->AlbumAdd("845690");
	menu->AlbumAdd("582923");
	menu->AlbumAdd("841316");
	menu->AlbumAdd("220791");
	menu->AlbumAdd("221079");

	AlbumPage page;
	while(1) {
		menu->GetPage(page);
		for (size_t i = 0; i < page.Count(); i++) {
			KolaAlbum *album = page.GetAlbum(i);
			size_t video_count = album->GetVideoCount();
			printf("[%ld] %s: Video:Count %ld\n", i, album->albumName.c_str(), video_count);

			for (size_t j = 0; j < video_count; j++) {
				std::string player_url;
				KolaVideo *video = album->GetVideo(j);
				if (video) {
					player_url = video->GetVideoUrl();
					printf("\t%s [%s] -> %s\n", video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
				}
			}
		}

		if (page.Count() != menu->GetPageSize())
			break;
	}

	menu->SaveToFile();
	delete menu;

	printf("%s End!!!\n", __func__);
}

void test_livetv()
{
	AlbumPage page;
	KolaMenu* m = NULL;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
#if 1
	for(int i=0, count=kola.MenuCount(); i < count; i++) {
		m = kola[i];
		std::cout << "Menu: " << m->name << std::endl;
	}
#endif

	//m = kola["直播"];
	m = kola.GetMenuByCid(200);
//	m = kola[200];
	if (m == NULL)
		return;
//	m->Filter.KeyAdd("类型", "CCTV");

	m->SetPageSize(100);
	m->GetPage(page);

	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);

		size_t video_count = album->GetVideoCount();
		printf("[%ldd] %s: Video:Count %ld\n", i, album->albumName.c_str(), video_count);

		for (size_t j = 0; j < video_count; j++) {
			std::string player_url;
			KolaVideo *video = album->GetVideo(j);
			if (video) {
				player_url = video->GetVideoUrl();
				printf("\t%s %s [%s] -> %s\n", video->vid.c_str(), video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
				KolaEpg epg;

				std::string info = video->GetInfo();
				epg.LoadFromText(info);

				EPG e1, e2;
				if (epg.GetCurrent(e1)) {
					printf("\t\tCurrent:[%s] %s", e1.timeString.c_str(), e1.title.c_str());
					if (epg.GetNext(e2))
						printf(", Next: [%s] %s", e2.timeString.c_str(), e2.title.c_str());
					printf("\n\n");
				}
			}
		}
	}

	printf("%s End!!!\n", __func__);
}

void test_video(const char *menuName)
{
	AlbumPage page;
	KolaMenu* m = NULL;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
	m = kola[menuName];

	if (m == NULL)
		return;


	foreach(m->quickFilters, s) {
		std::cout << *s << std::endl;
	}
	//m->Filter.KeyAdd("类型", "爱情片");
	//m->Filter.KeyAdd("产地", "香港,台湾");
	//m->SetQuickFilter("推荐电影");

	//m->Sort.Set("周播放最多");
	//m->Sort.Set("评分最高");

	printf("%d album in menu!\n", m->GetAlbumCount());
	m->SetPageSize(4);
#if 0
	do {
		m->GetPage(page);

		for (size_t i = 0; i < page.Count(); i++) {
			KolaAlbum *album = page.GetAlbum(i);

			printf("[%ld] %s\n", i, album->albumName.c_str());
		}

		if (page.Count() < m->GetPageSize())
			break;
	} while(0);
#endif

	m->GetPage(page, 0);
	page.CachePicture(PIC_LARGE);
	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);
		size_t video_count = album->GetVideoCount();
		printf("[%ld]: Video:Count %ld\n", i, video_count);

		for (size_t j = 0; j < video_count; j++) {
			std::string player_url;
			KolaVideo *video = album->GetVideo(j);
			if (video) {
				player_url = video->GetVideoUrl();
				printf("\t%s %s %s [%s] -> %s\n",
						video->pid.c_str(), video->vid.c_str(),
						video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
			}
		}
	}

	size_t count = page.PictureCount();
	printf("Picture count %ld\n", count);
#if 0
	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);

		Picture *LargePic = page.GetPicture(album->GetPictureUrl(PIC_LARGE));
		if (LargePic) {
			LargePic->Wait();
			if (LargePic->GetStatus() == Task::StatusFinish && LargePic->used == false) {
				if (LargePic->inCache) {
					printf("[%d] %s: data:%p, size=%d\n", i,
							LargePic->fileName.c_str(),
							LargePic->data, LargePic->size);
					printf("count = %d\n", count);
				}
				LargePic->used = true;
				count--;
			}
		}
	}
#endif

#if 0
	while (count) {
		for (size_t i = 0; i < page.Count(); i++) {
			KolaAlbum *album = page.GetAlbum(i);

			Picture *LargePic = page.GetPicture(album->GetPictureUrl(PIC_LARGE));
			if (LargePic) {
				if (LargePic->GetStatus() == Task::StatusFinish && LargePic->used == false) {
					if (LargePic->inCache) {
						printf("[%d] %s: data:%p, size=%d\n", i,
							LargePic->fileName.c_str(),
							LargePic->data, LargePic->size);
						printf("count = %d\n", count);
					}
					LargePic->used = true;
					count--;
				}
			}
		}
	}
#endif

	printf("%s End!!!\n", __func__);
}

int main(int argc, char **argv)
{
	KolaClient &kola = KolaClient::Instance();

#if 0
	while(1) {
		printf("%d\n", kola.GetTime());

		sleep(1);
	}
#endif

	std::cout << kola.GetArea() << std::endl;
	std::cout << kola.GetTime() << std::endl;

//	test_script();
//	return 0;
//	test_custommenu();
//	return 0;
	printf("Test LiveTV\n"); test_livetv();

	printf("Test Video\n"); test_video("电影");

	printf("Test TV\n");    test_video("电视剧");
//
//	printf("end\n");
//	test_task(); return 0;
}
