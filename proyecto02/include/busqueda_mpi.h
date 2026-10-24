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
    /* Tipos MPI explicitos: evita transmitir padding y representacion nativa del struct. */
    MPI_Bcast(&p->limit, 1, MPI_UINT64_T, 0, MPI_COMM_WORLD);
    MPI_Bcast(&p->batch, 1, MPI_UINT64_T, 0, MPI_COMM_WORLD);
    MPI_Bcast(&p->offset, 1, MPI_UINT64_T, 0, MPI_COMM_WORLD);
    MPI_Bcast(&p->max_seconds, 1, MPI_UINT64_T, 0, MPI_COMM_WORLD);
    MPI_Bcast(&p->exhaustive_only, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(p->phrase, FRASE_MAX + 1, MPI_CHAR, 0, MPI_COMM_WORLD);
    MPI_Bcast(&d->length, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(d->cipher, cipher_length(d->length), MPI_UNSIGNED_CHAR, 0, MPI_COMM_WORLD);
    MPI_Bcast(d->tag, AUTH_SIZE, MPI_UNSIGNED_CHAR, 0, MPI_COMM_WORLD);
    return 1;
}

static inline void mpi_fail(const char *message) {
    fprintf(stderr, "%s\n", message);
    MPI_Abort(MPI_COMM_WORLD, 1);
}
/* Estado de aplicacion explicito. El helper WSL lo recupera cuando PRRTE se
 * configura para finalizar normalmente ante estados no-cero de los ranks.
 * El ejecutable conserva su retorno habitual para lanzadores sin ese ajuste.
 */
static inline int mpi_finish(int status) {
    int rank, agreed;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Allreduce(&status, &agreed, 1, MPI_INT, MPI_MAX, MPI_COMM_WORLD);
    if (rank == 0) { printf("Estado MPI: %d\n", agreed); fflush(stdout); }
    MPI_Finalize();
    return agreed;
}
#endif
