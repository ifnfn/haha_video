#include <iostream>
#include <unistd.h>

#include "kola.hpp"

int main(int argc, char **argv)
{
	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
	KolaMenu m;

#if 0
	for(int i=0, count=kola.MenuCount(); i < count; i++) {
		m = kola[i];
		std::cout << "Menu: " << m.name << std::endl;
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
#if 0
	foreach(m.Filter.filterKey, i) {
		std::cout << i->first << ": ";
		foreach(i->second, j)
			std::cout << "\t" << *j << std::endl;
	}
#endif

#if 0
	std::cout << "Sort List: " << std::endl;
	for(int i=0, count=m.Sort.size(); i < count; i++) {
		std::cout << "\t" << m.Sort[i] << std::endl;
	}
#endif

//	m.Filter.KeyAdd("类型", "爱情片");
	m.Sort.Set("周播放最多");
//	m.Sort.Set("评分最高");
	AlbumPage page;
	m.GetPage(page, 0);
//	page.CachePicture(PIC_LARGE);
	page.UpdateVideos();

	for (size_t i = 0; i < page.Count(); i++) {
		std::string player_url;
		KolaAlbum &album = page.GetAlbum(i);

		printf("[%s] %s (%d)\n", album.playlistid.c_str(), album.albumName.c_str(), album.weeklyPlayNum);

		foreach(album.videos, i) {
			KolaVideo *video = *i;
			printf("\tVideo: %s < %s >, playUrl=%s\n", video->name.c_str(),
					video->publishTime.c_str(),
					video->playUrl.c_str());
			player_url = video->GetVideoUrl();
			std::cout << player_url << std::endl;
#if 0
			for (int j=0, count=video->size(); j < count; j++) {
				video->GetVideoUrl(player_url, j);
				std::cout << player_url << std::endl;
			}
#endif
		}
	}

	while (1)
		sleep(3);

	return 0;
}
