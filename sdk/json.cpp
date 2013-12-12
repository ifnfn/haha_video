#include "json.hpp"
#include "kola.hpp"

json_t* json_loadurl(const char *url)
{
	json_error_t error;
	std::string text;
	KolaClient& kola = KolaClient::Instance();
	if (kola.UrlGet(url, text) == true) {
		json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

		return js;
	}

	return NULL;
}

const char *json_gets(json_t *js, const char *key, const char *def)
{
	json_t *p = json_object_get(js, key);
	if (p == NULL)
		return def;

	if (json_is_string(p))
		return json_string_value(p);
	else if (json_is_object(p)) {
		json_t *sc = json_object_get(p, "script");
		if (sc) {
			return ScriptCommand(sc).Run().c_str();
		}
	}

	return def;
}


