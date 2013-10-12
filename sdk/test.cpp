#include <iostream>
#include <unistd.h>

#include "kola.hpp"

int main(int argc, char **argv)
{
	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
	KolaMenu m;

#if 0
	m = kola["电影"];
	m = kola.GetMenuByCid(1);
	m = kola[1];
	m = kola["电影"];
#endif

	m = kola.GetMenuByName("电影");
	std::cout << "GetMenuByName(\"电影\"):" << m.name << std::endl;

//	m.Filter.KeyAdd("类型", "爱情片");
	m.Sort.Set("周播放最多");
//	m.Sort.Set("评分最高");
	AlbumPage page;
	m.GetPage(page, 0);
	page.CachePicture(PIC_LARGE);
	page.CacheVideo();

//	for (std::vector<KolaAlbum>::iterator it = page.begin(); it != page.end(); it++) {
	foreach(page, it) {
		std::string play_url;
		printf("[%d] %s (%d)\n", it->playlistid, it->albumName.c_str(), it->weeklyPlayNum);
		it->GetVideos();
		foreach(it->videos, i) {
			printf("\tVideo: %s < %s >\n", i->name.c_str(), i->publishTime.c_str());

			player_url = i->GetM3U8();
		}
	}

	while (true)
		sleep(3);

	return 0;
}
