#include <glob.h>
#include <math.h>
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
#define NNEUT 7
#define PAYLOAD_MAGIC 20260522
#define DUMP_MAGIC 20260523

#define PTH 0
#define PTO 1
#define PTNO 2
#define PTO2 3
#define PTHE 4
#define PTN2 5
#define PTN 6

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
    size_t npoints, n_s;
    int *col;
    int *row_start;
    int *row_count;
    double *s;
} Weights;

typedef struct {
    int pver;
    int nspecies;
    int nprofile;
    int nsource;
    int *present;
    double *lat_deg;
    double *lon_deg;
    double *ps;
    double *profile;
    double *qprof;
} LiveState;

typedef struct {
    long long samples;
    long long invalid_samples;
    long long bad_weighted_z;
    long long above_live_top;
    long long n2_residual_used;
    long long n2_residual_negative;
    double n2_residual_min;
    double n2_residual_max;
    double n2_residual_negative_min;
} SampleStats;

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

static size_t idx_sami3(size_t i, size_t j, size_t k) {
    return (k * NF + j) * NZ + i;
}

static size_t idx_sami4(size_t i, size_t j, size_t k, size_t n) {
    return (((n * NL + k) * NF + j) * NZ + i);
}

static size_t idx_prof(const LiveState *st, int lev, int src, int field) {
    return ((size_t)field * (size_t)st->nsource + (size_t)src) * (size_t)st->pver + (size_t)lev;
}

static size_t idx_q(const LiveState *st, int lev, int src, int species) {
    return ((size_t)species * (size_t)st->nsource + (size_t)src) * (size_t)st->pver + (size_t)lev;
}

static int finite_real(double x) {
    return isfinite(x) && fabs(x) < 1.0e300;
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
    if (nbytes2 != nbytes1) {
        fprintf(stderr, "bad trailing record marker in %s\n", path);
        exit(2);
    }
    fclose(fp);
    return dst;
}

static Weights load_esmf_weights(const char *path, size_t npoints) {
    int ncid, dimid, varid;
    size_t n_s;
    int *row;
    Weights w;

    memset(&w, 0, sizeof(w));
    nc_check(nc_open(path, NC_NOWRITE, &ncid), path);
    nc_check(nc_inq_dimid(ncid, "n_s", &dimid), "weights n_s dim");
    nc_check(nc_inq_dimlen(ncid, dimid, &n_s), "weights n_s len");
    row = (int *)xcalloc(n_s, sizeof(int));
    w.col = (int *)xcalloc(n_s, sizeof(int));
    w.s = (double *)xcalloc(n_s, sizeof(double));
    w.row_start = (int *)xmalloc(npoints * sizeof(int));
    w.row_count = (int *)xcalloc(npoints, sizeof(int));
    for (size_t i = 0; i < npoints; ++i) w.row_start[i] = -1;

    nc_check(nc_inq_varid(ncid, "row", &varid), "weights row");
    nc_check(nc_get_var_int(ncid, varid, row), "weights row read");
    nc_check(nc_inq_varid(ncid, "col", &varid), "weights col");
    nc_check(nc_get_var_int(ncid, varid, w.col), "weights col read");
    nc_check(nc_inq_varid(ncid, "S", &varid), "weights S");
    nc_check(nc_get_var_double(ncid, varid, w.s), "weights S read");
    nc_check(nc_close(ncid), "close weights");

    for (size_t i = 0; i < n_s; ++i) {
        int r = row[i] - 1;
        if (r < 0 || (size_t)r >= npoints) {
            fprintf(stderr, "weight row out of range: %d for npoints=%zu\n", row[i], npoints);
            exit(2);
        }
        if (w.row_start[r] < 0) w.row_start[r] = (int)i;
        w.row_count[r] += 1;
        w.col[i] -= 1;
    }
    free(row);
    w.npoints = npoints;
    w.n_s = n_s;
    fprintf(stderr, "loaded ESMF weights: npoints=%zu n_s=%zu\n", npoints, n_s);
    return w;
}

