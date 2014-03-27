#include "kola.hpp"
#include "http.hpp"
#include "json.hpp"
#include "script.hpp"

KolaUpdate::KolaUpdate(string name) {
	js = NULL;
	ProjectName = name;
}

KolaUpdate::~KolaUpdate() {
	if (js)
		json_delete(js);
}

bool KolaUpdate::VersionCompr(const string newVersion, const string oldVersion)
{
	return Version != oldVersion;
}

bool KolaUpdate::CheckVersion(string oldVersion)
{
	string text;
	string url = "files/" + ProjectName + "/info.json";

	json_t *js = json_loadurl(url.c_str());

	Version = json_gets(js, "version", "");

	json_t *files = json_geto(js, "files");


	if (files) {
		json_t *v;
		json_array_foreach(files, v) {
			UpdateSegment sgm;
			sgm.name = json_gets(v, "name", "");
			sgm.href = json_gets(v, "href", "");
			sgm.md5  = json_gets(v, "md5", "");
			Segments.push_back(sgm);
		}
	}

	return VersionCompr(Version, oldVersion);
}

bool KolaUpdate::GetSegment(const string name, UpdateSegment &sgm)
{
	vector<UpdateSegment>::iterator it;

	for (it = Segments.begin(); it != Segments.end(); it++) {
		if (it->name == name) {
			sgm = *it;
			return true;
		}
	}

	return false;
}

bool KolaUpdate::Download(const string name, const string filename)
{
	UpdateSegment sgm;

	if (GetSegment(name, sgm) ) {
		Http http;

		if (http.Get(sgm.href.c_str())) {
			HttpBuffer &data = http.Data();

			if (data.GetMD5() == sgm.md5) {
				http.Data().SaveToFile(filename.c_str());

				return true;
			}
		}
	}

	return false;
}
