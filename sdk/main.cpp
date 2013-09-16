#include <iostream>
#include <unistd.h>

#include "kola.hpp"


void filter_test(void)
{
	KolaFilter filter;

	filter.KeyAdd("aa", "a1");
	filter.KeyAdd("aa", "a2");
	filter.KeyAdd("aa", "a3");
	filter.KeyAdd("aa", "a4");
	filter.KeyAdd("bb", "b1");
	filter.KeyAdd("bb", "b2");
	filter.KeyAdd("bb", "b3");
	filter.KeyAdd("bb", "b4");
	filter.GetJsonStr();
	filter.KeyRemove("bb", "b3");

	filter["aa"].Add("aaaaaa");
	ValueArray keys = filter["aa"];
	foreach(keys, i)
		printf("%s\n", i->c_str());

	filter.GetJsonStr();
	filter["aa"].clear();
	filter["bb"].clear();
	printf("\\\\\\\\\\\\\\\\\\\\\\\\\\\\\n");
	filter.GetJsonStr();
}

int main(int argc, char **argv)
{
	int count = 30;
	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();

	printf("\\\\\\\\\\\\\\\\\\\\\\\\\\\\\n");
	KolaMenu *m;
	for(int i = 0; i < kola.MenuCount(); i++) {
		m = kola[i];
		if (m) {
			printf("ddd:");
			std::cout << m->name << std::endl;
		}
	}

	m = kola.GetMenuByCid(1);
	if (m)
		std::cout << "ByCid: " << m->name << std::endl;
	else
		printf("No Found by cid 1\n");
	m = kola[1];
	if (m)
		std::cout << "kola[1] = " << m->name << std::endl;
	m = kola["电影"];
	if (m)
		std::cout << "kola[\"电影\"] = " << m->name << std::endl;
	m = kola.GetMenuByName("电影");
	if (m) {
		std::cout << "GetMenuByName(\"电影\"):" << m->name << std::endl;
		m->GetPage(10);
#if 0
		std::cout << m->size() << std::endl;

		for (int i = 0 ; i < m->size(); i++)
			std::cout << m->at(i).albumName << std::endl;
#endif

		for (std::vector<KolaAlbum>::iterator it = m->begin(); it != m->end(); it++) {
			std::cout << it->albumName << std::endl;
			it->GetVideo();
			it->video.GetPlayerUrl(0);
		}
	}

	return 0;
}