static void free_weights(Weights *w) {
    free(w->col);
    free(w->row_start);
    free(w->row_count);
    free(w->s);
    memset(w, 0, sizeof(*w));
}

static void scan_dump_pattern(const char *pattern, glob_t *g, int *pver, int *nspecies,
                              int *nprofile, int *nsource) {
    int rc = glob(pattern, 0, NULL, g);
    int max_cid = 0;
    *pver = 0;
    *nspecies = 0;
    *nprofile = 0;
    if (rc != 0 || g->gl_pathc == 0) {
        fprintf(stderr, "no live dump files matched: %s\n", pattern);
        exit(2);
    }
    for (size_t f = 0; f < g->gl_pathc; ++f) {
        const char *path = g->gl_pathv[f];
        FILE *fp = fopen(path, "rb");
        int32_t header[12];
        double dtime;
        int *species_ind, *cid;
        size_t ncols;
        if (!fp) {
            perror(path);
            exit(2);
        }
        read_exact(fp, header, sizeof(header), "dump header", path);
        if (header[0] != DUMP_MAGIC) {
            fprintf(stderr, "bad dump magic in %s: %d\n", path, header[0]);
            exit(2);
        }
        if (*pver == 0) *pver = header[6];
        if (*nspecies == 0) *nspecies = header[7];
        if (*nprofile == 0) *nprofile = header[8];
        if (*pver != header[6] || *nspecies != header[7] || *nprofile != header[8]) {
            fprintf(stderr, "inconsistent dump dimensions in %s\n", path);
            exit(2);
        }
        ncols = (size_t)header[9];
        read_exact(fp, &dtime, sizeof(double), "dtime", path);
        species_ind = (int *)xmalloc((size_t)(*nspecies) * sizeof(int));
        read_exact(fp, species_ind, (size_t)(*nspecies) * sizeof(int), "species indices", path);
        cid = (int *)xmalloc(ncols * sizeof(int));
        read_exact(fp, cid, ncols * sizeof(int), "cid", path);
        for (size_t i = 0; i < ncols; ++i) {
            if (cid[i] > max_cid) max_cid = cid[i];
        }
        free(species_ind);
        free(cid);
        fclose(fp);
    }
    *nsource = max_cid;
    if (*nsource <= 0) die("no valid positive cid found in live dump");
}

