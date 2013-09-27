#ifndef __JSON_H__
#define __JSON_H__

#include <stdbool.h>
#include <jansson.h>

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
	json_object_set_new(js, key, json_integer(value));
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
	json_object_set_new(js, key, json_real(value));
}

inline const char *json_gets(json_t *js, const char *key, const char *def)
{
	json_t *p = json_object_get(js, key);
	if (p && json_is_string(p))
		return json_string_value(p);
	else
		return def;
}

inline void json_sets(json_t *js, const char *key, const char *value)
{
	json_object_del(js, key);
	json_object_set_new(js, key, json_string_nocheck(value));
}

inline json_t *json_geto(json_t *js, const char *key)
{
	return json_object_get(js, key);
}

inline void json_seto(json_t *js, const char *key, json_t *value)
{
	json_object_del(js, key);
	json_object_set_new(js, key, value);
}

#define json_array_foreach(object, value) \
	for (int count = json_array_size(object), i = 0; \
			i < count && (value = json_array_get(object, i)) != NULL; i++) \

#endif

