#include <glob.h>
#include <math.h>
#include <netcdf.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DUMP_MAGIC 20260523
#define NPROF 7
#define NSPEC 7

#define F_T 0
#define F_U 1
#define F_V 2
#define F_OMEGA 3
#define F_PMID 4
#define F_ZM 5
#define F_MBARV 6

#define S_O 0
#define S_O2 1
#define S_H 2
#define S_N 3
#define S_NO 4
#define S_N2 5
#define S_HE 6

typedef struct {
    int pver;
    int nsource;
    int nfiles;
    int packet;
    int nstep;
    double dtime_phys;
    int *present;
    double *lat;
    double *lon;
    double *ps;
    double *profile;
    double *qprof;
} LiveDump;

typedef struct {
    int nlat;
    int nlon;
    int nlev;
    int ncid;
} CamNc;

typedef enum {
    SPECIES_MOLMOL,
    SPECIES_MASS
} SpeciesMode;

typedef struct {
    long long n;
    long long live_bad;
    long long nc_bad;
    double live_min;
    double live_max;
    double nc_min;
    double nc_max;
    double max_abs;
    double max_rel;
    long double sumsq;
    int worst_src;
    int worst_lev;
} DiffStats;

static const double species_mw[NSPEC] = {16.0, 32.0, 1.0, 14.0, 30.0, 28.0, 4.0};

static void die(const char *msg) {
    fprintf(stderr, "%s\n", msg);
    exit(2);
}

static void *xmalloc(size_t n) {
    void *p = malloc(n);
    if (!p) die("allocation failed");
    return p;
}

static void *xcalloc(size_t n, size_t size) {
    void *p = calloc(n, size);
    if (!p) die("allocation failed");
    return p;
}

static void nc_check(int status, const char *what) {
    if (status != NC_NOERR) {
        fprintf(stderr, "netCDF error at %s: %s\n", what, nc_strerror(status));
        exit(2);
    }
}

static int finite_value(double x) {
    return isfinite(x) && fabs(x) < 1.0e300;
}

static void read_exact(FILE *fp, void *dst, size_t size, const char *what, const char *path) {
    if (size > 0 && fread(dst, 1, size, fp) != size) {
        fprintf(stderr, "failed to read %s from %s\n", what, path);
        exit(2);
    }
}

static void skip_exact(FILE *fp, size_t size, const char *what, const char *path) {
    if (size > 0 && fseek(fp, (long)size, SEEK_CUR) != 0) {
        fprintf(stderr, "failed to skip %s in %s\n", what, path);
        exit(2);
    }
}

static size_t idx_prof(const LiveDump *ld, int lev, int src, int field) {
    return ((size_t)field * (size_t)ld->nsource + (size_t)src) * (size_t)ld->pver + (size_t)lev;
}

static size_t idx_q(const LiveDump *ld, int lev, int src, int species) {
    return ((size_t)species * (size_t)ld->nsource + (size_t)src) * (size_t)ld->pver + (size_t)lev;
}

static size_t idx_nc3(int lev, int src, int nlat, int nlon) {
    int ilat = src / nlon;
    int ilon = src - ilat * nlon;
    return ((size_t)lev * (size_t)nlat + (size_t)ilat) * (size_t)nlon + (size_t)ilon;
}

static size_t idx_nc2(int src, int nlon) {
    int ilat = src / nlon;
    int ilon = src - ilat * nlon;
    return (size_t)ilat * (size_t)nlon + (size_t)ilon;
}

