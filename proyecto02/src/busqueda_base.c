/* Proyecto 02, incisos 2 y 3. Estrategia base: reparto estatico por lotes.
 * Se recorren las claves [offset, offset+limite). En la ronda r el proceso p
 * prueba [offset+(r*n+p)*B, offset+(r*n+p+1)*B), con n procesos y lote B.
 * Al terminar cada ronda todos los procesos comparten el resultado con MPI_Allreduce.
 */
#include "busqueda_mpi.h"

#define USO "Uso: mpirun -np N busqueda_base [-f frase] [-o offset] [-l limite] [-b lote] [-t segundos] archivo.aes\n" \
    "  Prueba las claves offset..offset+limite-1 (offset 0 y limite 4294967296 por defecto) en lotes de 65536 claves.\n" \
    "  Use -o para medir claves altas, p. ej. -o 18014398509481984 (2^56/4)."

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank); MPI_Comm_size(MPI_COMM_WORLD, &size);
    Params p; Dataset d = {0};
    init_params(&p, UINT64_C(1) << 32, 65536, 0);
    if (!mpi_setup(argc, argv, USO, &p, &d)) return mpi_finish(1);
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) mpi_fail("No se pudo crear el contexto AES.");
    unsigned char plain[MAX_MESSAGE + 16];
    int plen = (int)strlen(p.phrase);
    uint64_t found = NO_KEY, attempts = 0, total = 0;
    uint64_t stride = (uint64_t)size * p.batch;
    /* Fin de la ventana; se evita el desbordamiento al sumar offset + limite. */
    uint64_t hi = p.offset + p.limit; if (hi < p.offset) hi = UINT64_MAX;
    int timed_out = 0;
    MPI_Barrier(MPI_COMM_WORLD);
    double start = MPI_Wtime();
    for (uint64_t base = p.offset; base < hi && !timed_out;) {
        uint64_t local = NO_KEY;
        uint64_t relative = (uint64_t)rank * p.batch;
        uint64_t first = relative < hi - base ? base + relative : hi;
        uint64_t count = hi - first < p.batch ? hi - first : p.batch;
        uint64_t end = first + count;
        for (uint64_t k = first; k < end; ++k) {
            int result = try_phrase(ctx, k, &d, plain, p.phrase, plen); ++attempts;
            if (result < 0) mpi_fail("Error de API AES.");
            if (result) { local = k; break; }
        }
        /* MIN: si dos procesos aciertan en la misma ronda se conserva la clave menor. */
        MPI_Allreduce(&local, &found, 1, MPI_UINT64_T, MPI_MIN, MPI_COMM_WORLD);
        if (found != NO_KEY) break;
        int expired = p.max_seconds && MPI_Wtime() - start >= (double)p.max_seconds;
        MPI_Allreduce(&expired, &timed_out, 1, MPI_INT, MPI_MAX, MPI_COMM_WORLD);
        if (stride >= hi - base) break;
        base += stride;
    }
    double local_time = MPI_Wtime() - start, elapsed = 0;
    MPI_Reduce(&local_time, &elapsed, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&attempts, &total, 1, MPI_UINT64_T, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0)
        print_report("base (lotes estaticos, Open MPI)", size, found, total, elapsed, timed_out, ctx, &d, &p);
    EVP_CIPHER_CTX_free(ctx);
    return mpi_finish(found != NO_KEY ? 0 : (timed_out ? 3 : 2));
}
