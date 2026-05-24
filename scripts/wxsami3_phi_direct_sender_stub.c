#include <mpi.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define TAG_PHI_HEADER      220
#define TAG_PHI_HOUR        221
#define TAG_PHI_VALID_UNTIL 222
#define TAG_PHI_DATA        223
#define TAG_DONE            299

#define PHI_MAGIC   20260524
#define PHI_VERSION 1
#define PHI_NLAT    125
#define PHI_NLON    97

typedef struct {
    float hour;
    float valid_until;
    float *phi;
} PhiFrame;

static void die(const char *msg)
{
    fprintf(stderr, "phi-direct sender fatal: %s\n", msg);
    MPI_Abort(MPI_COMM_WORLD, 2);
}

static void read_port_file(const char *path, char *port, int port_len)
{
    FILE *fp = NULL;

    for (int i = 0; i < 300; ++i) {
        fp = fopen(path, "r");
        if (fp) break;
        sleep(1);
    }
    if (!fp) {
        perror(path);
        die("failed to open direct phi port file");
    }
    if (!fgets(port, port_len, fp)) {
        perror(path);
        fclose(fp);
        die("failed to read direct phi port file");
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
    if (header[1] != PHI_VERSION || header[2] != PHI_NLAT ||
        header[3] != PHI_NLON) {
        fprintf(stderr,
                "MPI phi payload header mismatch: magic=%d version=%d nlat=%d nlon=%d nframes=%d\n",
                header[0], header[1], header[2], header[3], header[4]);
        die("MPI phi payload header mismatch");
    }
    nframes = header[4];
    if (nframes < 1) die("MPI phi payload contains no frames");

    frames = (PhiFrame *)calloc((size_t)nframes, sizeof(PhiFrame));
    if (!frames) die("MPI phi frame allocation failed");
    for (int i = 0; i < nframes; ++i) {
        int32_t frame_index;
        float frame_meta[2];

        read_exact(fp, &frame_index, sizeof(frame_index), "MPI phi frame index");
        if (frame_index != i) die("MPI phi frame index mismatch");
        read_exact(fp, frame_meta, sizeof(frame_meta), "MPI phi frame metadata");
        frames[i].hour = frame_meta[0];
        frames[i].valid_until = frame_meta[1];
        frames[i].phi = (float *)malloc((size_t)nphi * sizeof(float));
        if (!frames[i].phi) die("MPI phi frame allocation failed");
        read_exact(fp, frames[i].phi, (size_t)nphi * sizeof(float),
                   "MPI phi frame data");
    }

    *nframes_out = nframes;
    printf("PHI_DIRECT_SENDER payload_format=remix_sami3_phi_payload.v1 nframes=%d\n",
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

    if (!read_fortran_record(fp, &payload, &nbytes)) die("empty phi stream");
    current_hour = record_as_float(payload, nbytes,
                                   "initial phi hour record is not one float");
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
        payload = NULL;
        nframes += 1;
    }

    if (nframes < 1) die("phi stream contains no frames");
    *nframes_out = nframes;
    printf("PHI_DIRECT_SENDER payload_format=phi_weimer.inp nframes=%d\n", nframes);
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
        printf("PHI_DIRECT_SENDER sent frame=%d/%d hour=%g valid_until=%g\n",
               i, nframes, frames[i].hour, frames[i].valid_until);
        fflush(stdout);
    }
}

int main(int argc, char **argv)
{
    int rank, rc;
    char port[MPI_MAX_PORT_NAME];
    MPI_Comm peer = MPI_COMM_NULL;
    const char *port_file;
    const char *phi_stream;
    int done_value = 1;
    PhiFrame *frames = NULL;
    int nframes = 0;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    if (argc != 3 && argc != 4) {
        if (rank == 0) {
            fprintf(stderr, "usage: %s DIRECT_PHI_PORT_FILE PHI_STREAM [DONE_VALUE]\n",
                    argv[0]);
        }
        MPI_Finalize();
        return 2;
    }

    port_file = argv[1];
    phi_stream = argv[2];
    if (argc == 4) done_value = atoi(argv[3]);

    if (rank == 0) {
        frames = read_phi_stream(phi_stream, &nframes);
        read_port_file(port_file, port, sizeof(port));
        printf("PHI_DIRECT_SENDER connecting to %s\n", port);
        fflush(stdout);
    }

    rc = MPI_Comm_connect(port, MPI_INFO_NULL, 0, MPI_COMM_WORLD, &peer);
    if (rc != MPI_SUCCESS) die("MPI_Comm_connect failed");

    if (rank == 0) {
        send_phi_frames(peer, frames, nframes);
        MPI_Send(&done_value, 1, MPI_INT, 0, TAG_DONE, peer);
        printf("PHI_DIRECT_SENDER sent done=%d\n", done_value);
        fflush(stdout);
        free_phi_frames(frames, nframes);
    }

    MPI_Comm_disconnect(&peer);
    MPI_Finalize();
    return 0;
}
