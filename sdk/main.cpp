#include <iostream>
#include <unistd.h>

#include "kola.hpp"

#if TEST
#include "script.hpp"
void test_script()
{
	LuaScript &lua = LuaScript::Instance();
	const char *argv[] = { "http://live.letv.com/lunbo" };

	string ret = lua.RunScript(1, argv, "letv");
}

void test_task()
{
	int c = 100;
	vector<Task*> tasks;
	for (int i=0; i < c; i ++)
		tasks.push_back(new Task());
	for (int i=0; i < c; i ++)
		tasks[i]->Start();
	for (int i=0; i <c ; i++) {
		delete tasks[i];
	}
//	tasks.clear();
	printf("end\n");
}
#endif

void test_custommenu()
{
	int count;
	CustomMenu *menu = new CustomMenu("abc");

	while(1) {
#if 1
		menu->AlbumAdd("0c7ac1f004");
		menu->AlbumAdd("11eec465ba");
		menu->AlbumAdd("04a2547275");
		menu->AlbumAdd("4e13fc0109");
		menu->SaveToFile();
		count = menu->GetAlbumCount();
		printf("count=%d\n", count);

		for (int i=0; i < count; i++) {
			KolaAlbum *album = menu->GetAlbum(i);
			if (album == NULL)
				continue;
			size_t video_count = album->GetVideoCount();
			printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
		}
		menu->AlbumAdd("a132d1189a");
		menu->AlbumAdd("1687598f46");
		menu->AlbumAdd("bc4ba8859c");
		menu->AlbumAdd("7152c6122a");
		menu->AlbumAdd("c9467b05a9");
		menu->SaveToFile();
		count = menu->GetAlbumCount();
		printf("count=%d\n", count);

		for (int i=0; i < count; i++) {
			KolaAlbum *album = menu->GetAlbum(i);
			if (album == NULL)
				continue;
			size_t video_count = album->GetVideoCount();
			printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
		}
		menu->AlbumAdd("1ff0e4591c");
		menu->AlbumAdd("9248ce715b");
		menu->AlbumAdd("ada612c186");
		menu->SaveToFile();
		count = menu->GetAlbumCount();
		printf("count=%d\n", count);

		for (int i=0; i < count; i++) {
			KolaAlbum *album = menu->GetAlbum(i);
			if (album == NULL)
				continue;
			size_t video_count = album->GetVideoCount();
			printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
		}
		menu->AlbumAdd("a3eec31e8a");
		menu->AlbumAdd("c85bfd1868");
		menu->SaveToFile();
		count = menu->GetAlbumCount();
		printf("count=%d\n", count);

		for (int i=0; i < count; i++) {
			KolaAlbum *album = menu->GetAlbum(i);
			if (album == NULL)
				continue;
			size_t video_count = album->GetVideoCount();
			printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
		}
		menu->AlbumAdd("95896fb628");
		menu->AlbumAdd("c0cb215ceb");
		menu->AlbumAdd("a7104e13d9");

		menu->SaveToFile();
		count = menu->GetAlbumCount();
		printf("count=%d\n", count);

		for (int i=0; i < count; i++) {
			KolaAlbum *album = menu->GetAlbum(i);
			if (album == NULL)
				continue;
			size_t video_count = album->GetVideoCount();
			printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
		}
#endif
		count = menu->GetAlbumCount();
		printf("count=%d\n", count);

		for (int i=0; i < count; i++) {
			KolaAlbum *album = menu->GetAlbum(i);
			if (album == NULL)
				continue;
			size_t video_count = album->GetVideoCount();
			printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
		}
	}

	delete menu;

	printf("%s End!!!\n", __func__);
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
		cout << "Menu: " << m->name << endl;
	}
#endif

	//m = kola["直播"];
	m = kola.GetMenuByCid(200);
//	m = kola[200];
	if (m == NULL)
		return;
//	m->Filter.KeyAdd("类型", "CCTV");

//	m->SetPageSize(3);
//	m->GetPage(page);
//	m->Filter.KeyAdd("PinYin", "zjw");
	m->Sort.Set("Name", "1");
	int count = m->GetAlbumCount();
	int pos = 0;
