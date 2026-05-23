#include <float.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

enum {
    TAG_HEADER = 200,
    TAG_HR = 201,
    TAG_DENNI = 202,
    TAG_TNI = 203,
    TAG_UI = 204,
    TAG_VI = 205,
    TAG_WI = 206,
    TAG_DENNF = 207,
    TAG_TNF = 208,
    TAG_UF = 209,
    TAG_VF = 210,
    TAG_WF = 211,
    TAG_DONE = 299,
    WXSAMI3_MAGIC = 20260522
};

static void abort_msg(int rank, const char *msg, int rc)
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

static void recv_float_field(MPI_Comm peer, int tag, float *buf, int n,
                             double *sum, float *minv, float *maxv)
{
    MPI_Recv(buf, n, MPI_FLOAT, 0, tag, peer, MPI_STATUS_IGNORE);
    for (int i = 0; i < n; ++i) {
        float v = buf[i];
        *sum += (double)v;
        if (v < *minv) *minv = v;
        if (v > *maxv) *maxv = v;
    }
}

int main(int argc, char **argv)
{
    int rank = -1, size = -1;
    int rc;
    const char *port_file;
    char port[MPI_MAX_PORT_NAME];
    MPI_Comm peer = MPI_COMM_NULL;
    int packets = 0;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc != 2) {
        if (rank == 0) fprintf(stderr, "usage: %s PORT_FILE\n", argv[0]);
        MPI_Finalize();
        return 2;
    }
    port_file = argv[1];
    memset(port, 0, sizeof(port));

    if (rank == 0) {
        rc = MPI_Open_port(MPI_INFO_NULL, port);
        if (rc != MPI_SUCCESS) abort_msg(rank, "MPI_Open_port failed", rc);
        write_port_file(port_file, port);
        printf("WXSAMI3_RECEIVER_STUB port ready: %s ranks=%d\n", port_file, size);
        fflush(stdout);
    }

    MPI_Bcast(port, MPI_MAX_PORT_NAME, MPI_CHAR, 0, MPI_COMM_WORLD);
    rc = MPI_Comm_accept(port, MPI_INFO_NULL, 0, MPI_COMM_WORLD, &peer);
    if (rc != MPI_SUCCESS) abort_msg(rank, "MPI_Comm_accept failed", rc);
    if (rank == 0) {
        printf("WXSAMI3_RECEIVER_STUB accepted CAM sender\n");
        fflush(stdout);
    }

    for (;;) {
        MPI_Status status;
        MPI_Probe(0, MPI_ANY_TAG, peer, &status);
        if (status.MPI_TAG == TAG_DONE) {
            int done_value = -1;
            MPI_Recv(&done_value, 1, MPI_INT, 0, TAG_DONE, peer, MPI_STATUS_IGNORE);
            printf("WXSAMI3_RECEIVER_STUB done rank=%d done_value=%d packets=%d\n",
                   rank, done_value, packets);
            fflush(stdout);
            break;
        }

        if (rank == 0) {
            fprintf(stderr, "rank 0 expected done tag, got tag=%d\n", status.MPI_TAG);
            abort_msg(rank, "unexpected rank0 payload", 3);
        }
        if (status.MPI_TAG != TAG_HEADER) {
            fprintf(stderr, "rank %d expected header tag, got tag=%d\n", rank, status.MPI_TAG);
            abort_msg(rank, "unexpected payload tag", 4);
        }

        int header[6];
        float packet_hour = -1.0f;
        MPI_Recv(header, 6, MPI_INT, 0, TAG_HEADER, peer, MPI_STATUS_IGNORE);
        MPI_Recv(&packet_hour, 1, MPI_FLOAT, 0, TAG_HR, peer, MPI_STATUS_IGNORE);
        if (header[0] != WXSAMI3_MAGIC) {
            fprintf(stderr, "rank %d bad magic=%d\n", rank, header[0]);
            abort_msg(rank, "bad payload magic", 5);
        }

        int nz = header[1], nf = header[2], nl = header[3], nneut = header[4];
        int nlocal = nz * nf * nl;
        int nlocal4 = nlocal * nneut;
        int max_count = nlocal4 > nlocal ? nlocal4 : nlocal;
        float *buf = (float *)malloc((size_t)max_count * sizeof(float));
        if (!buf) abort_msg(rank, "allocation failed", 6);

        double sum = 0.0;
        float minv = FLT_MAX, maxv = -FLT_MAX;
        recv_float_field(peer, TAG_DENNI, buf, nlocal4, &sum, &minv, &maxv);
        recv_float_field(peer, TAG_TNI, buf, nlocal, &sum, &minv, &maxv);
        recv_float_field(peer, TAG_UI, buf, nlocal, &sum, &minv, &maxv);
        recv_float_field(peer, TAG_VI, buf, nlocal, &sum, &minv, &maxv);
        recv_float_field(peer, TAG_WI, buf, nlocal, &sum, &minv, &maxv);
        recv_float_field(peer, TAG_DENNF, buf, nlocal4, &sum, &minv, &maxv);
        recv_float_field(peer, TAG_TNF, buf, nlocal, &sum, &minv, &maxv);
        recv_float_field(peer, TAG_UF, buf, nlocal, &sum, &minv, &maxv);
        recv_float_field(peer, TAG_VF, buf, nlocal, &sum, &minv, &maxv);
        recv_float_field(peer, TAG_WF, buf, nlocal, &sum, &minv, &maxv);
        free(buf);
        packets++;

        printf("WXSAMI3_RECEIVER_STUB packet rank=%d packet=%d nstep=%d hour=%g nz=%d nf=%d nl=%d nneut=%d sum=%.17g min=%g max=%g\n",
               rank, packets - 1, header[5], packet_hour, nz, nf, nl, nneut,
               sum, minv, maxv);
        fflush(stdout);
    }

    MPI_Barrier(MPI_COMM_WORLD);
    MPI_Comm_disconnect(&peer);
    if (rank == 0) {
        MPI_Close_port(port);
        unlink(port_file);
        printf("WXSAMI3_RECEIVER_STUB complete\n");
        fflush(stdout);
    }

    MPI_Finalize();
    return 0;
}
