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
#define TAG_SOURCE_FLAGS 212

#define TAG_PHI_HEADER      220
#define TAG_PHI_HOUR        221
#define TAG_PHI_VALID_UNTIL 222
#define TAG_PHI_DATA        223

#define TAG_DONE   299

#define SOURCE_FLAG_WACCMX_VALID 1
#define SOURCE_FLAG_OTHER_INVALID 4
#define PHI_MAGIC 20260524
#define PHI_VERSION 1
#define PHI_NLAT 125
#define PHI_NLON 97

typedef struct {
    float hour;
    float valid_until;
    float *phi;
} PhiFrame;

static void die(const char *msg)
{
    fprintf(stderr, "neutral+phi sender fatal: %s\n", msg);
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

static int read_fortran_record(FILE *fp, unsigned char **payload, int *nbytes)
{
    int32_t head, tail;
    size_t nread = fread(&head, 1, sizeof(head), fp);
    if (nread == 0 && feof(fp)) return 0;
    if (nread != sizeof(head)) die("truncated Fortran record marker");
    if (head <= 0) die("invalid Fortran record length");
    *payload = (unsigned char *)malloc((size_t)head);
    if (!*payload) die("Fortran record allocation failed");
    read_exact(fp, *payload, (size_t)head, "Fortran record payload");
    read_exact(fp, &tail, sizeof(tail), "Fortran record tail");
    if (tail != head) die("Fortran record marker mismatch");
    *nbytes = (int)head;
    return 1;
}

static float record_as_float(unsigned char *payload, int nbytes, const char *what)
{
    float value;
    if (nbytes != (int)sizeof(float)) die(what);
    memcpy(&value, payload, sizeof(float));
    return value;
}

static PhiFrame *read_mpi_phi_payload(FILE *fp, int *nframes_out)
{
    int32_t header[5];
    int nframes;
    PhiFrame *frames;
    const int nphi = PHI_NLAT * PHI_NLON;

    read_exact(fp, &header[1], 4 * sizeof(int32_t), "MPI phi payload header");
    header[0] = PHI_MAGIC;

    if (header[1] != PHI_VERSION || header[2] != PHI_NLAT || header[3] != PHI_NLON) {
        fprintf(stderr,
                "MPI phi payload header mismatch: magic=%d version=%d nlat=%d nlon=%d nframes=%d\n",
                header[0], header[1], header[2], header[3], header[4]);
        die("MPI phi payload header mismatch");
    }
    nframes = header[4];
    if (nframes < 1) die("MPI phi payload contains no frames");

    frames = (PhiFrame *)calloc((size_t)nframes, sizeof(PhiFrame));
    if (!frames) die("MPI phi payload frame allocation failed");

    for (int i = 0; i < nframes; ++i) {
        int32_t frame_index;
        float frame_meta[2];

        read_exact(fp, &frame_index, sizeof(frame_index), "MPI phi payload frame index");
        if (frame_index != i) die("MPI phi payload frame index mismatch");
        read_exact(fp, frame_meta, sizeof(frame_meta), "MPI phi payload frame hour metadata");

        frames[i].hour = frame_meta[0];
        frames[i].valid_until = frame_meta[1];
        frames[i].phi = (float *)malloc((size_t)nphi * sizeof(float));
        if (!frames[i].phi) die("MPI phi payload phi allocation failed");
        read_exact(fp, frames[i].phi, (size_t)nphi * sizeof(float),
                   "MPI phi payload phi frame");
    }

    *nframes_out = nframes;
    printf("NEUTRAL_PHI_SENDER phi_payload_format=remix_sami3_phi_payload.v1 nframes=%d\n",
           nframes);
    fflush(stdout);
    return frames;
}

static PhiFrame *read_phi_weimer_stream(FILE *fp, int *nframes_out)
{
    unsigned char *payload = NULL;
    int nbytes = 0;
    float current_hour;
    int nframes = 0;
    int capacity = 4;
    PhiFrame *frames;
    const int nphi = PHI_NLAT * PHI_NLON;
    const int phi_nbytes = nphi * (int)sizeof(float);

    if (!read_fortran_record(fp, &payload, &nbytes)) {
        die("empty phi stream");
    }
    current_hour = record_as_float(payload, nbytes, "initial phi hour record is not one float");
    free(payload);

    frames = (PhiFrame *)calloc((size_t)capacity, sizeof(PhiFrame));
    if (!frames) die("phi frame allocation failed");

    while (read_fortran_record(fp, &payload, &nbytes)) {
        unsigned char *hour_payload = NULL;
        int hour_nbytes = 0;
        if (nbytes != phi_nbytes) die("phi frame has unexpected byte count");
        if (nframes == capacity) {
            capacity *= 2;
            frames = (PhiFrame *)realloc(frames, (size_t)capacity * sizeof(PhiFrame));
            if (!frames) die("phi frame realloc failed");
        }
        frames[nframes].hour = current_hour;
        frames[nframes].phi = (float *)payload;

        if (!read_fortran_record(fp, &hour_payload, &hour_nbytes)) {
            die("phi stream ended without next-hour record");
        }
        current_hour = record_as_float(hour_payload, hour_nbytes,
                                       "next phi hour record is not one float");
        frames[nframes].valid_until = current_hour;
        free(hour_payload);
        nframes += 1;
        payload = NULL;
    }

    if (nframes < 1) die("phi stream contains no frames");
    *nframes_out = nframes;
    printf("NEUTRAL_PHI_SENDER phi_payload_format=phi_weimer.inp nframes=%d\n", nframes);
    fflush(stdout);
    return frames;
}

static PhiFrame *read_phi_stream(const char *path, int *nframes_out)
{
    FILE *fp = fopen(path, "rb");
    int32_t first_word;
    PhiFrame *frames;

    if (!fp) {
        perror(path);
        die("failed to open phi stream");
    }
    read_exact(fp, &first_word, sizeof(first_word), "phi payload leading word");
    if (first_word == PHI_MAGIC) {
        frames = read_mpi_phi_payload(fp, nframes_out);
    } else {
        if (fseek(fp, 0L, SEEK_SET) != 0) die("failed to rewind phi_weimer stream");
        frames = read_phi_weimer_stream(fp, nframes_out);
    }
    fclose(fp);
    return frames;
}

static void free_phi_frames(PhiFrame *frames, int nframes)
{
    for (int i = 0; i < nframes; ++i) free(frames[i].phi);
    free(frames);
}

static void send_phi_frames(MPI_Comm peer, const PhiFrame *frames, int nframes)
{
    const int nphi = PHI_NLAT * PHI_NLON;
    for (int i = 0; i < nframes; ++i) {
        int header[6] = {PHI_MAGIC, PHI_VERSION, PHI_NLAT, PHI_NLON, i, nframes};
        MPI_Send(header, 6, MPI_INT, 0, TAG_PHI_HEADER, peer);
        MPI_Send((void *)&frames[i].hour, 1, MPI_FLOAT, 0, TAG_PHI_HOUR, peer);
        MPI_Send((void *)&frames[i].valid_until, 1, MPI_FLOAT, 0,
                 TAG_PHI_VALID_UNTIL, peer);
        MPI_Send(frames[i].phi, nphi, MPI_FLOAT, 0, TAG_PHI_DATA, peer);
        printf("NEUTRAL_PHI_SENDER sent phi frame=%d/%d hour=%g valid_until=%g minmax not computed\n",
               i, nframes, frames[i].hour, frames[i].valid_until);
        fflush(stdout);
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
    int *source_flags;

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
    source_flags = malloc(nlocal * sizeof(int));
    if (!denni || !tni || !ui || !vi || !wi ||
        !dennf || !tnf || !uf || !vf || !wf || !source_flags) {
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

    for (size_t i = 0; i < nlocal; ++i) {
        source_flags[i] = (denni[i] >= 0.0f) ?
            SOURCE_FLAG_WACCMX_VALID : SOURCE_FLAG_OTHER_INVALID;
    }

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
    MPI_Send(source_flags, (int)nlocal, MPI_INT, rank, TAG_SOURCE_FLAGS, peer);

    free(denni); free(tni); free(ui); free(vi); free(wi);
    free(dennf); free(tnf); free(uf); free(vf); free(wf);
    free(source_flags);
}

int main(int argc, char **argv)
{
    int rank, rc;
    char port[MPI_MAX_PORT_NAME];
    MPI_Comm peer = MPI_COMM_NULL;
    const char *port_file;
    const char *payload_prefix;
    const char *phi_stream;
    int step;
    int count = 1;
    int packet_index;
    float packet_hour;
    float hour_stride = 0.25f;
    PhiFrame *phi_frames = NULL;
    int nphi_frames = 0;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    if (argc != 6 && argc != 8) {
        if (rank == 0) {
            fprintf(stderr, "usage: %s PORT_FILE PAYLOAD_PREFIX STEP PACKET_HOUR PHI_STREAM [COUNT HOUR_STRIDE]\n", argv[0]);
        }
        MPI_Finalize();
        return 2;
    }

    port_file = argv[1];
    payload_prefix = argv[2];
    step = atoi(argv[3]);
    packet_hour = (float)atof(argv[4]);
    phi_stream = argv[5];
    if (argc == 8) {
        count = atoi(argv[6]);
        hour_stride = (float)atof(argv[7]);
        if (count < 1) count = 1;
    }

    if (rank == 0) {
        phi_frames = read_phi_stream(phi_stream, &nphi_frames);
        read_port_file(port_file, port, sizeof(port));
        printf("NEUTRAL_PHI_SENDER connecting to %s\n", port);
        printf("NEUTRAL_PHI_SENDER phi_stream=%s nframes=%d\n", phi_stream, nphi_frames);
        fflush(stdout);
    }

    rc = MPI_Comm_connect(port, MPI_INFO_NULL, 0, MPI_COMM_WORLD, &peer);
    if (rc != MPI_SUCCESS) die("MPI_Comm_connect failed");

    if (rank == 0) {
        printf("NEUTRAL_PHI_SENDER connected; sending neutral count=%d start_step=%d start_packet_hour=%g hour_stride=%g\n",
               count, step, packet_hour, hour_stride);
        fflush(stdout);
        for (packet_index = 0; packet_index < count; ++packet_index) {
            int packet_step = step + packet_index;
            float packet_hr = packet_hour + hour_stride * (float)packet_index;
            for (int r = 1; r <= 32; ++r) {
                send_rank_payload(peer, payload_prefix, r, packet_step, packet_hr);
                printf("NEUTRAL_PHI_SENDER sent neutral step=%d packet_hour=%g rank=%04d\n",
                       packet_step, packet_hr, r);
                fflush(stdout);
            }
        }

        send_phi_frames(peer, phi_frames, nphi_frames);

        {
            int done = 1;
            for (int r = 0; r <= 32; ++r) {
                MPI_Send(&done, 1, MPI_INT, r, TAG_DONE, peer);
            }
            printf("NEUTRAL_PHI_SENDER sent done signal\n");
            fflush(stdout);
        }
        printf("NEUTRAL_PHI_SENDER done\n");
        fflush(stdout);
        free_phi_frames(phi_frames, nphi_frames);
    }

    MPI_Comm_disconnect(&peer);
    MPI_Finalize();
    return 0;
}