#if 1
	for (int i=0; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album == NULL)
			continue;
		int video_count = album->GetVideoCount();
		printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
#if 1
		for (size_t j = 0; j < video_count; j++) {
			string player_url;
			KolaVideo *video = album->GetVideo(j);
			if (video) {
				player_url = video->GetVideoUrl();
				printf("\t%s %s [%s] -> %s\n", video->vid.c_str(), video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
#if 0
				KolaEpg epg;

				string info = video->GetInfo();
				epg.LoadFromText(info);

				EPG e1, e2;
				if (epg.GetCurrent(e1)) {
					printf("\t\tCurrent:[%s] %s", e1.timeString.c_str(), e1.title.c_str());
					if (epg.GetNext(e2))
						printf(", Next: [%s] %s", e2.timeString.c_str(), e2.title.c_str());
					printf("\n\n");
				}
#endif
			}
		}
#endif
	}

	return;
#endif

#if 0
	//pos = m->SeekByAlbumId("156ceef6b9");
	//pos = m->SeekByAlbumId("fff64edb5a");
	//pos = m->SeekByAlbumId("9dfbf95f82");
	//pos = m->SeekByAlbumId("3f200a7529");
	//pos = m->SeekByAlbumId("4302400107");
	pos = m->SeekByAlbumId("764c5069aa");

	KolaAlbum *album = m->GetAlbum(99);
	printf("album->name = %s\n", album->albumName.c_str());
#endif

	map<int, string> vids;
	for (int i=0; i < 9; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album == NULL)
			continue;
		vids[i] = album->vid;
		size_t video_count = 1; //album->GetVideoCount();
		printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
	}
	for (int i=8; i >= 0; i--) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album == NULL)
			continue;
		vids[i] = album->vid;
		size_t video_count = 1; //album->GetVideoCount();
		printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
	}

#if 1
	for (int i=0; i < count; i++) {
		KolaAlbum *album = m->GetAlbum(i);
		if (album == NULL)
			continue;
		vids[i] = album->vid;
		size_t video_count = album->GetVideoCount();
		printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
	}
#endif

	while(1) {
		pos = random() % count;
		KolaAlbum *album = m->GetAlbum(pos);

		if (album == NULL)
			printf("pos[%d] == NULL\n", pos);
		else if (album->vid != vids[pos])
			printf("[%d] [%s : %s] %s\n", pos, album->vid.c_str(), vids[pos].c_str(), album->albumName.c_str());
#if 0
		for (int i=0; i < pos; i++) {
			KolaAlbum *album = m->GetAlbum(i);
			if (album == NULL)
				continue;
			size_t video_count = album->GetVideoCount();
			printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
		}
		printf("\n");
		for (int i=pos; i < count; i++) {
			KolaAlbum *album = m->GetAlbum(i);
			if (album == NULL)
				continue;
			size_t video_count = album->GetVideoCount();
			printf("[%d] [%s] %s: Video Count %ld\n", i, album->vid.c_str(), album->albumName.c_str(), video_count);
		}
#endif
	}

#if 0
		for (size_t j = 0; j < video_count; j++) {
			string player_url;
			KolaVideo *video = album->GetVideo(j);
			if (video) {
				player_url = video->GetVideoUrl();
				printf("\t%s %s [%s] -> %s\n", video->vid.c_str(), video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
				KolaEpg epg;

				string info = video->GetInfo();
				epg.LoadFromText(info);

				EPG e1, e2;
				if (epg.GetCurrent(e1)) {
					printf("\t\tCurrent:[%s] %s", e1.timeString.c_str(), e1.title.c_str());
					if (epg.GetNext(e2))
						printf(", Next: [%s] %s", e2.timeString.c_str(), e2.title.c_str());
					printf("\n\n");
				}
			}
		}
	}