static LiveState load_live_state(const char *pattern) {
    glob_t g;
    LiveState st;
    int pver, nspecies, nprofile, nsource;
    int filled = 0, duplicates = 0;

    memset(&st, 0, sizeof(st));
    scan_dump_pattern(pattern, &g, &pver, &nspecies, &nprofile, &nsource);
    st.pver = pver;
    st.nspecies = nspecies;
    st.nprofile = nprofile;
    st.nsource = nsource;
    st.present = (int *)xcalloc((size_t)nsource, sizeof(int));
    st.lat_deg = (double *)xmalloc((size_t)nsource * sizeof(double));
    st.lon_deg = (double *)xmalloc((size_t)nsource * sizeof(double));
    st.ps = (double *)xmalloc((size_t)nsource * sizeof(double));
    st.profile = (double *)xmalloc((size_t)nsource * (size_t)pver * (size_t)nprofile * sizeof(double));
    st.qprof = (double *)xmalloc((size_t)nsource * (size_t)pver * (size_t)nspecies * sizeof(double));

    for (int i = 0; i < nsource; ++i) {
        st.lat_deg[i] = NAN;
        st.lon_deg[i] = NAN;
        st.ps[i] = NAN;
    }
    for (size_t i = 0; i < (size_t)nsource * (size_t)pver * (size_t)nprofile; ++i) st.profile[i] = NAN;
    for (size_t i = 0; i < (size_t)nsource * (size_t)pver * (size_t)nspecies; ++i) st.qprof[i] = NAN;

    for (size_t f = 0; f < g.gl_pathc; ++f) {
        const char *path = g.gl_pathv[f];
        FILE *fp = fopen(path, "rb");
        int32_t header[12];
        double dtime;
        int ncols;
        int *species_ind, *cid, *lchnk, *col;
        double *lat, *lon, *ps, *profile, *qprof;
        if (!fp) {
            perror(path);
            exit(2);
        }
        read_exact(fp, header, sizeof(header), "dump header", path);
        ncols = header[9];
        read_exact(fp, &dtime, sizeof(double), "dtime", path);
        species_ind = (int *)xmalloc((size_t)nspecies * sizeof(int));
        cid = (int *)xmalloc((size_t)ncols * sizeof(int));
        lchnk = (int *)xmalloc((size_t)ncols * sizeof(int));
        col = (int *)xmalloc((size_t)ncols * sizeof(int));
        lat = (double *)xmalloc((size_t)ncols * sizeof(double));
        lon = (double *)xmalloc((size_t)ncols * sizeof(double));
        ps = (double *)xmalloc((size_t)ncols * sizeof(double));
        profile = (double *)xmalloc((size_t)pver * (size_t)ncols * (size_t)nprofile * sizeof(double));
        qprof = (double *)xmalloc((size_t)pver * (size_t)ncols * (size_t)nspecies * sizeof(double));

        read_exact(fp, species_ind, (size_t)nspecies * sizeof(int), "species indices", path);
        read_exact(fp, cid, (size_t)ncols * sizeof(int), "cid", path);
        read_exact(fp, lchnk, (size_t)ncols * sizeof(int), "lchnk", path);
        read_exact(fp, col, (size_t)ncols * sizeof(int), "col", path);
        read_exact(fp, lat, (size_t)ncols * sizeof(double), "lat", path);
        read_exact(fp, lon, (size_t)ncols * sizeof(double), "lon", path);
        read_exact(fp, ps, (size_t)ncols * sizeof(double), "ps", path);
        read_exact(fp, profile, (size_t)pver * (size_t)ncols * (size_t)nprofile * sizeof(double), "profile", path);
        read_exact(fp, qprof, (size_t)pver * (size_t)ncols * (size_t)nspecies * sizeof(double), "qprof", path);
        fclose(fp);

        for (int c = 0; c < ncols; ++c) {
            int src = cid[c] - 1;
            if (src < 0 || src >= nsource) {
                fprintf(stderr, "cid out of range in %s: %d nsource=%d\n", path, cid[c], nsource);
                exit(2);
            }
            if (st.present[src]) duplicates++;
            else filled++;
            st.present[src] = 1;
            st.lat_deg[src] = lat[c];
            st.lon_deg[src] = lon[c];
            st.ps[src] = ps[c];
            for (int fidx = 0; fidx < nprofile; ++fidx) {
                for (int k = 0; k < pver; ++k) {
                    size_t in = ((size_t)fidx * (size_t)ncols + (size_t)c) * (size_t)pver + (size_t)k;
                    st.profile[idx_prof(&st, k, src, fidx)] = profile[in];
                }
            }
            for (int sidx = 0; sidx < nspecies; ++sidx) {
                for (int k = 0; k < pver; ++k) {
                    size_t in = ((size_t)sidx * (size_t)ncols + (size_t)c) * (size_t)pver + (size_t)k;
                    st.qprof[idx_q(&st, k, src, sidx)] = qprof[in];
                }
            }
        }

        free(species_ind); free(cid); free(lchnk); free(col);
        free(lat); free(lon); free(ps); free(profile); free(qprof);
    }
    globfree(&g);

    if (duplicates) {
        fprintf(stderr, "warning: duplicate cid entries overwritten: %d\n", duplicates);
    }
    fprintf(stderr, "loaded live dump: source_cols=%d filled=%d pver=%d\n", nsource, filled, pver);
    return st;
}

static void free_live_state(LiveState *st) {
    free(st->present);
    free(st->lat_deg);
    free(st->lon_deg);
    free(st->ps);
    free(st->profile);
    free(st->qprof);
    memset(st, 0, sizeof(*st));
}

