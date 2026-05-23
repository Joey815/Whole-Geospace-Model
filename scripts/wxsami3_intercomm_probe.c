#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static void die(int rank, const char *msg, int rc)
{
    fprintf(stderr, "[%d] %s rc=%d\n", rank, msg, rc);
    MPI_Abort(MPI_COMM_WORLD, rc ? rc : 1);
}

static void write_port_file(const char *path, const char *port)
{
    FILE *fp = fopen(path, "w");
    if (!fp) {
        perror("fopen port file");
        MPI_Abort(MPI_COMM_WORLD, 2);
    }
    fprintf(fp, "%s\n", port);
    fclose(fp);
}

static void read_port_file(const char *path, char *port, int port_len)
{
    FILE *fp = NULL;
    for (int i = 0; i < 120; ++i) {
        fp = fopen(path, "r");
        if (fp) break;
        sleep(1);
    }
    if (!fp) {
        perror("open port file");
        MPI_Abort(MPI_COMM_WORLD, 3);
    }
    if (!fgets(port, port_len, fp)) {
        perror("read port file");
        fclose(fp);
        MPI_Abort(MPI_COMM_WORLD, 4);
    }
    fclose(fp);
    port[strcspn(port, "\r\n")] = '\0';
}

int main(int argc, char **argv)
{
    int rank = -1, size = -1;
    int rc;
    const char *mode;
    const char *port_file;
    MPI_Comm peer = MPI_COMM_NULL;
    char port[MPI_MAX_PORT_NAME];

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc != 3) {
        if (rank == 0) {
            fprintf(stderr, "usage: %s server|client PORT_FILE\n", argv[0]);
        }
        MPI_Finalize();
        return 2;
    }

    mode = argv[1];
    port_file = argv[2];

    if (strcmp(mode, "server") == 0) {
        if (rank == 0) {
            rc = MPI_Open_port(MPI_INFO_NULL, port);
            if (rc != MPI_SUCCESS) die(rank, "MPI_Open_port failed", rc);
            write_port_file(port_file, port);
            printf("SERVER opened port: %s\n", port);
            fflush(stdout);
            rc = MPI_Comm_accept(port, MPI_INFO_NULL, 0, MPI_COMM_WORLD, &peer);
            if (rc != MPI_SUCCESS) die(rank, "MPI_Comm_accept failed", rc);
            printf("SERVER accepted client\n");
            fflush(stdout);

            for (int i = 0; i < 4; ++i) {
                int step = -1;
                double vals[3] = {-1.0, -1.0, -1.0};
                MPI_Recv(&step, 1, MPI_INT, 0, 100, peer, MPI_STATUS_IGNORE);
                MPI_Recv(vals, 3, MPI_DOUBLE, 0, 101, peer, MPI_STATUS_IGNORE);
                printf("SERVER received step=%d vals=%g,%g,%g\n",
                       step, vals[0], vals[1], vals[2]);
                fflush(stdout);
            }

            MPI_Comm_disconnect(&peer);
            MPI_Close_port(port);
            unlink(port_file);
            printf("SERVER done\n");
            fflush(stdout);
        }
    } else if (strcmp(mode, "client") == 0) {
        if (rank == 0) {
            read_port_file(port_file, port, sizeof(port));
            printf("CLIENT connecting to port: %s\n", port);
            fflush(stdout);
            rc = MPI_Comm_connect(port, MPI_INFO_NULL, 0, MPI_COMM_WORLD, &peer);
            if (rc != MPI_SUCCESS) die(rank, "MPI_Comm_connect failed", rc);
            printf("CLIENT connected\n");
            fflush(stdout);

            for (int i = 0; i < 4; ++i) {
                int step = i;
                double vals[3] = {300.0 * i, 1000.0 + i, -10.0 - i};
                MPI_Send(&step, 1, MPI_INT, 0, 100, peer);
                MPI_Send(vals, 3, MPI_DOUBLE, 0, 101, peer);
                printf("CLIENT sent step=%d\n", step);
                fflush(stdout);
            }

            MPI_Comm_disconnect(&peer);
            printf("CLIENT done\n");
            fflush(stdout);
        }
    } else {
        if (rank == 0) fprintf(stderr, "unknown mode: %s\n", mode);
        MPI_Finalize();
        return 2;
    }

    MPI_Finalize();
    return 0;
}
