.PHONY: all laboratorio test clean

all:
	$(MAKE) -C proyecto02

laboratorio:
	$(MAKE) -C laboratorio03/programas

test: all laboratorio
	$(CC) -std=c11 -O2 -Wall -Wextra -Wpedantic laboratorio03/programas/test_aes.c -o laboratorio03/programas/test_aes -lcrypto
	./laboratorio03/programas/test_aes
	python3 proyecto02/tests/probar_inciso1.py
	python3 proyecto02/tests/probar_busqueda.py

clean:
	$(MAKE) -C proyecto02 clean
	$(MAKE) -C laboratorio03/programas clean
