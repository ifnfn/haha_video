#include "kola.hpp"
#include "http.hpp"
#include "json.hpp"
#include "script.hpp"

bool KolaUserResources::VersionCompr(const string newVersion, const string oldVersion)
{
	return Version != oldVersion;
}

bool KolaUserResources::CheckVersion(const string ProjectName, string oldVersion)
{
	string text;
	string url = "files/" + ProjectName + "/info.json";

	json_t *js = json_loadurl(url.c_str());

	Version = json_gets(js, "version", "");
	ChangeLog = json_gets(js, "chanagelog", "");

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

bool KolaUserResources::GetSegment(const string name, UpdateSegment &sgm)
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

bool KolaUserResources::Download(const string name, const string filename)
{
	class UpdateHttp: public Http {
	public:
		UpdateHttp(KolaUserResources *u) {
			 update = u;
		}
		virtual void Progress(curl_off_t dltotal, curl_off_t dlnow, curl_off_t ultotal, curl_off_t ulnow) {
			update->Progress(dltotal, dlnow);
		}
	private:
		KolaUserResources *update;
	};

	UpdateSegment sgm;

	if (GetSegment(name, sgm) ) {
		UpdateHttp http(this);

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
