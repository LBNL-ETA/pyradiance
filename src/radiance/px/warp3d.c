#ifndef lint
static const char	RCSid[] = "$Id: warp3d.c,v 3.12 2024/02/22 17:45:27 greg Exp $";
#endif
/*
 * 3D warping routines.
 */

#include <stdlib.h>
#include <math.h>

#include "rterror.h"
#include "rtio.h"
#include "fvect.h"
#include "warp3d.h"

#define MIND	1e-5		/* minimum distance between input points */

typedef struct {
	GNDX	n;		/* index must be first */
	W3VEC	v;
} KEYDP;		/* key/data allocation pair */

#define fgetvec(p,v)	(fgetval(p,'f',v) > 0 && fgetval(p,'f',v+1) > 0 \
				&& fgetval(p,'f',v+2) > 0)

#define AHUNK	24		/* number of points to allocate at a time */


double wpdist2(W3VEC p1, W3VEC p2);
static int gridpoint(GNDX ndx, W3VEC rem, W3VEC ipt, struct grid3d *gp);
static int get3dgpt(W3VEC ov, GNDX ndx, WARP3D *wp);
static int get3dgin(W3VEC ov, GNDX ndx, W3VEC rem, WARP3D *wp);
static void l3interp(W3VEC vo, W3VEC *cl, W3VEC dv, int n);
static int warp3dex(W3VEC ov, W3VEC pi, WARP3D *wp);
static lut_hashf_t gridhash;
static int new3dgrid(WARP3D *wp);
static void done3dgrid(struct grid3d *gp);


double
wpdist2(			/* compute square of distance between points */
	W3VEC	p1,
	W3VEC	p2
)
{
	double	d, d2;

	d = p1[0] - p2[0]; d2  = d*d;
	d = p1[1] - p2[1]; d2 += d*d;
	d = p1[2] - p2[2]; d2 += d*d;
	return(d2);
}


int
warp3d(		/* warp 3D point according to the given map */
	W3VEC	po,
	W3VEC	pi,
	WARP3D	*wp
)
{
	int	rval = W3OK;
	GNDX	gi;
	W3VEC	gd, ov;

	if (wp->grid.gn[0] == 0 && (rval = new3dgrid(wp)) != W3OK)
		return(rval);
	rval |= gridpoint(gi, gd, pi, &wp->grid);
	if (wp->grid.flags & W3EXACT)
		rval |= warp3dex(ov, pi, wp);
	else if (wp->grid.flags & W3FAST)
		rval |= get3dgpt(ov, gi, wp);
	else
		rval |= get3dgin(ov, gi, gd, wp);
	po[0] = pi[0] + ov[0];
	po[1] = pi[1] + ov[1];
	po[2] = pi[2] + ov[2];
	return(rval);
}


static int
gridpoint(	/* compute grid position for ipt */
	GNDX	ndx,
	W3VEC	rem,
	W3VEC	ipt,
	struct grid3d	*gp
)
{
	int	rval = W3OK;
	int	i;

	for (i = 0; i < 3; i++) {
		rem[i] = (ipt[i] - gp->gmin[i])/gp->gstep[i];
		if (rem[i] < 0.) {
			ndx[i] = 0;
			rval = W3GAMUT;
		} else if ((int)rem[i] >= gp->gn[i]) {
			ndx[i] = gp->gn[i] - 1;
			rval = W3GAMUT;
		} else
			ndx[i] = (int)rem[i];
		rem[i] -= (double)ndx[i];
	}
	return(rval);
}


static int
get3dgpt(		/* get value for voxel */
	W3VEC	ov,
	GNDX	ndx,
	WARP3D	*wp
)
{
	W3VEC	gpt;
	LUENT	*le;
	KEYDP	*kd;
	int	rval = W3OK;
	int	i;

	le = lu_find(&wp->grid.gtab, ndx);
	if (le == NULL)
		return(W3ERROR);
	if (le->data == NULL) {
		if (le->key != NULL)
			kd = (KEYDP *)le->key;
		else if ((kd = (KEYDP *)malloc(sizeof(KEYDP))) == NULL)
			return(W3ERROR);
		for (i = 0; i < 3; i++) {
			kd->n[i] = ndx[i];
			gpt[i] = wp->grid.gmin[i] + ndx[i]*wp->grid.gstep[i];
			if (wp->grid.flags & W3FAST)	/* on centers */
				gpt[i] += .5*wp->grid.gstep[i];
		}
		rval = warp3dex(kd->v, gpt, wp);
		le->key = (char *)kd->n;
		le->data = (char *)kd->v;
	}
	W3VCPY(ov, (float *)le->data);
	return(rval);
}