static void scan_dump_pattern(const char *pattern, glob_t *g, int *pver, int *nsource,
                              int *nstep, int *packet, double *dtime) {
    int rc = glob(pattern, 0, NULL, g);
    int max_cid = 0;
    *pver = -1;
    *nsource = 0;
    *nstep = -1;
    *packet = -1;
    *dtime = 0.0;
    if (rc != 0 || g->gl_pathc == 0) {
        fprintf(stderr, "no live dump files matched: %s\n", pattern);
        exit(2);
    }
    for (size_t f = 0; f < g->gl_pathc; ++f) {
        const char *path = g->gl_pathv[f];
        FILE *fp = fopen(path, "rb");
        int32_t header[12];
        double this_dtime;
        int32_t *cid;
        int ncols;
        if (!fp) {
            perror(path);
            exit(2);
        }
        read_exact(fp, header, sizeof(header), "dump header", path);
        if (header[0] != DUMP_MAGIC || header[1] != 1 || header[7] != NSPEC || header[8] != NPROF) {
            fprintf(stderr, "bad live dump header in %s\n", path);
            exit(2);
        }
        if (*pver < 0) *pver = header[6];
        if (*nstep < 0) *nstep = header[2];
        if (*packet < 0) *packet = header[3];
        if (*pver != header[6] || *nstep != header[2] || *packet != header[3]) {
            fprintf(stderr, "mixed pver/nstep/packet in live dump pattern at %s\n", path);
            exit(2);
        }
        ncols = header[9];
        read_exact(fp, &this_dtime, sizeof(double), "dtime", path);
        if (f == 0) *dtime = this_dtime;
        skip_exact(fp, sizeof(int32_t) * NSPEC, "species indices", path);
        cid = (int32_t *)xmalloc((size_t)ncols * sizeof(int32_t));
        read_exact(fp, cid, (size_t)ncols * sizeof(int32_t), "cid", path);
        for (int i = 0; i < ncols; ++i) {
            if (cid[i] > max_cid) max_cid = cid[i];
        }
        free(cid);
        fclose(fp);
    }
    *nsource = max_cid;
}

static LiveDump load_dump_pattern(const char *pattern) {
    glob_t g;
    LiveDump ld;
    memset(&ld, 0, sizeof(ld));
    scan_dump_pattern(pattern, &g, &ld.pver, &ld.nsource, &ld.nstep, &ld.packet, &ld.dtime_phys);
    ld.nfiles = (int)g.gl_pathc;
    ld.present = (int *)xcalloc((size_t)ld.nsource, sizeof(int));
    ld.lat = (double *)xcalloc((size_t)ld.nsource, sizeof(double));
    ld.lon = (double *)xcalloc((size_t)ld.nsource, sizeof(double));
    ld.ps = (double *)xcalloc((size_t)ld.nsource, sizeof(double));
    ld.profile = (double *)xmalloc((size_t)NPROF * (size_t)ld.nsource * (size_t)ld.pver * sizeof(double));
    ld.qprof = (double *)xmalloc((size_t)NSPEC * (size_t)ld.nsource * (size_t)ld.pver * sizeof(double));
    for (size_t i = 0; i < (size_t)NPROF * (size_t)ld.nsource * (size_t)ld.pver; ++i) ld.profile[i] = NAN;
    for (size_t i = 0; i < (size_t)NSPEC * (size_t)ld.nsource * (size_t)ld.pver; ++i) ld.qprof[i] = NAN;

    for (size_t f = 0; f < g.gl_pathc; ++f) {
        const char *path = g.gl_pathv[f];
        FILE *fp = fopen(path, "rb");
        int32_t header[12];
        int ncols;
        double dtime;
        int32_t *cid, *tmpi;
        double *lat, *lon, *ps, *profile, *qprof;
        if (!fp) {
            perror(path);
            exit(2);
        }
        read_exact(fp, header, sizeof(header), "dump header", path);
        ncols = header[9];
        read_exact(fp, &dtime, sizeof(double), "dtime", path);
        skip_exact(fp, sizeof(int32_t) * NSPEC, "species indices", path);
        cid = (int32_t *)xmalloc((size_t)ncols * sizeof(int32_t));
        tmpi = (int32_t *)xmalloc((size_t)ncols * sizeof(int32_t));
        lat = (double *)xmalloc((size_t)ncols * sizeof(double));
        lon = (double *)xmalloc((size_t)ncols * sizeof(double));
        ps = (double *)xmalloc((size_t)ncols * sizeof(double));
        profile = (double *)xmalloc((size_t)ld.pver * (size_t)ncols * NPROF * sizeof(double));
        qprof = (double *)xmalloc((size_t)ld.pver * (size_t)ncols * NSPEC * sizeof(double));
        read_exact(fp, cid, (size_t)ncols * sizeof(int32_t), "cid", path);
        read_exact(fp, tmpi, (size_t)ncols * sizeof(int32_t), "lchnk", path);
        read_exact(fp, tmpi, (size_t)ncols * sizeof(int32_t), "col", path);
        read_exact(fp, lat, (size_t)ncols * sizeof(double), "lat", path);
        read_exact(fp, lon, (size_t)ncols * sizeof(double), "lon", path);
        read_exact(fp, ps, (size_t)ncols * sizeof(double), "ps", path);
        read_exact(fp, profile, (size_t)ld.pver * (size_t)ncols * NPROF * sizeof(double), "profile", path);
        read_exact(fp, qprof, (size_t)ld.pver * (size_t)ncols * NSPEC * sizeof(double), "qprof", path);
        fclose(fp);
        for (int c = 0; c < ncols; ++c) {
            int src = cid[c] - 1;
            if (src < 0 || src >= ld.nsource) continue;
            ld.present[src] = 1;
            ld.lat[src] = lat[c];
            ld.lon[src] = lon[c];
            ld.ps[src] = ps[c];
            for (int fprof = 0; fprof < NPROF; ++fprof) {
                for (int k = 0; k < ld.pver; ++k) {
                    size_t local_idx = (size_t)k + (size_t)ld.pver * ((size_t)c + (size_t)ncols * (size_t)fprof);
                    ld.profile[idx_prof(&ld, k, src, fprof)] = profile[local_idx];
                }
            }
            for (int sp = 0; sp < NSPEC; ++sp) {
                for (int k = 0; k < ld.pver; ++k) {
                    size_t local_idx = (size_t)k + (size_t)ld.pver * ((size_t)c + (size_t)ncols * (size_t)sp);
                    ld.qprof[idx_q(&ld, k, src, sp)] = qprof[local_idx];
                }
            }
        }
        free(cid);
        free(tmpi);
        free(lat);
        free(lon);
        free(ps);
        free(profile);
        free(qprof);
    }
    globfree(&g);
    return ld;
}

