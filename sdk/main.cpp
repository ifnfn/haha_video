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

int main(int argc, char **argv)
{
	test_custommenu();

	return 0;
#if 0
	while(1)
		test_task();
	return 0;
#endif
#if 1
	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
	KolaMenu* m = NULL;

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

	//m = kola["直播"];
	m = kola["电影"];

	if (m == NULL)
		return -1;

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
		AlbumPage page;
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

	AlbumPage page;
	m->GetPage(page, 0);
#if 1
	for (size_t i = 0; i < page.Count(); i++) {
		std::string player_url;
		KolaAlbum *album = page.GetAlbum(i);
		album->WaitVideo();
		printf("[%d]: Video:Count %d\n", i, album->videos.size());
		foreach(album->videos, j) {
			KolaVideo *video = *j;
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
		}
	}
#endif

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

	printf("End!!!\n");
#endif

	while (1)
		sleep(3);

	return 0;
#endif
}
