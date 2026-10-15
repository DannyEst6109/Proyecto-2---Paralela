CC = gcc
CFLAGS = -std=c11 -O2 -Wall -Wextra -Wpedantic
CPPFLAGS = -Iinclude
LDLIBS = -lcrypto
TARGET = build/aes_archivo

.PHONY: all clean
all: $(TARGET)

$(TARGET): src/aes_archivo.c include/aes_comun.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $< -o $@ $(LDLIBS)

build:
	mkdir -p build

clean:
	rm -f $(TARGET)
	-rmdir build