#endif
#if 0
	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);

		size_t video_count = album->GetVideoCount();
		printf("[%ldd] %s: Video:Count %ld\n", i, album->albumName.c_str(), video_count);

		for (size_t j = 0; j < video_count; j++) {
			string player_url;
			KolaVideo *video = album->GetVideo(j);
			if (video) {
				player_url = video->GetVideoUrl();
				printf("\t%s %s [%s] -> %s\n", video->vid.c_str(), video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
				KolaEpg epg;

				string info = video->GetInfo();
				epg.LoadFromText(info);

				EPG e1, e2;
				if (epg.GetCurrent(e1)) {
					printf("\t\tCurrent:[%s] %s", e1.timeString.c_str(), e1.title.c_str());
					if (epg.GetNext(e2))
						printf(", Next: [%s] %s", e2.timeString.c_str(), e2.title.c_str());
					printf("\n\n");
				}
			}
		}
	}
#endif

	printf("%s End!!!\n", __func__);
}

void test_video(const char *menuName)
{
	AlbumPage page;
	KolaMenu* m = NULL;

	KolaClient &kola = KolaClient::Instance();

	kola.UpdateMenu();
	m = kola[menuName];

	if (m == NULL)
		return;

	foreach(m->quickFilters, s) {
		cout << *s << endl;
	}
	//m->Filter.KeyAdd("类型", "爱情片");
	//m->Filter.KeyAdd("产地", "香港,台湾");
	m->SetQuickFilter("推荐电影");

	//m->Sort.Set("周播放最多");
	//m->Sort.Set("评分最高");

	printf("%d album in menu!\n", m->GetAlbumCount());
	m->SetPageSize(4);

	m->GetPage(page, 0);
	page.CachePicture(PIC_LARGE);
	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);
		size_t video_count = album->GetVideoCount();
		printf("[%ld]: Video:Count %ld\n", i, video_count);

		for (size_t j = 0; j < video_count; j++) {
			string player_url;
			KolaVideo *video = album->GetVideo(j);
			if (video) {
				StringList res;
				player_url = video->GetVideoUrl();
				printf("\t%s %s %s [%s] -> %s\n",
						video->pid.c_str(), video->vid.c_str(),
						video->name.c_str(), video->publishTime.c_str(), player_url.c_str());
				video->GetResolution(res);
				printf("Resolution: %s\n", res.ToString().c_str());
			}
			else
				printf("video ============== NULL\n");
		}
	}

	size_t count = page.PictureCount();
	printf("Picture count %ld\n", count);
#if 0
	for (size_t i = 0; i < page.Count(); i++) {
		KolaAlbum *album = page.GetAlbum(i);

		Picture *LargePic = page.GetPicture(album->GetPictureUrl(PIC_LARGE));
		if (LargePic) {
			LargePic->Wait();
			if (LargePic->GetStatus() == Task::StatusFinish && LargePic->used == false) {
				if (LargePic->inCache) {
					printf("[%d] %s: data:%p, size=%d\n", i,
							LargePic->fileName.c_str(),
							LargePic->data, LargePic->size);
					printf("count = %d\n", count);
				}
				LargePic->used = true;
				count--;
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
				if (LargePic->GetStatus() == Task::StatusFinish && LargePic->used == false) {
					if (LargePic->inCache) {
						printf("[%d] %s: data:%p, size=%d\n", i,
							LargePic->fileName.c_str(),
							LargePic->data, LargePic->size);
						printf("count = %d\n", count);
					}
					LargePic->used = true;
					count--;
				}
			}
		}
	}
#endif

	printf("%s End!!!\n", __func__);
}

int main(int argc, char **argv)
{
	KolaClient &kola = KolaClient::Instance();

#if 0
	while(1) {
		printf("%d\n", kola.GetTime());

		sleep(1);
	}
#endif

	cout << kola.GetArea() << endl;
	cout << kola.GetTime() << endl;

//	test_script();
//	return 0;
//	test_custommenu();
//	return 0;
//	printf("Test LiveTV\n"); test_livetv();
//	return 0;

	printf("Test Video\n"); test_video("电影");

	printf("Test TV\n");    test_video("电视剧");
//
//	printf("end\n");
//	test_task(); return 0;
}
