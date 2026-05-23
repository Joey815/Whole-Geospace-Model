#include <mpi.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define TAG_HEADER 200
#define TAG_HR     201
#define TAG_DENNI  202
#define TAG_TNI    203
#define TAG_UI     204
#define TAG_VI     205
#define TAG_WI     206
#define TAG_DENNF  207
#define TAG_TNF    208
#define TAG_UF     209
#define TAG_VF     210
#define TAG_WF     211
#define TAG_DONE   299

static void die(const char *msg)
{
    fprintf(stderr, "neutral sender fatal: %s\n", msg);
    MPI_Abort(MPI_COMM_WORLD, 2);
}

static void read_port_file(const char *path, char *port, int port_len)
{
    FILE *fp = NULL;
    for (int i = 0; i < 180; ++i) {
        fp = fopen(path, "r");
        if (fp) break;
        sleep(1);
    }
    if (!fp) {
        perror("open port file");
        die("failed to open port file");
    }
    if (!fgets(port, port_len, fp)) {
        perror("read port file");
        fclose(fp);
        die("failed to read port file");
    }
    fclose(fp);
    port[strcspn(port, "\r\n")] = '\0';
}

static void read_exact(FILE *fp, void *ptr, size_t nbytes, const char *what)
{
    if (fread(ptr, 1, nbytes, fp) != nbytes) {
        fprintf(stderr, "failed reading %s: %s\n", what, strerror(errno));
        die("payload read failed");
    }
}

static void send_rank_payload(MPI_Comm peer, const char *prefix, int rank,
                              int step, float packet_hour)
{
    char path[1024];
    FILE *fp;
    int file_header[5];
    int header[6];
    int nz, nf, nl, nneut;
    size_t nlocal, nlocal4;
    float *denni, *tni, *ui, *vi, *wi;
    float *dennf, *tnf, *uf, *vf, *wf;

    snprintf(path, sizeof(path), "%s%04d.bin", prefix, rank);
    fp = fopen(path, "rb");
    if (!fp) {
        perror(path);
        die("failed to open rank payload");
    }

    read_exact(fp, file_header, sizeof(file_header), "header");
    nz = file_header[1];
    nf = file_header[2];
    nl = file_header[3];
    nneut = file_header[4];
    nlocal = (size_t)nz * (size_t)nf * (size_t)nl;
    nlocal4 = nlocal * (size_t)nneut;

    denni = malloc(nlocal4 * sizeof(float));
    tni   = malloc(nlocal  * sizeof(float));
    ui    = malloc(nlocal  * sizeof(float));
    vi    = malloc(nlocal  * sizeof(float));
    wi    = malloc(nlocal  * sizeof(float));
    dennf = malloc(nlocal4 * sizeof(float));
    tnf   = malloc(nlocal  * sizeof(float));
    uf    = malloc(nlocal  * sizeof(float));
    vf    = malloc(nlocal  * sizeof(float));
    wf    = malloc(nlocal  * sizeof(float));
    if (!denni || !tni || !ui || !vi || !wi ||
        !dennf || !tnf || !uf || !vf || !wf) {
        die("allocation failed");
    }

    read_exact(fp, denni, nlocal4 * sizeof(float), "denni");
    read_exact(fp, tni,   nlocal  * sizeof(float), "tni");
    read_exact(fp, ui,    nlocal  * sizeof(float), "ui");
    read_exact(fp, vi,    nlocal  * sizeof(float), "vi");
    read_exact(fp, wi,    nlocal  * sizeof(float), "wi");
    read_exact(fp, dennf, nlocal4 * sizeof(float), "dennf");
    read_exact(fp, tnf,   nlocal  * sizeof(float), "tnf");
    read_exact(fp, uf,    nlocal  * sizeof(float), "uf");
    read_exact(fp, vf,    nlocal  * sizeof(float), "vf");
    read_exact(fp, wf,    nlocal  * sizeof(float), "wf");
    fclose(fp);

    header[0] = file_header[0];
    header[1] = nz;
    header[2] = nf;
    header[3] = nl;
    header[4] = nneut;
    header[5] = step;

    MPI_Send(header, 6, MPI_INT, rank, TAG_HEADER, peer);
    MPI_Send(&packet_hour, 1, MPI_FLOAT, rank, TAG_HR, peer);
    MPI_Send(denni, (int)nlocal4, MPI_FLOAT, rank, TAG_DENNI, peer);
    MPI_Send(tni,   (int)nlocal,  MPI_FLOAT, rank, TAG_TNI, peer);
    MPI_Send(ui,    (int)nlocal,  MPI_FLOAT, rank, TAG_UI, peer);
    MPI_Send(vi,    (int)nlocal,  MPI_FLOAT, rank, TAG_VI, peer);
    MPI_Send(wi,    (int)nlocal,  MPI_FLOAT, rank, TAG_WI, peer);
    MPI_Send(dennf, (int)nlocal4, MPI_FLOAT, rank, TAG_DENNF, peer);
    MPI_Send(tnf,   (int)nlocal,  MPI_FLOAT, rank, TAG_TNF, peer);
    MPI_Send(uf,    (int)nlocal,  MPI_FLOAT, rank, TAG_UF, peer);
    MPI_Send(vf,    (int)nlocal,  MPI_FLOAT, rank, TAG_VF, peer);
    MPI_Send(wf,    (int)nlocal,  MPI_FLOAT, rank, TAG_WF, peer);

    free(denni); free(tni); free(ui); free(vi); free(wi);
    free(dennf); free(tnf); free(uf); free(vf); free(wf);
}

