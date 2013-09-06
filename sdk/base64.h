#ifndef BASE64_H
#define BASE64_H

#define BASE64_SIZE(x)  (((x)+2) / 3 * 4 + 1)
unsigned int base64encode(const unsigned char *input, unsigned int input_length, unsigned char *output, int output_length);
unsigned int base64decode(const unsigned char *input, unsigned int input_length, unsigned char *output, int output_length);

#endif

