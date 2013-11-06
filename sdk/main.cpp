#include <iostream>
#include <unistd.h>

#include "kola.hpp"

void test_task()
{
	int c = 4;
	std::vector<Task*> tasks;
	for (int i=0; i < c; i ++)
		tasks.push_back(new Task());
	for (int i=0; i < c; i ++)
		tasks[i]->Start();
	for (int i=0; i <c ; i++) {
		delete tasks[i];
	}
	tasks.clear();
	printf("end\n");
}

void test_custommenu()
{
	CustomMenu *menu = new CustomMenu("abc");

	menu->AlbumAdd("845690");
	menu->AlbumAdd("582923");
	menu->AlbumAdd("841316");
	menu->AlbumAdd("220791");
	menu->AlbumAdd("221079");

	AlbumPage page;
	menu->GetPage(page);
	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);

		printf("[%d] %s\n", i, album->albumName.c_str());
	}

	menu->SaveToFile();
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

	m = kola["直播"];
	m->Filter.KeyAdd("类型", "CCTV");

	m->GetPage(page);

	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);

		printf("[%d] %s\n", i, album->albumName.c_str());
	}
}

void test_tv()
{
	AlbumPage page;
	KolaMenu* m = NULL;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
	m = kola["电视剧"];

	if (m == NULL)
		return;
	//m->Filter.KeyAdd("类型", "爱情片");
	//m->Filter.KeyAdd("产地", "香港,台湾");
	//m->SetQuickFilter("推荐电影");

//	m->Sort.Set("周播放最多");
//	m->Sort.Set("评分最高");

	printf("%d album in menu!\n", m->GetAlbumCount());
#if 1
	while (1) {
		m->GetPage(page);
		page.CachePicture(PIC_LARGE);

		for (size_t i = 0; i < page.Count(); i++) {
			KolaAlbum *album = page.GetAlbum(i);

			printf("[%d] %s\n", i, album->albumName.c_str());
		}

		break;
		if (page.Count() < 20)
			break;
	}
#endif

	m->GetPage(page, 0);
	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);
		int video_count = album->GetVideoCount();
		printf("[%d]: Video:Count %d\n", i, video_count);

		for (size_t j = 0; j < video_count; j++) {
			std::string player_url;
			KolaVideo *video = album->GetVideo(j);
			player_url = video->GetVideoUrl();
			printf("\t%s -> %s\n", video->name.c_str(), player_url.c_str());
		}
	}
}

void test_video()
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

#if 0
	m = kola["电影"];
	m = kola.GetMenuByCid(1);
	m = kola[1];
	m = kola["电影"];
	m = kola.GetMenuByName("电影");
#endif
	m = kola["电影"];

	if (m == NULL)
		return;
#if 0
	foreach(m->Filter.filterKey, i) {
		std::cout << i->first << ": ";
		foreach(i->second, j)
			std::cout << "\t" << *j << std::endl;
	}
#endif
	foreach(m->quickFilters, i) {
		std::cout << *i << std::endl;
	}

#if 0
	std::cout << "Sort List: " << std::endl;
	for(int i=0, count=m->Sort.size(); i < count; i++) {
		std::cout << "\t" << m->Sort[i] << std::endl;
	}
#endif

	//m->Filter.KeyAdd("类型", "爱情片");
	//m->Filter.KeyAdd("产地", "香港,台湾");
	m->SetQuickFilter("推荐电影");

//	m->Sort.Set("周播放最多");
//	m->Sort.Set("评分最高");

	printf("%d album in menu!\n", m->GetAlbumCount());

//	return 0;

#if 1
	while (1) {
		m->GetPage(page);
		page.CachePicture(PIC_LARGE);

		for (size_t i = 0; i < page.Count(); i++) {
			KolaAlbum *album = page.GetAlbum(i);

			printf("[%d] %s\n", i, album->albumName.c_str());
		}

		break;
		if (page.Count() < 20)
			break;
	}
#endif

	m->GetPage(page, 0);
#if 1
	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);
		int video_count = album->GetVideoCount();
		printf("[%d]: Video:Count %d\n", i, video_count);

		for (size_t j = 0; j < video_count; j++) {
			std::string player_url;
			KolaVideo *video = album->GetVideo(j);
			player_url = video->GetVideoUrl();
			printf("\t%s -> %s\n", video->name.c_str(), player_url.c_str());
		}
	}
#endif

#if 1
	page.CachePicture(PIC_LARGE);
	size_t count = page.PictureCount();

#if 0
	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);

		Picture *LargePic = page.GetPicture(album->GetPictureUrl(PIC_LARGE));
		if (LargePic) {
			LargePic->Wait();
			if (LargePic->GetStatus() == Task::StatusFinish) {
				if (LargePic->inCache && LargePic->used == false) {
					printf("[%d] %s: data:%p, size=%d\n", i,
							LargePic->fileName.c_str(),
							LargePic->data, LargePic->size);
					LargePic->used = true;
					printf("count = %d\n", count);
				}
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
				if (LargePic->GetStatus() == Task::StatusFinish) {
					if (LargePic->inCache && LargePic->used == false) {
						printf("[%d] %s: data:%p, size=%d\n", i,
							LargePic->fileName.c_str(),
							LargePic->data, LargePic->size);
						LargePic->used = true;
						printf("count = %d\n", count);
					}
					count--;
				}
			}
		}
	}
#endif

	printf("End!!!\n");
#endif
}

int main(int argc, char **argv)
{
//	test_custommenu(); return 0;
//	test_livetv(); return 0;
	test_video(); return 0;
//	test_tv(); return 0;
//	test_task(); return 0;
}