static double weighted_profile(const LiveState *st, const Weights *w, size_t target_idx,
                               int lev, int field) {
    int start = w->row_start[target_idx];
    int count = w->row_count[target_idx];
    double sum = 0.0;
    double wsum = 0.0;
    if (start < 0 || count <= 0) return NAN;
    for (int q = 0; q < count; ++q) {
        size_t n = (size_t)(start + q);
        int src = w->col[n];
        double val;
        if (src < 0 || src >= st->nsource || !st->present[src]) return NAN;
        val = st->profile[idx_prof(st, lev, src, field)];
        if (!finite_real(val)) return NAN;
        sum += w->s[n] * val;
        wsum += w->s[n];
    }
    return wsum > 0.0 ? sum / wsum : NAN;
}

static double weighted_q(const LiveState *st, const Weights *w, size_t target_idx,
                         int lev, int species) {
    int start = w->row_start[target_idx];
    int count = w->row_count[target_idx];
    double sum = 0.0;
    double wsum = 0.0;
    if (start < 0 || count <= 0) return NAN;
    for (int q = 0; q < count; ++q) {
        size_t n = (size_t)(start + q);
        int src = w->col[n];
        double val;
        if (src < 0 || src >= st->nsource || !st->present[src]) return NAN;
        val = st->qprof[idx_q(st, lev, src, species)];
        if (!finite_real(val)) return NAN;
        sum += w->s[n] * val;
        wsum += w->s[n];
    }
    return wsum > 0.0 ? sum / wsum : NAN;
}

static double lerp(double a, double b, double w) {
    return a * (1.0 - w) + b * w;
}

static void mark_invalid_sample(float den[NNEUT], float *tn, float *uu, float *vv, float *ww) {
    for (int n = 0; n < NNEUT; ++n) den[n] = -1.0f;
    *tn = -1.0f;
    *uu = 0.0f;
    *vv = 0.0f;
    *ww = 0.0f;
}

static void init_sample_stats(SampleStats *stats) {
    memset(stats, 0, sizeof(*stats));
    stats->n2_residual_min = 1.0e300;
    stats->n2_residual_max = -1.0e300;
    stats->n2_residual_negative_min = 1.0e300;
}

static void record_n2_residual(SampleStats *stats, double residual) {
    if (!stats) return;
    stats->n2_residual_used++;
    if (residual < stats->n2_residual_min) stats->n2_residual_min = residual;
    if (residual > stats->n2_residual_max) stats->n2_residual_max = residual;
    if (residual < 0.0) {
        stats->n2_residual_negative++;
        if (residual < stats->n2_residual_negative_min) {
            stats->n2_residual_negative_min = residual;
        }
    }
}

static void print_sample_stats(const char *label, const SampleStats *stats) {
    double n2min = stats->n2_residual_used ? stats->n2_residual_min : NAN;
    double n2max = stats->n2_residual_used ? stats->n2_residual_max : NAN;
    double n2negmin = stats->n2_residual_negative ? stats->n2_residual_negative_min : NAN;
    fprintf(stderr,
            "sample QC %s: samples=%lld invalid=%lld bad_weighted_z=%lld "
            "above_live_top=%lld n2_residual_used=%lld "
            "n2_residual_negative=%lld n2_residual_min=%.17g "
            "n2_residual_max=%.17g n2_residual_negative_min=%.17g\n",
            label, stats->samples, stats->invalid_samples, stats->bad_weighted_z,
            stats->above_live_top, stats->n2_residual_used,
            stats->n2_residual_negative, n2min, n2max, n2negmin);
}

static double interp_weighted_profile(const LiveState *st, const Weights *weights,
                                      size_t target_idx, int l0, int l1, double w, int field) {
    double a = weighted_profile(st, weights, target_idx, l0, field);
    double b = weighted_profile(st, weights, target_idx, l1, field);
    if (!finite_real(a) || !finite_real(b)) return NAN;
    return lerp(a, b, w);
}

