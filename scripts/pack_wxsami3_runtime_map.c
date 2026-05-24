#include <netcdf.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NZ 304
#define NF 124
#define NL 5
#define NUMWORK 32
#define NLT (NUMWORK * (NL - 2))
#define MAP_MAGIC 20260524

static void die(const char *msg) {
    fprintf(stderr, "%s\n", msg);
    exit(2);
}

static void nc_check(int status, const char *what) {
    if (status != NC_NOERR) {
        fprintf(stderr, "netCDF error at %s: %s\n", what, nc_strerror(status));
        exit(2);
    }
}

static void *xcalloc(size_t n, size_t size) {
    void *p = calloc(n, size);
    if (!p) die("allocation failed");
    return p;
}

static void *xmalloc(size_t size) {
    void *p = malloc(size);
    if (!p) die("allocation failed");
    return p;
}

static void read_exact(FILE *fp, void *dst, size_t size, const char *what, const char *path) {
    if (size > 0 && fread(dst, 1, size, fp) != size) {
        fprintf(stderr, "failed to read %s from %s\n", what, path);
        exit(2);
    }
}

static float *read_fortran_record_float(const char *path, size_t n) {
    FILE *fp = fopen(path, "rb");
    int32_t nbytes1 = 0, nbytes2 = 0;
    size_t want = n * sizeof(float);
    float *dst = (float *)xmalloc(want);
    if (!fp) {
        perror(path);
        exit(2);
    }
    read_exact(fp, &nbytes1, sizeof(int32_t), "record marker", path);
    if ((size_t)nbytes1 != want) {
        fprintf(stderr, "unexpected record size in %s: got %d expected %zu\n", path, nbytes1, want);
        exit(2);
    }
    read_exact(fp, dst, want, "payload", path);
    read_exact(fp, &nbytes2, sizeof(int32_t), "trailing marker", path);
    if (nbytes2 != nbytes1) die("bad trailing record marker");
    fclose(fp);
    return dst;
}

int main(int argc, char **argv) {
    const size_t npoints = (size_t)NZ * NF * NLT;
    const char *weights_path, *grid_dir, *out_path;
    char zalt_path[2048];
    int ncid, dimid, varid;
    size_t n_s;
    size_t nsource;
    int *row, *col, *row_start, *row_count;
    double *s;
    float *zalt;
    int32_t header[8];
    FILE *out;

    if (argc != 4) {
        fprintf(stderr, "usage: %s ESMF_WEIGHTS_NC SAMI_GRID_DIR OUT_MAP_BIN\n", argv[0]);
        return 2;
    }
    weights_path = argv[1];
    grid_dir = argv[2];
    out_path = argv[3];

    snprintf(zalt_path, sizeof(zalt_path), "%s/zaltu.dat", grid_dir);
    zalt = read_fortran_record_float(zalt_path, npoints);

    nc_check(nc_open(weights_path, NC_NOWRITE, &ncid), weights_path);
    nc_check(nc_inq_dimid(ncid, "n_s", &dimid), "weights n_s dim");
    nc_check(nc_inq_dimlen(ncid, dimid, &n_s), "weights n_s len");
    nc_check(nc_inq_dimid(ncid, "n_a", &dimid), "weights n_a dim");
    nc_check(nc_inq_dimlen(ncid, dimid, &nsource), "weights n_a len");
    if (n_s > INT32_MAX) die("n_s exceeds int32");
    if (nsource > INT32_MAX) die("n_a exceeds int32");

    row = (int *)xcalloc(n_s, sizeof(int));
    col = (int *)xcalloc(n_s, sizeof(int));
    s = (double *)xcalloc(n_s, sizeof(double));
    row_start = (int *)xcalloc(npoints, sizeof(int));
    row_count = (int *)xcalloc(npoints, sizeof(int));

    nc_check(nc_inq_varid(ncid, "row", &varid), "weights row");
    nc_check(nc_get_var_int(ncid, varid, row), "weights row read");
    nc_check(nc_inq_varid(ncid, "col", &varid), "weights col");
    nc_check(nc_get_var_int(ncid, varid, col), "weights col read");
    nc_check(nc_inq_varid(ncid, "S", &varid), "weights S");
    nc_check(nc_get_var_double(ncid, varid, s), "weights S read");
    nc_check(nc_close(ncid), "close weights");

    for (size_t i = 0; i < n_s; ++i) {
        int r = row[i];
        if (r < 1 || (size_t)r > npoints) {
            fprintf(stderr, "weight row out of range: %d\n", r);
            exit(2);
        }
        if (row_start[r - 1] == 0) row_start[r - 1] = (int)i + 1;
        row_count[r - 1] += 1;
        if (col[i] < 1 || (size_t)col[i] > nsource) {
            fprintf(stderr, "weight col out of range: %d for nsource=%zu\n", col[i], nsource);
            exit(2);
        }
    }

    out = fopen(out_path, "wb");
    if (!out) {
        perror(out_path);
        exit(2);
    }
    header[0] = MAP_MAGIC;
    header[1] = 1;
    header[2] = NZ;
    header[3] = NF;
    header[4] = NLT;
    header[5] = (int32_t)npoints;
    header[6] = (int32_t)n_s;
    header[7] = (int32_t)nsource;
    fwrite(header, sizeof(header), 1, out);
    fwrite(zalt, sizeof(float), npoints, out);
    fwrite(row_start, sizeof(int), npoints, out);
    fwrite(row_count, sizeof(int), npoints, out);
    fwrite(col, sizeof(int), n_s, out);
    fwrite(s, sizeof(double), n_s, out);
    fclose(out);

    fprintf(stderr, "wrote runtime map: %s npoints=%zu n_s=%zu nsource=%zu\n",
            out_path, npoints, n_s, nsource);
    free(row);
    free(col);
    free(s);
    free(row_start);
    free(row_count);
    free(zalt);
    return 0;
}
