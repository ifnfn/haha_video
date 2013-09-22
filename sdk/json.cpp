#include "json.hpp"

KolaJson KolaJson::Get(const char *key) {
	if (js) {
		json_t *jxx = json_object_get(js, key);
		return KolaJson(jxx);
	}

	return KolaJson();
}

KolaJson KolaJson::GetArray(int index) {

	if (js) {
		json_t *jx = json_array_get(js, index);
		return KolaJson(jx);
	}

	return KolaJson();
}