static double interp_weighted_q(const LiveState *st, const Weights *weights,
                                size_t target_idx, int l0, int l1, double w, int species) {
    double a = weighted_q(st, weights, target_idx, l0, species);
    double b = weighted_q(st, weights, target_idx, l1, species);
    if (!finite_real(a) || !finite_real(b)) return NAN;
    return fmax(lerp(a, b, w), 0.0);
}

static double density_cm3(double q, double mbarv, double pmid, double temp, double species_mw) {
    const double kb = 1.380649e-23;
    if (!finite_real(q) || !finite_real(mbarv) || !finite_real(pmid) || !finite_real(temp)) return NAN;
    if (temp <= 0.0 || pmid <= 0.0 || mbarv <= 0.0) return NAN;
    return q * mbarv / species_mw * pmid / (kb * temp) * 1.0e-6;
}

static float density_or_floor(double q, double mbarv, double pmid, double temp, double species_mw) {
    double d = density_cm3(q, mbarv, pmid, temp, species_mw);
    if (!finite_real(d)) return NAN;
    return (float)fmax(d, 1.0e-30);
}

static void sample_live(const LiveState *st, const Weights *weights, double target_alt_m,
                        size_t target_idx, float den[NNEUT], float *tn,
                        float *uu, float *vv, float *ww, SampleStats *stats) {
    double best = 1.0e300, wv = 0.0;
    double zmax = -1.0e300, zmin = 1.0e300;
    int l0 = 0, l1 = 0, lmin = 0;
    int bracketed = 0;

    if (stats) stats->samples++;
    for (int l = 0; l < st->pver; ++l) {
        double z = weighted_profile(st, weights, target_idx, l, F_ZM);
        double d;
        if (!finite_real(z)) {
            if (stats) {
                stats->bad_weighted_z++;
                stats->invalid_samples++;
            }
            mark_invalid_sample(den, tn, uu, vv, ww);
            return;
        }
        d = fabs(z - target_alt_m);
        if (d < best) { best = d; l0 = l; l1 = l; }
        if (z > zmax) { zmax = z; }
        if (z < zmin) { zmin = z; lmin = l; }
    }
    for (int l = 0; l + 1 < st->pver; ++l) {
        double z0 = weighted_profile(st, weights, target_idx, l, F_ZM);
        double z1 = weighted_profile(st, weights, target_idx, l + 1, F_ZM);
        if ((target_alt_m >= fmin(z0, z1)) && (target_alt_m <= fmax(z0, z1))) {
            l0 = l;
            l1 = l + 1;
            wv = (fabs(z1 - z0) > 1.0e-9) ? (target_alt_m - z0) / (z1 - z0) : 0.0;
            if (wv < 0.0) wv = 0.0;
            if (wv > 1.0) wv = 1.0;
            bracketed = 1;
            break;
        }
    }
    if (!bracketed && target_alt_m > zmax) {
        if (stats) {
            stats->above_live_top++;
            stats->invalid_samples++;
        }
        mark_invalid_sample(den, tn, uu, vv, ww);
        return;
    } else if (!bracketed && target_alt_m < zmin) {
        l0 = lmin;
        l1 = lmin;
        wv = 0.0;
    }

    double temp = interp_weighted_profile(st, weights, target_idx, l0, l1, wv, F_T);
    double uu_m = interp_weighted_profile(st, weights, target_idx, l0, l1, wv, F_U);
    double vv_m = interp_weighted_profile(st, weights, target_idx, l0, l1, wv, F_V);
    double pmid = interp_weighted_profile(st, weights, target_idx, l0, l1, wv, F_PMID);
    double mbar = interp_weighted_profile(st, weights, target_idx, l0, l1, wv, F_MBARV);
    double q_o = interp_weighted_q(st, weights, target_idx, l0, l1, wv, S_O);
    double q_o2 = interp_weighted_q(st, weights, target_idx, l0, l1, wv, S_O2);
    double q_h = interp_weighted_q(st, weights, target_idx, l0, l1, wv, S_H);
    double q_n = interp_weighted_q(st, weights, target_idx, l0, l1, wv, S_N);
    double q_no = interp_weighted_q(st, weights, target_idx, l0, l1, wv, S_NO);
    double q_n2 = interp_weighted_q(st, weights, target_idx, l0, l1, wv, S_N2);

    if (!finite_real(q_n2) && finite_real(q_h) && finite_real(q_o) &&
        finite_real(q_o2) && finite_real(q_n) && finite_real(q_no)) {
        double residual = 1.0 - q_h - q_o - q_o2 - q_n - q_no;
        record_n2_residual(stats, residual);
        q_n2 = fmax(residual, 1.0e-20);
    }
    if (!finite_real(temp) || !finite_real(uu_m) || !finite_real(vv_m) ||
        !finite_real(pmid) || !finite_real(mbar) ||
        !finite_real(q_h) || !finite_real(q_o) || !finite_real(q_o2) ||
        !finite_real(q_n) || !finite_real(q_no) || !finite_real(q_n2)) {
        if (stats) stats->invalid_samples++;
        mark_invalid_sample(den, tn, uu, vv, ww);
        return;
    }
    temp = fmax(temp, 50.0);

    den[PTH]  = density_or_floor(q_h,  mbar, pmid, temp, 1.0);
    den[PTO]  = density_or_floor(q_o,  mbar, pmid, temp, 16.0);
    den[PTNO] = density_or_floor(q_no, mbar, pmid, temp, 30.0);
    den[PTO2] = density_or_floor(q_o2, mbar, pmid, temp, 32.0);
    den[PTHE] = -1.0f;
    den[PTN2] = density_or_floor(q_n2, mbar, pmid, temp, 28.0);
    den[PTN]  = density_or_floor(q_n,  mbar, pmid, temp, 14.0);
    if (!finite_real(den[PTH]) || !finite_real(den[PTO]) || !finite_real(den[PTNO]) ||
        !finite_real(den[PTO2]) || !finite_real(den[PTN2]) || !finite_real(den[PTN])) {
        if (stats) stats->invalid_samples++;
        mark_invalid_sample(den, tn, uu, vv, ww);
        return;
    }
    *tn = (float)temp;
    *uu = (float)(100.0 * uu_m);
    *vv = (float)(100.0 * vv_m);
    *ww = 0.0f;
}