static void free_dump(LiveDump *ld) {
    free(ld->present);
    free(ld->lat);
    free(ld->lon);
    free(ld->ps);
    free(ld->profile);
    free(ld->qprof);
    memset(ld, 0, sizeof(*ld));
}

static int has_var(int ncid, const char *name) {
    int varid;
    return nc_inq_varid(ncid, name, &varid) == NC_NOERR;
}

static size_t dim_len(int ncid, const char *name) {
    int dimid;
    size_t len;
    nc_check(nc_inq_dimid(ncid, name, &dimid), name);
    nc_check(nc_inq_dimlen(ncid, dimid, &len), name);
    return len;
}

static CamNc open_cam_nc(const char *path) {
    CamNc cam;
    memset(&cam, 0, sizeof(cam));
    nc_check(nc_open(path, NC_NOWRITE, &cam.ncid), path);
    cam.nlat = (int)dim_len(cam.ncid, "lat");
    cam.nlon = (int)dim_len(cam.ncid, "lon");
    cam.nlev = (int)dim_len(cam.ncid, "lev");
    return cam;
}

static char *read_att_string(int ncid, const char *var, const char *att) {
    int varid;
    size_t len = 0;
    char *buf;
    if (nc_inq_varid(ncid, var, &varid) != NC_NOERR) return strdup("");
    if (nc_inq_attlen(ncid, varid, att, &len) != NC_NOERR) return strdup("");
    buf = (char *)xmalloc(len + 1);
    if (nc_get_att_text(ncid, varid, att, buf) != NC_NOERR) {
        free(buf);
        return strdup("");
    }
    buf[len] = '\0';
    return buf;
}

static double *read_nc_var3(const CamNc *cam, const char *name) {
    int varid, ndims;
    int dimids[NC_MAX_VAR_DIMS];
    nc_type xtype;
    double *buf = (double *)xmalloc((size_t)cam->nlev * (size_t)cam->nlat * (size_t)cam->nlon * sizeof(double));
    nc_check(nc_inq_varid(cam->ncid, name, &varid), name);
    nc_check(nc_inq_var(cam->ncid, varid, NULL, &xtype, &ndims, dimids, NULL), name);
    if (ndims == 3) {
        nc_check(nc_get_var_double(cam->ncid, varid, buf), name);
    } else if (ndims == 4) {
        size_t start[4] = {0, 0, 0, 0};
        size_t count[4] = {1, (size_t)cam->nlev, (size_t)cam->nlat, (size_t)cam->nlon};
        nc_check(nc_get_vara_double(cam->ncid, varid, start, count, buf), name);
    } else {
        fprintf(stderr, "%s: expected rank 3 or 4, got %d\n", name, ndims);
        exit(2);
    }
    return buf;
}

