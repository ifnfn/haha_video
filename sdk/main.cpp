#include <iostream>
#include <unistd.h>

#include "kola.hpp"


void filter_test(void)
{
	KolaFilter filter;

	filter.KeyAdd("aa", "a1");
	filter.GetJsonStr();
	filter.KeyAdd("aa", "a2");
	filter.GetJsonStr();
	filter.KeyAdd("aa", "a3");
	filter.GetJsonStr();
	filter.KeyAdd("aa", "a4");
	filter.GetJsonStr();
	filter.KeyAdd("bb", "b1");
	filter.GetJsonStr();
	filter.KeyAdd("bb", "b2");
	filter.GetJsonStr();
	filter.KeyAdd("bb", "b3");
	filter.GetJsonStr();
	filter.KeyAdd("bb", "b4");
	filter.GetJsonStr();
	filter.KeyRemove("bb", "b3");
	filter["bb"] >> "b2";

	filter["aa"].Add("aaaaaa");
	filter["aa"] << "1231231231";
	ValueArray keys = filter["aa"];
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
#if 1
	filter_test();

//	return 0;
	int count = 30;
	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
#if 1
	printf("\\\\\\\\\\\\\\\\\\\\\\\\\\\\\n");
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
	m.GetPage(0);
	for (std::vector<KolaAlbum>::iterator it = m.begin(); it != m.end(); it++) {
		std::string play_url;
		std::cout << it->albumName << std::endl;
		it->GetVideo();
		if (it->video.GetPlayerUrl(0, play_url))
			std::cout << play_url << std::endl;
	}
#endif

#endif
	return 0;
}
