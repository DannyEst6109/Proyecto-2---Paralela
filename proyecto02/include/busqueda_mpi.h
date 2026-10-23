/* Proyecto 02. Rutinas MPI compartidas por la busqueda base y la alternativa. */
#ifndef BUSQUEDA_MPI_H
#define BUSQUEDA_MPI_H
#include <mpi.h>
#include "busqueda.h"

/* El proceso 0 valida argumentos y archivo; el resultado se difunde a todos.
 * Retorna 1 si todos pueden continuar (todos los procesos retornan el mismo valor).
 */
static inline int mpi_setup(int argc, char **argv, const char *usage, Params *p, Dataset *d) {
    int rank, valid = 1;
    const char *file = NULL;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    if (rank == 0) {
        valid = parse_params(argc, argv, p, &file) && load_dataset(file, d) && phrase_fits(p, d);
        if (!valid) fprintf(stderr, "%s\nArgumentos o archivo AES invalidos.\n", usage);
    }
    MPI_Bcast(&valid, 1, MPI_INT, 0, MPI_COMM_WORLD);
    if (!valid) return 0;
    MPI_Bcast(p, (int)sizeof *p, MPI_BYTE, 0, MPI_COMM_WORLD);
    MPI_Bcast(&d->length, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(d->cipher, cipher_length(d->length), MPI_UNSIGNED_CHAR, 0, MPI_COMM_WORLD);
    return 1;
}

static inline void mpi_fail(const char *message) {
    fprintf(stderr, "%s\n", message);
    MPI_Abort(MPI_COMM_WORLD, 1);
}
#endif