static void fill_rank_arrays(const LiveState *st, const Weights *weights, int rank,
                             const float *zalt, float *den, float *tn,
                             float *uu, float *vv, float *ww, SampleStats *stats) {
    for (int k = 0; k < NL; ++k) {
        int g = (rank - 1) * (NL - 2) + (k - 1);
        while (g < 0) g += NLT;
        while (g >= NLT) g -= NLT;
        for (int j = 0; j < NF; ++j) {
            for (int i = 0; i < NZ; ++i) {
                size_t gidx = ((size_t)g * NF + (size_t)j) * NZ + (size_t)i;
                size_t lidx = idx_sami3((size_t)i, (size_t)j, (size_t)k);
                float d[NNEUT];
                sample_live(st, weights, (double)zalt[gidx] * 1000.0, gidx,
                            d, &tn[lidx], &uu[lidx], &vv[lidx], &ww[lidx], stats);
                for (int n = 0; n < NNEUT; ++n) {
                    den[idx_sami4((size_t)i, (size_t)j, (size_t)k, (size_t)n)] = d[n];
                }
            }
        }
    }
}

static void write_rank_block(const char *prefix, int rank, int final_block,
                             const float *den, const float *tn, const float *uu,
                             const float *vv, const float *ww) {
    char path[1024];
    FILE *fp;
    snprintf(path, sizeof(path), "%s%04d.bin", prefix, rank);
    fp = fopen(path, final_block ? "ab" : "wb");
    if (!fp) {
        perror(path);
        exit(2);
    }
    if (!final_block) {
        int32_t hdr[5] = {PAYLOAD_MAGIC, NZ, NF, NL, NNEUT};
        fwrite(hdr, sizeof(int32_t), 5, fp);
    }
    fwrite(den, sizeof(float), (size_t)NZ * NF * NL * NNEUT, fp);
    fwrite(tn,  sizeof(float), (size_t)NZ * NF * NL, fp);
    fwrite(uu,  sizeof(float), (size_t)NZ * NF * NL, fp);
    fwrite(vv,  sizeof(float), (size_t)NZ * NF * NL, fp);
    fwrite(ww,  sizeof(float), (size_t)NZ * NF * NL, fp);
    fclose(fp);
}