static double *read_nc_var2(const CamNc *cam, const char *name) {
    int varid, ndims;
    int dimids[NC_MAX_VAR_DIMS];
    nc_type xtype;
    double *buf = (double *)xmalloc((size_t)cam->nlat * (size_t)cam->nlon * sizeof(double));
    nc_check(nc_inq_varid(cam->ncid, name, &varid), name);
    nc_check(nc_inq_var(cam->ncid, varid, NULL, &xtype, &ndims, dimids, NULL), name);
    if (ndims == 2) {
        nc_check(nc_get_var_double(cam->ncid, varid, buf), name);
    } else if (ndims == 3) {
        size_t start[3] = {0, 0, 0};
        size_t count[3] = {1, (size_t)cam->nlat, (size_t)cam->nlon};
        nc_check(nc_get_vara_double(cam->ncid, varid, start, count, buf), name);
    } else {
        fprintf(stderr, "%s: expected rank 2 or 3, got %d\n", name, ndims);
        exit(2);
    }
    return buf;
}

static void init_stats(DiffStats *st) {
    memset(st, 0, sizeof(*st));
    st->live_min = HUGE_VAL;
    st->live_max = -HUGE_VAL;
    st->nc_min = HUGE_VAL;
    st->nc_max = -HUGE_VAL;
    st->worst_src = -1;
    st->worst_lev = -1;
}

static void update_stats(DiffStats *st, double live, double nc, int src, int lev) {
    int live_ok = finite_value(live);
    int nc_ok = finite_value(nc);
    if (!live_ok) {
        st->live_bad++;
        return;
    }
    if (!nc_ok) {
        st->nc_bad++;
        return;
    }
    double diff = fabs(live - nc);
    double denom = fmax(fabs(nc), 1.0e-300);
    double rel = diff / denom;
    st->n++;
    if (live < st->live_min) st->live_min = live;
    if (live > st->live_max) st->live_max = live;
    if (nc < st->nc_min) st->nc_min = nc;
    if (nc > st->nc_max) st->nc_max = nc;
    st->sumsq += (long double)diff * (long double)diff;
    if (diff > st->max_abs) {
        st->max_abs = diff;
        st->worst_src = src;
        st->worst_lev = lev;
    }
    if (rel > st->max_rel) st->max_rel = rel;
}

static void print_stats(const char *label, const char *nc_var, const char *units,
                        const char *cell_methods, const DiffStats *st, int nlon) {
    double rms = st->n > 0 ? sqrt((double)(st->sumsq / (long double)st->n)) : NAN;
    int cid = st->worst_src >= 0 ? st->worst_src + 1 : -1;
    int ilat = st->worst_src >= 0 ? st->worst_src / nlon : -1;
    int ilon = st->worst_src >= 0 ? st->worst_src - ilat * nlon : -1;
    printf("FIELD %-14s nc=%-8s units=%-10s n=%lld live_bad=%lld nc_bad=%lld "
           "max_abs=%.17g rms_abs=%.17g max_rel=%.17g live_min=%.17g live_max=%.17g "
           "nc_min=%.17g nc_max=%.17g worst_cid=%d worst_lev=%d worst_lat_index=%d "
           "worst_lon_index=%d cell_methods=\"%s\"\n",
           label, nc_var, units, st->n, st->live_bad, st->nc_bad,
           st->max_abs, rms, st->max_rel, st->live_min, st->live_max,
           st->nc_min, st->nc_max, cid, st->worst_lev + 1, ilat + 1, ilon + 1,
           cell_methods);
}

static void compare_profile_field(const LiveDump *ld, const CamNc *cam, const char *label,
                                  int live_field, const char *nc_var, const char *units,
                                  double scale_live) {
    double *nc = read_nc_var3(cam, nc_var);
    DiffStats st;
    char *cell_methods = read_att_string(cam->ncid, nc_var, "cell_methods");
    init_stats(&st);
    for (int src = 0; src < ld->nsource; ++src) {
        if (!ld->present[src]) continue;
        for (int k = 0; k < ld->pver; ++k) {
            double live = scale_live * ld->profile[idx_prof(ld, k, src, live_field)];
            double nv = nc[idx_nc3(k, src, cam->nlat, cam->nlon)];
            update_stats(&st, live, nv, src, k);
        }
    }
    print_stats(label, nc_var, units, cell_methods, &st, cam->nlon);
    free(cell_methods);
    free(nc);
}

