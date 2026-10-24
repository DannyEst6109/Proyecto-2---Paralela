CC = gcc
MPICC = mpicc
CFLAGS = -std=c11 -O2 -Wall -Wextra -Wpedantic
# -std=c11 oculta getopt y clock_gettime; _POSIX_C_SOURCE los vuelve a exponer.
CPPFLAGS = -Iinclude -D_POSIX_C_SOURCE=200809L
LDLIBS = -lcrypto

# En macOS (Homebrew) OpenSSL no esta en la ruta por defecto.
OPENSSL_PREFIX := $(shell brew --prefix openssl@3 2>/dev/null)
ifneq ($(OPENSSL_PREFIX),)
CPPFLAGS += -I$(OPENSSL_PREFIX)/include
LDFLAGS += -L$(OPENSSL_PREFIX)/lib
endif

SEQ = build/aes_archivo build/busqueda_secuencial
MPI = build/busqueda_base build/busqueda_alternativa
HEADERS = include/aes_comun.h include/busqueda.h include/busqueda_mpi.h

.PHONY: all clean
all: $(SEQ) $(MPI)

build/aes_archivo: src/aes_archivo.c include/aes_comun.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $< -o $@ $(LDFLAGS) $(LDLIBS)

build/busqueda_secuencial: src/busqueda_secuencial.c $(HEADERS) | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $< -o $@ $(LDFLAGS) $(LDLIBS)

build/busqueda_base build/busqueda_alternativa: build/%: src/%.c $(HEADERS) | build
	$(MPICC) $(CPPFLAGS) $(CFLAGS) $< -o $@ $(LDFLAGS) $(LDLIBS)

build:
	mkdir -p build

clean:
	rm -f $(SEQ) $(MPI) build/test_aes
	-rmdir build
