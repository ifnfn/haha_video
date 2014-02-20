#ifndef BASE64_HPP
#define BASE64_HPP

#include <string>

using namespace std;
#define BASE64_SIZE(x)  (((x)+2) / 3 * 4 + 1)

size_t base64decode(const unsigned char *input, size_t input_length, unsigned char *output, size_t output_length);
size_t base64encode(const unsigned char *input, size_t input_length, unsigned char *output, size_t output_length);

string base64encode(const string input);

#endif