static void compare_ps(const LiveDump *ld, const CamNc *cam) {
    double *nc = read_nc_var2(cam, "PS");
    DiffStats st;
    char *cell_methods = read_att_string(cam->ncid, "PS", "cell_methods");
    init_stats(&st);
    for (int src = 0; src < ld->nsource; ++src) {
        if (!ld->present[src]) continue;
        update_stats(&st, ld->ps[src], nc[idx_nc2(src, cam->nlon)], src, 0);
    }
    print_stats("PS", "PS", "Pa", cell_methods, &st, cam->nlon);
    free(cell_methods);
    free(nc);
}

static void compare_species_molmol(const LiveDump *ld, const CamNc *cam, const char *label,
                                   int species, const char *nc_var) {
    double *nc = read_nc_var3(cam, nc_var);
    DiffStats st;
    char *cell_methods = read_att_string(cam->ncid, nc_var, "cell_methods");
    init_stats(&st);
    for (int src = 0; src < ld->nsource; ++src) {
        if (!ld->present[src]) continue;
        for (int k = 0; k < ld->pver; ++k) {
            double q = ld->qprof[idx_q(ld, k, src, species)];
            double mbarv = ld->profile[idx_prof(ld, k, src, F_MBARV)];
            double live = q * mbarv / species_mw[species];
            double nv = nc[idx_nc3(k, src, cam->nlat, cam->nlon)];
            update_stats(&st, live, nv, src, k);
        }
    }
    print_stats(label, nc_var, "mol/mol", cell_methods, &st, cam->nlon);
    free(cell_methods);
    free(nc);
}

static void compare_species_mass(const LiveDump *ld, const CamNc *cam, const char *label,
                                 int species, const char *nc_var) {
    double *nc = read_nc_var3(cam, nc_var);
    DiffStats st;
    char *cell_methods = read_att_string(cam->ncid, nc_var, "cell_methods");
    init_stats(&st);
    for (int src = 0; src < ld->nsource; ++src) {
        if (!ld->present[src]) continue;
        for (int k = 0; k < ld->pver; ++k) {
            double live = ld->qprof[idx_q(ld, k, src, species)];
            double nv = nc[idx_nc3(k, src, cam->nlat, cam->nlon)];
            update_stats(&st, live, nv, src, k);
        }
    }
    print_stats(label, nc_var, "kg/kg", cell_methods, &st, cam->nlon);
    free(cell_methods);
    free(nc);
}

static void compare_species(const LiveDump *ld, const CamNc *cam, SpeciesMode mode,
                            const char *base_label, int species, const char *nc_var) {
    char label[64];
    if (mode == SPECIES_MASS) {
        snprintf(label, sizeof(label), "%s_qmass", base_label);
        compare_species_mass(ld, cam, label, species, nc_var);
    } else {
        snprintf(label, sizeof(label), "%s_molmol", base_label);
        compare_species_molmol(ld, cam, label, species, nc_var);
    }
}

static void compare_latlon(const LiveDump *ld, const CamNc *cam) {
    double *lat = (double *)xmalloc((size_t)cam->nlat * sizeof(double));
    double *lon = (double *)xmalloc((size_t)cam->nlon * sizeof(double));
    int varid;
    DiffStats latst, lonst;
    init_stats(&latst);
    init_stats(&lonst);
    nc_check(nc_inq_varid(cam->ncid, "lat", &varid), "lat");
    nc_check(nc_get_var_double(cam->ncid, varid, lat), "lat");
    nc_check(nc_inq_varid(cam->ncid, "lon", &varid), "lon");
    nc_check(nc_get_var_double(cam->ncid, varid, lon), "lon");
    for (int src = 0; src < ld->nsource; ++src) {
        if (!ld->present[src]) continue;
        int ilat = src / cam->nlon;
        int ilon = src - ilat * cam->nlon;
        update_stats(&latst, ld->lat[src], lat[ilat], src, 0);
        update_stats(&lonst, ld->lon[src], lon[ilon], src, 0);
    }
    print_stats("lat", "lat", "deg", "", &latst, cam->nlon);
    print_stats("lon", "lon", "deg", "", &lonst, cam->nlon);
    free(lat);
    free(lon);
}

static void usage(const char *argv0) {
    fprintf(stderr, "usage: %s [--species-mode molmol|mass] '<live_dump_glob>' cam_history_or_restart.nc\n", argv0);
    fprintf(stderr, "example: %s --species-mode molmol '/path/wxsami3_physstate_rank*_pkt000000.bin' case.cam.rh0....nc\n", argv0);
    fprintf(stderr, "         %s --species-mode mass   '/path/wxsami3_physstate_rank*_pkt000000.bin' case.cam.r....nc\n", argv0);
}

