#include "json.hpp"
#include "kola.hpp"

bool json_dump_str(json_t *js, string &ret)
{
	char *text = json_dumps(js, 2);

	if (text) {
		ret = text;
		jsonp_free(text);

		return true;
	}

	return false;
}

json_t* json_loadurl(const char *url)
{
	json_error_t error;
	string text;
	KolaClient& kola = KolaClient::Instance();
	if (kola.UrlGet(url, text) == true) {
		json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

		return js;
	}

	return NULL;
}

bool json_to_variant(json_t *js, ScriptCommand *script)
{
	return script->LoadFromJson(js);
}

bool json_get_variant(json_t *js, const char *key, ScriptCommand *script)
{
	json_t *p = json_object_get(js, key);

	if (p)
		return json_to_variant(p, script);
	else
		return false;
}

const bool json_gets(json_t *js, const char *key, string &ret)
{
	json_t *p = json_object_get(js, key);
	if (p == NULL)
		return false;

	if (json_is_string(p))
		ret = json_string_value(p);
	else if (json_is_integer(p)) {
		char buf[32];
		sprintf(buf, "%lld", json_integer_value(p));

		ret.assign(buf);
	}
	else if (json_is_object(p)) {
		json_t *sc = json_object_get(p, "script");
		if (sc) {
			ScriptCommand cmd(p);
			ret = cmd.Run();
			return true;
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
		while(1)
			printf("dddddddddddddd\n");
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
