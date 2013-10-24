#include <iostream>
#include <unistd.h>

#include "kola.hpp"

int main(int argc, char **argv)
{
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

	m = kola["直播"];
	//m = kola["电影"];

	if (m == NULL)
		return -1;

#if 1
	foreach(m->Filter.filterKey, i) {
		std::cout << i->first << ": ";
		foreach(i->second, j)
			std::cout << "\t" << *j << std::endl;
	}
#endif

#if 1
	std::cout << "Sort List: " << std::endl;
	for(int i=0, count=m->Sort.size(); i < count; i++) {
		std::cout << "\t" << m->Sort[i] << std::endl;
	}
#endif

//	m->Filter.KeyAdd("类型", "爱情片");
//	m->Sort.Set("周播放最多");
//	m->Sort.Set("评分最高");
	AlbumPage page;
	m->GetPage(page, 0);
	page.CachePicture(PIC_LARGE);
	//page.CachePicture(PIC_SMALL);

	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);

		printf("[%d] %s\n", i, album->albumName.c_str());
	}

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
	size_t count = page.PictureCount();
	while (count) {
		for (size_t i = 0; i < page.Count(); i++) {
			KolaAlbum *album = page.GetAlbum(i);

			Picture *LargePic = page.GetPicture(album->GetPictureUrl(PIC_LARGE));
			if (LargePic) {
				if (LargePic->inCache && LargePic->used == false) {
					printf("[%d] %s: data:%p, size=%d\n", i, LargePic->fileName.c_str(), LargePic->data, LargePic->size);
					LargePic->used = true;
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
}
