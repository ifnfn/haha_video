#ifndef JSON_HPP
#define JSON_HPP

#include <string>
#include "jansson.h"

using namespace std;

class ScriptCommand;
class StringList;

json_t* json_loadurl(const char *url);

bool json_dump_str(json_t *js, string &ret);
bool json_to_variant(json_t *js, ScriptCommand *script);
bool json_get_variant(json_t *js, const char *key, ScriptCommand *script);
bool json_get_stringlist(json_t *js, const char *key, StringList *list);

inline bool json_key_exists(json_t *js, const char *key)
{
	return  json_object_get(js, key) != NULL;
}

inline json_int_t json_geti(json_t *js, const char *key, json_int_t def)
{
	json_t *p = json_object_get(js, key);
	if (p && json_is_integer(p))
		return json_integer_value(p);
	else
		return def;
}

inline void json_seti(json_t *js, const char *key, json_int_t value)
{
	json_object_del(js, key);
	json_object_set(js, key, json_integer(value));
}

inline double json_getreal(json_t *js, const char *key, double def)
{
	json_t *p = json_object_get(js, key);
	if (p && json_is_number(p))
		return json_number_value(p);
	else
		return def;
}

inline void json_setreal(json_t *js, const char *key, double value)
{
	json_object_del(js, key);
	json_object_set(js, key, json_real(value));
}

const char *json_gets(json_t *js, const char *key, const char *def);
const bool json_gets(json_t *js, const char *key, string &ret);

inline void json_sets(json_t *js, const char *key, const char *value)
{
	json_object_del(js, key);
	json_object_set(js, key, json_string_nocheck(value));
}

inline json_t *json_geto(json_t *js, const char *key)
{
	return json_object_get(js, key);
}

inline void json_seto(json_t *js, const char *key, json_t *value)
{
	json_object_del(js, key);
	json_object_set(js, key, value);
}

#ifdef json_array_foreach
#undef json_array_foreach
#endif
#define json_array_foreach(object, value) \
	for (size_t count = json_array_size(object), i = 0; \
			i < count && (value = json_array_get(object, i)) != NULL; i++) \

#endif