int main(int argc, char **argv)
{
    int rank, rc;
    char port[MPI_MAX_PORT_NAME];
    MPI_Comm peer = MPI_COMM_NULL;
    const char *port_file;
    const char *payload_prefix;
    int step;
    int count = 1;
    int packet_index;
    float packet_hour;
    float hour_stride = 0.25f;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    if (argc != 5 && argc != 7) {
        if (rank == 0) {
            fprintf(stderr, "usage: %s PORT_FILE PAYLOAD_PREFIX STEP PACKET_HOUR [COUNT HOUR_STRIDE]\n", argv[0]);
        }
        MPI_Finalize();
        return 2;
    }

    port_file = argv[1];
    payload_prefix = argv[2];
    step = atoi(argv[3]);
    packet_hour = (float)atof(argv[4]);
    if (argc == 7) {
        count = atoi(argv[5]);
        hour_stride = (float)atof(argv[6]);
        if (count < 1) count = 1;
    }

    if (rank == 0) {
        read_port_file(port_file, port, sizeof(port));
        printf("NEUTRAL_SENDER connecting to %s\n", port);
        fflush(stdout);
    }

    rc = MPI_Comm_connect(port, MPI_INFO_NULL, 0, MPI_COMM_WORLD, &peer);
    if (rc != MPI_SUCCESS) die("MPI_Comm_connect failed");

    if (rank == 0) {
        printf("NEUTRAL_SENDER connected; sending count=%d start_step=%d start_packet_hour=%g hour_stride=%g\n",
               count, step, packet_hour, hour_stride);
        fflush(stdout);
        for (packet_index = 0; packet_index < count; ++packet_index) {
            int packet_step = step + packet_index;
            float packet_hr = packet_hour + hour_stride * (float)packet_index;
            for (int r = 1; r <= 32; ++r) {
                send_rank_payload(peer, payload_prefix, r, packet_step, packet_hr);
                printf("NEUTRAL_SENDER sent step=%d packet_hour=%g rank=%04d\n",
                       packet_step, packet_hr, r);
                fflush(stdout);
            }
        }
        {
            int done = 1;
            for (int r = 0; r <= 32; ++r) {
                MPI_Send(&done, 1, MPI_INT, r, TAG_DONE, peer);
            }
            printf("NEUTRAL_SENDER sent done signal\n");
            fflush(stdout);
        }
        printf("NEUTRAL_SENDER done\n");
        fflush(stdout);
    }

    MPI_Comm_disconnect(&peer);
    MPI_Finalize();
    return 0;
}
