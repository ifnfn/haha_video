#ifndef __JSON_H__
#define __JSON_H__

#include <vector>
#include <string>
#include <stdbool.h>
#include <jansson.h>

class KolaJson {
	public:
		KolaJson() {
			js = NULL;
		}
		KolaJson(const KolaJson &v) {
			js = json_incref(v.js);
		}

		KolaJson(json_t *_js) {
			js = json_incref(_js);
		}

		~KolaJson() {
			json_decref(js);
		}
		bool LoadFromString(std::string v) {
			json_error_t error;
			js = json_loads(v.c_str(), JSON_REJECT_DUPLICATES, &error);

			return js != NULL;
		}

		bool Exists(const char *key) {
			return json_object_get(js, key) != NULL;
		}

		void Set(const char *key, json_int_t value) {
			SetNew(key, json_integer(value));
		}

		void Set(const char *key, const char *value){
			SetNew(key, json_string(value));
		}

		void Set(const char *key, KolaJson *value){
			SetNew(key, value->js);
		}

		void Set(const char *key, float value){
			SetNew(key, json_real(value));
		}

		int Get(const char *key, int def) {
			if (js) {
				json_t *p = json_object_get(js, key);
				if (p && json_is_integer(p))
					return json_integer_value(p);
			}
			return def;
		}

		double Get(const char *key, double def) {
			if (js) {
				json_t *p = json_object_get(js, key);
				if (p && json_is_number(p))
					return json_number_value(p);
			}
			return def;
		}

		const char *Get(const char *key, const char *def) {
			if (js) {
				json_t *p = json_object_get(js, key);
				if (p && json_is_string(p))
					return json_string_value(p);
			}
			return def;
		}
		int Count(void) {
			if (json_is_array(js))
				return json_array_size(js);
			else
				return 0;
		}

		KolaJson Get(const char *key);
		KolaJson GetArray(int index);

		std::string ValueString() {
			return json_string_value(js);
		}

		bool IsArray() {
			return js && json_is_array(js);
		}
		std::string Dumps() {
			if (js)
				json_dumps(js, 2);
			else
				return "";
		}
	private:
		json_t *js;
		void SetNew(const char *key, json_t *o) {
			json_object_del(js, key);
			json_object_set_new(js, key, o);
		}
};

#endif