static int
get3dgin(	/* interpolate from warp grid */
	W3VEC	ov,
	GNDX	ndx,
	W3VEC	rem,
	WARP3D	*wp
)
{
	W3VEC	cv[8];
	GNDX	gi;
	int	rval = W3OK;
	int	i;
					/* get corner values */
	for (i = 0; i < 8; i++) {
		gi[0] = ndx[0] + (i & 1);
		gi[1] = ndx[1] + (i>>1 & 1);
		gi[2] = ndx[2] + (i>>2);
		rval |= get3dgpt(cv[i], gi, wp);
	}
	if (rval & W3ERROR)
		return(rval);
	l3interp(ov, cv, rem, 3);	/* perform trilinear interpolation */
	return(rval);
}


static void
l3interp(		/* trilinear interpolation (recursive) */
	W3VEC	vo,
	W3VEC	*cl,
	W3VEC	dv,
	int	n
)
{
	W3VEC	v0, v1;
	int	i;

	if (--n) {
		l3interp(v0, cl, dv, n);
		l3interp(v1, cl+(1<<n), dv, n);
	} else {
		W3VCPY(v0, cl[0]);
		W3VCPY(v1, cl[1]);
	}
	for (i = 0; i < 3; i++)
		vo[i] = (1.-dv[n])*v0[i] + dv[n]*v1[i];
}


static int
warp3dex(		/* compute warp using 1/r^2 weighted avg. */
	W3VEC	ov,
	W3VEC	pi,
	WARP3D	*wp
)
{
	double	d2, w, wsum;
	W3VEC	vt;
	int	i;

	vt[0] = vt[1] = vt[2] = 0.;
	wsum = 0.;
	for (i = wp->npts; i--; ) {
		d2 = wpdist2(pi, wp->ip[i]);
		if (d2 <= MIND*MIND) w = 1./(MIND*MIND);
		else w = 1./d2;
		vt[0] += w*wp->ov[i][0];
		vt[1] += w*wp->ov[i][1];
		vt[2] += w*wp->ov[i][2];
		wsum += w;
	}
	if (wsum > 0.) {
		ov[0] = vt[0]/wsum;
		ov[1] = vt[1]/wsum;
		ov[2] = vt[2]/wsum;
	}
	return(W3OK);
}


WARP3D *
new3dw(			/* allocate and initialize WARP3D struct */
	int	flgs
)
{
	WARP3D  *wp;

	if ((flgs & (W3EXACT|W3FAST)) == (W3EXACT|W3FAST)) {
		eputs("new3dw: only one of W3EXACT or W3FAST\n");
		return(NULL);
	}
	if ((wp = (WARP3D *)malloc(sizeof(WARP3D))) == NULL) {
		eputs("new3dw: no memory\n");
		return(NULL);
	}
	wp->ip = wp->ov = NULL;
	wp->npts = 0;
	wp->grid.flags = flgs;
	wp->grid.gn[0] = wp->grid.gn[1] = wp->grid.gn[2] = 0;
	return(wp);
}


WARP3D *
load3dw(			/* load 3D warp from file */
	char	*fn,
	WARP3D	*wp
)
{
	FILE	*fp;
	W3VEC	inp, outp;

	if ((fp = fopen(fn, "r")) == NULL) {
		eputs(fn);
		eputs(": cannot open\n");
		return(NULL);
	}
	if (wp == NULL && (wp = new3dw(0)) == NULL)
		goto memerr;
	while (fgetvec(fp, inp) && fgetvec(fp, outp))
		if (!add3dpt(wp, inp, outp))
			goto memerr;
	if (!feof(fp)) {
		wputs(fn);
		wputs(": non-number in 3D warp file\n");
	}
	goto cleanup;
memerr:
	eputs("load3dw: out of memory\n");
cleanup:
	fclose(fp);
	return(wp);
}


extern int
set3dwfl(		/* reset warp flags */
	WARP3D	*wp,
	int	flgs
)
{
	if (flgs == wp->grid.flags)
		return(0);
	if ((flgs & (W3EXACT|W3FAST)) == (W3EXACT|W3FAST)) {
		eputs("set3dwfl: only one of W3EXACT or W3FAST\n");
		return(-1);
	}
	wp->grid.flags = flgs;
	done3dgrid(&wp->grid);		/* old grid is invalid */
	return(0);
}