int main(int argc, char **argv) {
    LiveDump ld;
    CamNc cam;
    SpeciesMode species_mode = SPECIES_MOLMOL;
    const char *pattern;
    const char *nc_path;
    int argi = 1;
    if (argc > 1 && strcmp(argv[argi], "--species-mode") == 0) {
        if (argc <= argi + 1) {
            usage(argv[0]);
            return 2;
        }
        if (strcmp(argv[argi + 1], "mass") == 0) {
            species_mode = SPECIES_MASS;
        } else if (strcmp(argv[argi + 1], "molmol") == 0) {
            species_mode = SPECIES_MOLMOL;
        } else {
            usage(argv[0]);
            return 2;
        }
        argi += 2;
    }
    if (argc - argi != 2) {
        usage(argv[0]);
        return 2;
    }
    pattern = argv[argi];
    nc_path = argv[argi + 1];
    ld = load_dump_pattern(pattern);
    cam = open_cam_nc(nc_path);
    printf("LIVE_DUMP files=%d packet=%d nstep=%d dtime_phys_s=%.17g pver=%d nsource=%d\n",
           ld.nfiles, ld.packet, ld.nstep, ld.dtime_phys, ld.pver, ld.nsource);
    printf("CAM_NC path=%s lat=%d lon=%d lev=%d variables_are_compared_on_cid_lat_lon_order=1 species_mode=%s\n",
           nc_path, cam.nlat, cam.nlon, cam.nlev,
           species_mode == SPECIES_MASS ? "mass" : "molmol");
    if (ld.nsource != cam.nlat * cam.nlon || ld.pver != cam.nlev) {
        fprintf(stderr, "dimension mismatch: live nsource/pver=%d/%d nc nsource/lev=%d/%d\n",
                ld.nsource, ld.pver, cam.nlat * cam.nlon, cam.nlev);
        free_dump(&ld);
        nc_close(cam.ncid);
        return 2;
    }
    compare_latlon(&ld, &cam);
    compare_ps(&ld, &cam);
    if (has_var(cam.ncid, "T")) compare_profile_field(&ld, &cam, "T_K", F_T, "T", "K", 1.0);
    if (has_var(cam.ncid, "U")) compare_profile_field(&ld, &cam, "U_m_s", F_U, "U", "m/s", 1.0);
    if (has_var(cam.ncid, "V")) compare_profile_field(&ld, &cam, "V_m_s", F_V, "V", "m/s", 1.0);
    if (has_var(cam.ncid, "OMEGA")) compare_profile_field(&ld, &cam, "OMEGA_Pa_s", F_OMEGA, "OMEGA", "Pa/s", 1.0);
    if (has_var(cam.ncid, "Z3GM")) {
        compare_profile_field(&ld, &cam, "ZM_m", F_ZM, "Z3GM", "m", 1.0);
    } else if (has_var(cam.ncid, "Z3")) {
        compare_profile_field(&ld, &cam, "ZM_m", F_ZM, "Z3", "m", 1.0);
    }
    if (has_var(cam.ncid, "MBARV")) compare_profile_field(&ld, &cam, "MBARV", F_MBARV, "MBARV", "g/mole", 1.0);
    if (has_var(cam.ncid, "O")) compare_species(&ld, &cam, species_mode, "O", S_O, "O");
    if (has_var(cam.ncid, "O2")) compare_species(&ld, &cam, species_mode, "O2", S_O2, "O2");
    if (has_var(cam.ncid, "H")) compare_species(&ld, &cam, species_mode, "H", S_H, "H");
    if (has_var(cam.ncid, "N")) compare_species(&ld, &cam, species_mode, "N", S_N, "N");
    if (has_var(cam.ncid, "NO")) compare_species(&ld, &cam, species_mode, "NO", S_NO, "NO");
    printf("NOTE use --species-mode molmol for CAM history species with mol/mol attributes; use --species-mode mass for restart/internal q fields.\n");
    printf("NOTE history files with cell_methods=\"time: mean\" are diagnostic time means, not guaranteed bitwise snapshots of runtime phys_state(:).\n");
    free_dump(&ld);
    nc_close(cam.ncid);
    return 0;
}
