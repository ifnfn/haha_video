#include "json.hpp"
#include "kola.hpp"
#include "script.hpp"

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

bool json_get_script(json_t *js, const char *key, ScriptCommand *script)
{
	json_t *p = json_object_get(js, key);

	if (p == NULL || json_is_string(p))
		return false;

	if (json_is_object(p)) {
		json_t *sc = json_object_get(p, "script");
		if (sc) {
			script->LoadFromJson(p);

			return false;
		}
	}

	return false;
}

const bool json_gets(json_t *js, const char *key, std::string &ret)
{
	json_t *p = json_object_get(js, key);
	if (p == NULL)
		return false;

	if (json_is_string(p))
		ret = json_string_value(p);
	else if (json_is_integer(p)) {
		char buf[32];
		sprintf(buf, "%d", json_integer_value(p));

		ret.assign(buf);
	}
	else if (json_is_object(p)) {
		json_t *sc = json_object_get(p, "script");
		if (sc) {
			ret = ScriptCommand(p).Run().c_str();
		}
	}

	return false;
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
			return ScriptCommand(p).Run().c_str();
		}
	}

	return def;
}


bool json_get_stringlist(json_t *js, const char *key, StringList *list)
{
	bool ret = false;

	if (list == NULL)
		return false;

	json_t *sub = json_geto(js, key);
	if (sub && json_is_array(sub)) {
		json_t *v;
		ret = true;
		json_array_foreach(sub, v) {
			if (json_is_string(v)) {
				const char *s = json_string_value(v);
				if (s) {
					list->Add(s);
					count++;
				}
			}
		}
	}

	return ret;
}
