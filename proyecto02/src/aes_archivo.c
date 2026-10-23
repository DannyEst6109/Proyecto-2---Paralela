/* Proyecto 02, inciso 1. Cifra y descifra archivos de texto con AES-128 (ECB). */
#include "aes_comun.h"

/* Lee bytes sin modificar saltos de linea ni la codificacion del texto. */
static int read_text(const char *path, unsigned char *text, int *length) {
    FILE *file = fopen(path, "rb");
    if (!file) { perror(path); return 0; }
    size_t count = fread(text, 1, MAX_MESSAGE, file);
    int extra = fgetc(file);
    int ok = !ferror(file) && extra == EOF;
    if (fclose(file) != 0) ok = 0;
    if (!ok) {
        fprintf(stderr, "No se pudo leer el archivo o supera %d bytes.\n", MAX_MESSAGE);
        return 0;
    }
    *length = (int)count;
    return 1;
}

/* El modo exclusivo evita reemplazar archivos existentes, incluida la entrada. */
static int write_output(const char *path, const Dataset *data,
        const unsigned char *plain, int encrypting) {
    FILE *file = fopen(path, "wbx");
    if (!file) { perror(path); return 0; }
    if (encrypting) {
        fprintf(file, "AESECB1\n%d\n", data->length);
        print_hex(file, data->cipher, cipher_length(data->length));
    } else {
        if (fwrite(plain, 1, (size_t)data->length, file) != (size_t)data->length) {
            fclose(file);
            remove(path);
            fputs("No se pudo escribir el texto recuperado.\n", stderr);
            return 0;
        }
    }
    int ok = !ferror(file);
    if (fclose(file) != 0) ok = 0;
    if (!ok) {
        remove(path);
        fputs("No se pudo guardar el archivo de salida.\n", stderr);
    }
    return ok;
}

int main(int argc, char **argv) {
    uint64_t number;
    int encrypting = argc == 5 && !strcmp(argv[1], "cifrar");
    int decrypting = argc == 5 && !strcmp(argv[1], "descifrar");
    if ((!encrypting && !decrypting) || !parse_number(argv[4], &number)) {
        fprintf(stderr, "Uso:\n  %s cifrar entrada.txt salida.aes clave\n"
            "  %s descifrar entrada.aes recuperado.txt clave\n"
            "Clave: entero decimal entre 0 y 18446744073709551614.\n"
            "Texto: hasta %d bytes. La salida debe ser un archivo nuevo.\n",
            argv[0], argv[0], MAX_MESSAGE);
        return 1;
    }
    Dataset data = {0};
    unsigned char plain[MAX_MESSAGE + 16] = {0}, key[16];
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) { fputs("No se pudo crear el contexto AES.\n", stderr); return 1; }
    int status = 1;
    if (encrypting) {
        if (!read_text(argv[2], plain, &data.length)) goto done;
        if (!encrypt_message(ctx, number, plain, data.length, &data)) {
            fputs("Error al cifrar el archivo.\n", stderr);
            goto done;
        }
    } else {
        if (!load_dataset(argv[2], &data)) {
            fputs("No se pudo leer el archivo AES o su formato es invalido.\n", stderr);
            goto done;
        }
        int recovered = 0;
        int result = decrypt_message(ctx, number, &data, plain, &recovered);
        if (result != 1) {
            fputs(result == 0 ? "Clave incorrecta o contenido alterado.\n"
                : "Error de la biblioteca al descifrar.\n", stderr);
            goto done;
        }
        data.length = recovered;
    }
    if (!write_output(argv[3], &data, plain, encrypting)) goto done;
    make_key(number, key);
    printf("Operacion: %s\nEntrada: %s\nSalida: %s\nLongitud: %d bytes\n",
        argv[1], argv[2], argv[3], data.length);
    printf("Clave AES-128 (hex): "); print_hex(stdout, key, 16);
    printf("Texto cifrado (hex): "); print_hex(stdout, data.cipher, cipher_length(data.length));
    printf("%s:\n", encrypting ? "Texto original" : "Texto recuperado");
    fwrite(plain, 1, (size_t)data.length, stdout);
    putchar('\n');
    status = 0;
done:
    OPENSSL_cleanse(plain, sizeof plain);
    EVP_CIPHER_CTX_free(ctx);
    return status;
}