int
add3dpt(		/* add 3D point pair to warp structure */
	WARP3D	*wp,
	W3VEC	pti,
	W3VEC	pto
)
{
	double	d2;
	W3VEC	*na;
	int	i;

	if (wp->npts == 0) {			/* initialize */
		wp->ip = (W3VEC *)malloc(AHUNK*sizeof(W3VEC));
		if (wp->ip == NULL) return(0);
		wp->ov = (W3VEC *)malloc(AHUNK*sizeof(W3VEC));
		if (wp->ov == NULL) return(0);
		wp->d2min = 1e10;
		wp->d2max = 0.;
		W3VCPY(wp->llim, pti);
		W3VCPY(wp->ulim, pti);
	} else {
		if (wp->npts % AHUNK == 0) {	/* allocate another hunk */
			na = (W3VEC *)realloc((void *)wp->ip,
					(wp->npts+AHUNK)*sizeof(W3VEC));
			if (na == NULL) return(0);
			wp->ip = na;
			na = (W3VEC *)realloc((void *)wp->ov,
					(wp->npts+AHUNK)*sizeof(W3VEC));
			if (na == NULL) return(0);
			wp->ov = na;
		}
		for (i = 0; i < 3; i++)		/* check boundaries */
			if (pti[i] < wp->llim[i])
				wp->llim[i] = pti[i];
			else if (pti[i] > wp->ulim[i])
				wp->ulim[i] = pti[i];
		for (i = wp->npts; i--; ) {	/* check distances */
			d2 = wpdist2(pti, wp->ip[i]);
			if (d2 < MIND*MIND)	/* value is too close */
				return(wp->npts);
			if (d2 < wp->d2min)
				wp->d2min = d2;
			if (d2 > wp->d2max)
				wp->d2max = d2;
		}
	}
	W3VCPY(wp->ip[wp->npts], pti);	/* add new point */
	wp->ov[wp->npts][0] = pto[0] - pti[0];
	wp->ov[wp->npts][1] = pto[1] - pti[1];
	wp->ov[wp->npts][2] = pto[2] - pti[2];
	done3dgrid(&wp->grid);		/* old grid is invalid */
	return(++wp->npts);
}


extern void
free3dw(			/* free WARP3D data */
	WARP3D	*wp
)
{
	done3dgrid(&wp->grid);
	free(wp->ip);
	free(wp->ov);
	free(wp);
}


static unsigned long
gridhash(			/* hash a grid point index */
	const char	*gp
)
{
	return(((unsigned long)((const unsigned char*)gp)[0]<<GNBITS | ((const unsigned char*)gp)[1])<<GNBITS | ((const unsigned char*)gp)[2]);
}


static int
new3dgrid(			/* initialize interpolating grid for warp */
	WARP3D	*wp
)
{
	W3VEC	gmax;
	double	gridstep, d;
	int	n;
	int	i;
				/* free old grid (if any) */
	done3dgrid(&wp->grid);
				/* check parameters */
	if (wp->npts < 2)
		return(W3BADMAP);	/* undefined for less than 2 points */
	if (wp->d2max < MIND)
		return(W3BADMAP);	/* not enough disparity */
				/* compute gamut */
	W3VCPY(wp->grid.gmin, wp->llim);
	W3VCPY(gmax, wp->ulim);
	gridstep = sqrt(wp->d2min);
	for (i = 0; i < 3; i++) {
		wp->grid.gmin[i] -= .501*gridstep;
		gmax[i] += .501*gridstep;
	}
	if (wp->grid.flags & W3EXACT) {
		wp->grid.gn[0] = wp->grid.gn[1] = wp->grid.gn[2] = 1;
		wp->grid.gstep[0] = gmax[0] - wp->grid.gmin[0];
		wp->grid.gstep[1] = gmax[1] - wp->grid.gmin[1];
		wp->grid.gstep[2] = gmax[2] - wp->grid.gmin[2];
		return(W3OK);		/* no interpolation, so no grid */
	}
				/* create grid */
	for (i = 0; i < 3; i++) {
		d = gmax[i] - wp->grid.gmin[i];
		n = d/gridstep + .5;
		if (n >= MAXGN-1)
			n = MAXGN-2;
		wp->grid.gstep[i] = d / n;
		wp->grid.gn[i] = n;
	}
				/* initialize lookup table */
	wp->grid.gtab.hashf = gridhash;
	wp->grid.gtab.keycmp = NULL;
	wp->grid.gtab.freek = free;
	wp->grid.gtab.freed = NULL;
	return(lu_init(&wp->grid.gtab, 1024) ? W3OK : W3ERROR);
}


static void
done3dgrid(			/* free interpolating grid for warp */
	struct grid3d	*gp
)
{
	if (gp->gn[0] == 0)
		return;
	lu_done(&gp->gtab);
	gp->gn[0] = gp->gn[1] = gp->gn[2] = 0;
}