static void write_payload_from_state(const LiveState *st, const Weights *weights,
                                     const float *zalt, const char *out_prefix,
                                     int final_block, const char *label) {
    size_t nlocal = (size_t)NZ * NF * NL;
    size_t nlocal4 = nlocal * NNEUT;
    SampleStats stats;
    init_sample_stats(&stats);
    for (int rank = 1; rank <= NUMWORK; ++rank) {
        float *den = (float *)xcalloc(nlocal4, sizeof(float));
        float *tn  = (float *)xcalloc(nlocal, sizeof(float));
        float *uu  = (float *)xcalloc(nlocal, sizeof(float));
        float *vv  = (float *)xcalloc(nlocal, sizeof(float));
        float *ww  = (float *)xcalloc(nlocal, sizeof(float));
        fill_rank_arrays(st, weights, rank, zalt, den, tn, uu, vv, ww, &stats);
        write_rank_block(out_prefix, rank, final_block, den, tn, uu, vv, ww);
        free(den); free(tn); free(uu); free(vv); free(ww);
    }
    print_sample_stats(label, &stats);
}

static void validate_weight_sources(const LiveState *st, const Weights *weights,
                                    const char *label) {
    if ((int)st->nsource < 1) die("empty live state");
    for (size_t i = 0; i < weights->n_s; ++i) {
        if (weights->col[i] < 0 || weights->col[i] >= st->nsource ||
            !st->present[weights->col[i]]) {
            fprintf(stderr, "ESMF source column %d is missing from live dump %s\n",
                    weights->col[i] + 1, label);
            exit(2);
        }
    }
}

int main(int argc, char **argv) {
    const char *pattern0, *pattern1, *grid_dir, *weights_path, *out_prefix;
    char path[1024];
    size_t ngrid = (size_t)NZ * NF * NLT;
    float *zalt;
    Weights weights;
    LiveState st0, st1;

    if (argc != 5 && argc != 6) {
        fprintf(stderr, "usage: %s LIVE_DUMP_PATTERN0 [LIVE_DUMP_PATTERN1] SAMI_GRID_DIR ESMF_WEIGHTS_NC OUT_PREFIX\n", argv[0]);
        return 2;
    }
    pattern0 = argv[1];
    if (argc == 5) {
        pattern1 = argv[1];
        grid_dir = argv[2];
        weights_path = argv[3];
        out_prefix = argv[4];
    } else {
        pattern1 = argv[2];
        grid_dir = argv[3];
        weights_path = argv[4];
        out_prefix = argv[5];
    }

    snprintf(path, sizeof(path), "%s/zaltu.dat", grid_dir);
    zalt = read_fortran_record_float(path, ngrid);
    weights = load_esmf_weights(weights_path, ngrid);
    st0 = load_live_state(pattern0);
    st1 = (strcmp(pattern0, pattern1) == 0) ? st0 : load_live_state(pattern1);

    validate_weight_sources(&st0, &weights, "pattern0");
    validate_weight_sources(&st1, &weights, "pattern1");

    write_payload_from_state(&st0, &weights, zalt, out_prefix, 0, "initial");
    write_payload_from_state(&st1, &weights, zalt, out_prefix, 1, "final");

    if (strcmp(pattern0, pattern1) != 0) free_live_state(&st1);
    free_live_state(&st0);
    free_weights(&weights);
    free(zalt);
    fprintf(stderr, "wrote live-dump replay payload prefix: %s\n", out_prefix);
    return 0;
}
