CC = gcc
MPICC = mpicc
CFLAGS = -std=c11 -O2 -Wall -Wextra -Wpedantic
LDLIBS = -lcrypto
TARGETS = busqueda_clave_aes_secuencial busqueda_clave_aes_mejorada busqueda_clave_aes_mpi
.PHONY: all clean
all: $(TARGETS)
busqueda_clave_aes_secuencial: busqueda_clave_aes_secuencial.c
	$(CC) $(CFLAGS) $< -o $@ $(LDLIBS)
busqueda_clave_aes_mejorada: busqueda_clave_aes_mejorada.c aes_comun.h
	$(CC) $(CFLAGS) $< -o $@ $(LDLIBS)
busqueda_clave_aes_mpi: busqueda_clave_aes_mpi.c aes_comun.h
	$(MPICC) $(CFLAGS) $< -o $@ $(LDLIBS)
clean:
	rm -f $(TARGETS) test_aes
