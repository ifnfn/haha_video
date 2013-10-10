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
#endif
	m = kola.GetMenuByName("电影");
	std::cout << "GetMenuByName(\"电影\"):" << m.name << std::endl;

//	m.Filter.KeyAdd("类型", "爱情片");
	m.Sort.Set("周播放最多");
//	m.Sort.Set("评分最高");
	albumPage page;
	m.GetPage(page, 0);
	page.CachePicture(PIC_LARGE);
	for (std::vector<KolaAlbum>::iterator it = page.begin(); it != page.end(); it++) {
		std::string play_url;
		printf("[%d] %s (%d)\n", it->playlistid, it->albumName.c_str(), it->weeklyPlayNum);
	}
#endif

	while (true)
		sleep(3);

	return 0;
}
