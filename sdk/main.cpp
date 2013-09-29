#include <iostream>
#include <unistd.h>

#include "kola.hpp"


void filter_test(void)
{
	KolaFilter filter;

	filter.KeyAdd("a1", "a1");
	filter.GetJsonStr();
	filter.KeyAdd("a1", "a2");
	filter.GetJsonStr();
	filter.KeyAdd("a1", "a3");
	filter.GetJsonStr();
	filter.KeyAdd("a1", "a4");
	filter.GetJsonStr();
	filter.KeyAdd("b1", "b1");
	filter.GetJsonStr();
	filter.KeyAdd("b1", "b2");
	filter.GetJsonStr();
	filter.KeyAdd("b1", "b3");
	filter.GetJsonStr();
	filter.KeyAdd("bb", "b4");
	filter.GetJsonStr();
	filter.KeyRemove("bb", "b3");
	filter["bb"] >> "b2";

	filter["aa"].Add("aaaaaa");
	filter["aa"] << "1231231231";
	FilterValue keys = filter["aa"];
	foreach(keys, i)
		printf("aa --> %s\n", i->c_str());

	keys = filter["bb"];
	foreach(keys, i)
		printf("bb --> %s\n", i->c_str());
	filter.GetJsonStr();
	filter["aa"].clear();
	filter["bb"].clear();
	printf("\\\\\\\\\\\\\\\\\\\\\\\\\\\\\n");
	filter.GetJsonStr();

	KolaSort sort;

	sort << "sort1";
	std::cout << sort.GetJsonStr() << std::endl;
	sort << "sort2";
	std::cout << sort.GetJsonStr() << std::endl;
	sort << "sort3";
	std::cout << sort.GetJsonStr() << std::endl;
}

int main(int argc, char **argv)
{
//	filter_test(); return 0;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
#if 1
	KolaMenu m;

#if 0
	m = kola["电影"];
	std::cout << "kola[\"电影\"] = " << m.name << std::endl;
	for(int i = 0; i < kola.MenuCount(); i++) {
		m = kola[i];
		printf("ddd:");
		std::cout << m.name << std::endl;
	}

	m = kola.GetMenuByCid(1);
	std::cout << "ByCid: " << m.name << std::endl;

	m = kola[1];
	std::cout << "kola[1] = " << m.name << std::endl;

	m = kola["电影"];
	std::cout << "kola[\"电影\"] = " << m.name << std::endl;
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
	m.GetPage(0);
	for (std::vector<KolaAlbum>::iterator it = m.begin(); it != m.end(); it++) {
		std::string play_url;
		printf("[%s] %s (%d)\n", it->playlistid.c_str(), it->albumName.c_str(), it->weeklyPlayNum);
		it->CachePicture(KolaAlbum::PIC_LARGE);
//		it->GetVideo();
//		if (it->video.GetPlayerUrl(0, play_url))
//			std::cout << play_url << std::endl;
	}
#endif
	while(1) sleep(3);
	return 0;
}
