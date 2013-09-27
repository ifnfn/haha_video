#ifndef BASE64_H
#define BASE64_H

#include <string>

#define BASE64_SIZE(x)  (((x)+2) / 3 * 4 + 1)

size_t base64decode(const unsigned char *input, size_t input_length, unsigned char *output, size_t output_length);
size_t base64encode(const unsigned char *input, size_t input_length, unsigned char *output, size_t output_length);

std::string base64encode(const std::string input);

#endif

