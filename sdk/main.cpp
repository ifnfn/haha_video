#include <iostream>
#include <unistd.h>

#include "kola.hpp"

int main(int argc, char **argv)
{
	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
#if 1
	KolaMenu m;

#if 0
	m = kola["电影"];
	m = kola.GetMenuByCid(1);
	m = kola[1];
	m = kola["电影"];
#endif

	m = kola.GetMenuByName("电影");
	std::cout << "GetMenuByName(\"电影\"):" << m.name << std::endl;
#if 0
	foreach(m.Filter.filterKey, i) {
		std::cout << i->first << ": ";
		foreach(i->second, j)
			std::cout << "\t" << *j << std::endl;
	}
#endif

//	m.Filter.KeyAdd("类型", "爱情片");
	m.Sort.Set("周播放最多");
//	m.Sort.Set("评分最高");
	AlbumPage page;
	m.GetPage(page, 0);
	page.CachePicture(PIC_LARGE);
	page.CacheVideo();
//	for (std::vector<KolaAlbum>::iterator it = page.begin(); it != page.end(); it++) {

	foreach(page, it) {
		std::string player_url;
		printf("[%d] %s (%d)\n", it->playlistid, it->albumName.c_str(), it->weeklyPlayNum);
		foreach(it->videos, i) {
			printf("\tVideo: %s < %s >, playUrl=%s\n", i->name.c_str(),
					i->publishTime.c_str(),
					i->playUrl.c_str());

			player_url = i->GetPlayerUrl();
			std::cout << player_url << std::endl;
			// i->GetPlayerUrl(0, player_url);
			// std::cout << player_url << std::endl;
		}
	}

//	Picture pic;
//	if (page.waitPictureTimeout(pic, 300) == true) {

//	}
#endif
	while (1)
		sleep(3);
	while (kola.haveCommand()) {
		sleep(1);
	}

	return 0;
}
