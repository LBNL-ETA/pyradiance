#ifndef lint
static const char RCSid[] = "$Id: bsdf2ttree.c,v 2.64 2025/06/07 05:09:45 greg Exp $";
#endif
/*
 * Load measured BSDF interpolant and write out as XML file with tensor tree.
 *
 *	G. Ward
 */

#define _USE_MATH_DEFINES
#include <stdlib.h>
#include <math.h>
#include <ctype.h>
#include "random.h"
#include "rtio.h"
#include "calcomp.h"
#include "bsdfrep.h"
				/* reciprocity averaging option */
static const char	*recip = "";
				/* percentage to cull (<0 to turn off) */
static double		pctcull = 90.;
				/* sampling order */
static int		samp_order = 6;
				/* super-sampling threshold */
static double		ssamp_thresh = 0.35;
				/* number of super-samples */
static int		nssamp = 64;
				/* limit on number of RBF lobes */
static int		lobe_lim = 15000;
				/* progress bar length */
static int		do_prog = 79;

#define MAXCARG		512	/* wrapBSDF command */
static char		*wrapBSDF[MAXCARG] = {"wrapBSDF", "-U"};
static int		wbsdfac = 2;

/* Add argument to wrapBSDF, allocating space if !isstatic */
static void
add_wbsdf(const char *arg, int isstatic)
{
	if (arg == NULL)
		return;
	if (wbsdfac >= MAXCARG-1) {
		fputs(progname, stderr);
		fputs(": too many command arguments to wrapBSDF\n", stderr);
		exit(1);
	}
	if (!*arg)
		arg = "";
	else if (!isstatic)
		arg = savqstr((char *)arg);

	wrapBSDF[wbsdfac++] = (char *)arg;
}

/* Create Yuv component file and add appropriate arguments */
static char *
create_component_file(int c)
{
	static const char	sname[3][6] = {"CIE-Y", "CIE-u", "CIE-v"};
	static const char	cname[4][4] = {"-rf", "-tf", "-tb", "-rb"};
	char			*tfname = mktemp(savqstr(TEMPLATE));

	add_wbsdf("-s", 1); add_wbsdf(sname[c], 1);
	add_wbsdf(cname[(input_orient>0)<<1 | (output_orient>0)], 1);
	add_wbsdf(tfname, 1);
	return(tfname);
}

/* Start new progress bar */
#define prog_start(s)	if (do_prog) fprintf(stderr, "%s: %s...\n", progname, s); else

/* Draw progress bar of the appropriate length */
static void
prog_show(double frac)
{
	static unsigned	call_cnt = 0;
	static char	lastc[] = "-\\|/";
	char		pbar[256];
	int		nchars;

	if (do_prog <= 1) return;
	if (do_prog > sizeof(pbar)-2)
		do_prog = sizeof(pbar)-2;
	if (frac < 0) frac = 0;
	else if (frac >= 1) frac = .9999;
	nchars = do_prog*frac;
	pbar[0] = '\r';
	memset(pbar+1, '*', nchars);
	pbar[nchars+1] = lastc[call_cnt++ & 3];
	memset(pbar+2+nchars, '-', do_prog-nchars-1);
	pbar[do_prog+1] = '\0';
	fputs(pbar, stderr);
}

/* Finish progress bar */
static void
prog_done(void)
{
	int	n = do_prog;

	if (n <= 1) return;
	fputc('\r', stderr);
	while (n--)
		fputc(' ', stderr);
	fputc('\r', stderr);
}

/* Compute absolute relative difference */
static double
abs_diff(double v1, double v0)
{
	if ((v0 < 0) | (v1 < 0))
		return(.0);
	v1 = (v1-v0)*2./(v0+v1+.0001);
	if (v1 < 0)
		return(-v1);
	return(v1);
}

/* Interpolate and output isotropic BSDF data */
static void
eval_isotropic(char *funame)
{
	const int	sqres = 1<<samp_order;
	const double	sqfact = 1./(double)sqres;
	float		*val_last = NULL;
	float		*val_next = NULL;
	SDValue		*sdv_next = NULL;
	FILE		*ofp, *uvfp[2];
	int		assignD = 0;
	char		cmd[128];
	int		ix, ox, oy;
	RREAL		iovec[6];
	float		bsdf, uv[2];

	if (pctcull >= 0) {
		sprintf(cmd, "rttree_reduce%s -h -ff -r 3 -t %f -g %d > %s",
				recip, pctcull, samp_order, create_component_file(0));
		ofp = popen(cmd, "w");
		if (ofp == NULL) {
			fprintf(stderr, "%s: cannot create pipe to rttree_reduce\n",
					progname);
			exit(1);
		}
		SET_FILE_BINARY(ofp);
#ifdef getc_unlocked				/* avoid lock/unlock overhead */
		flockfile(ofp);
#endif
		if (rbf_colorimetry == RBCtristimulus) {
			double	uvcull = 100. - (100.-pctcull)*.25;
			sprintf(cmd, "rttree_reduce%s -h -ff -r 3 -t %f -g %d > %s",
					recip, uvcull, samp_order, create_component_file(1));
			uvfp[0] = popen(cmd, "w");
			sprintf(cmd, "rttree_reduce%s -h -ff -r 3 -t %f -g %d > %s",
					recip, uvcull, samp_order, create_component_file(2));
			uvfp[1] = popen(cmd, "w");
			if ((uvfp[0] == NULL) | (uvfp[1] == NULL)) {
				fprintf(stderr, "%s: cannot open pipes to uv output\n",
						progname);
				exit(1);
			}
			SET_FILE_BINARY(uvfp[0]); SET_FILE_BINARY(uvfp[1]);
#ifdef getc_unlocked
			flockfile(uvfp[0]); flockfile(uvfp[1]);
#endif
		}
	} else {
		ofp = fopen(create_component_file(0), "w");
		if (ofp == NULL) {
			fprintf(stderr, "%s: cannot create Y output file\n",
					progname);
			exit(1);
		}
		fputs("{\n", ofp);
		if (rbf_colorimetry == RBCtristimulus) {
			uvfp[0] = fopen(create_component_file(1), "w");
			uvfp[1] = fopen(create_component_file(2), "w");
			if ((uvfp[0] == NULL) | (uvfp[1] == NULL)) {
				fprintf(stderr, "%s: cannot create uv output file(s)\n",
						progname);
				exit(1);
			}
			fputs("{\n", uvfp[0]);
			fputs("{\n", uvfp[1]);
		}
	}
	if (funame != NULL)			/* need to assign Dx, Dy, Dz? */
		assignD = (fundefined(funame) < 6);
	val_last = (float *)calloc(sqres, sizeof(float));
	if (funame == NULL)
		sdv_next = (SDValue *)malloc(sizeof(SDValue)*sqres);
	else
		val_next = (float *)malloc(sizeof(float)*sqres);
						/* run through directions */
	for (ix = 0; ix < sqres/2; ix++) {
		const int	zipsgn = (ix & 1)*2 - 1;
		RBFNODE		*rbf = NULL;
		iovec[0] = 2.*sqfact*(ix+.5) - 1.;
		iovec[1] = zipsgn*sqfact*.5;
		iovec[2] = input_orient * sqrt(1. - iovec[0]*iovec[0]
						- iovec[1]*iovec[1]);
		if (funame == NULL)
			rbf = advect_rbf(iovec, lobe_lim);
						/* presample first row */
		for (oy = 0; oy < sqres; oy++) {
		    square2disk(iovec+3, .5*sqfact, (oy+.5)*sqfact);
		    iovec[5] = output_orient *
				sqrt(1. - iovec[3]*iovec[3] - iovec[4]*iovec[4]);
		    if (funame == NULL) {
			eval_rbfcol(&sdv_next[oy], rbf, iovec+3);
		    } else {
			if (assignD) {
			    varset("Dx", '=', -iovec[3]);
			    varset("Dy", '=', -iovec[4]);
			    varset("Dz", '=', -iovec[5]);
			    ++eclock;
			}
			val_next[oy] = funvalue(funame, 6, iovec);
		    }
		}
		for (ox = 0; ox < sqres; ox++) {
		    /*
		     * Super-sample when we detect a difference from before
		     * or after in this row, above or below.
		     */
		    for (oy = 0; oy < sqres; oy++) {
			if (ox < sqres-1) {	/* keeping one row ahead... */
			    square2disk(iovec+3, (ox+1.5)*sqfact, (oy+.5)*sqfact);
			    iovec[5] = output_orient *
				sqrt(1. - iovec[3]*iovec[3] - iovec[4]*iovec[4]);
			}
			if (funame == NULL) {
			    SDValue	sdv = sdv_next[oy];
			    bsdf = sdv.cieY;
			    if (ox < sqres-1)
				eval_rbfcol(&sdv_next[oy], rbf, iovec+3);
			    if (abs_diff(bsdf, sdv_next[oy].cieY) > ssamp_thresh ||
				(ox && abs_diff(bsdf, val_last[oy]) > ssamp_thresh) ||
				(oy && abs_diff(bsdf, val_last[oy-1]) > ssamp_thresh) ||
				(oy < sqres-1 &&
				    abs_diff(bsdf, sdv_next[oy+1].cieY) > ssamp_thresh)) {
				int	ssi;
				double	ssa[2], sum = 0, usum = 0, vsum = 0;
						/* super-sample voxel */
				for (ssi = nssamp; ssi--; ) {
				    SDmultiSamp(ssa, 2, (ssi+frandom()) /
							(double)nssamp);
				    square2disk(iovec+3, (ox+ssa[0])*sqfact,
							(oy+ssa[1])*sqfact);
				    iovec[5] = output_orient *
					sqrt(1. - iovec[3]*iovec[3] - iovec[4]*iovec[4]);
				    eval_rbfcol(&sdv, rbf, iovec+3);
				    sum += sdv.cieY;
				    if (rbf_colorimetry == RBCtristimulus) {
					sdv.cieY /=
					    -2.*sdv.spec.cx + 12.*sdv.spec.cy + 3.;
					usum += 4.*sdv.spec.cx * sdv.cieY;
					vsum += 9.*sdv.spec.cy * sdv.cieY;
				    }
				}
				bsdf = sum / (double)nssamp;
				if (rbf_colorimetry == RBCtristimulus) {
				    uv[0] = usum / (sum+FTINY);
				    uv[1] = vsum / (sum+FTINY);
				}
			    } else if (rbf_colorimetry == RBCtristimulus) {
				uv[0] = uv[1] = 1. /
				    (-2.*sdv.spec.cx + 12.*sdv.spec.cy + 3.);
				uv[0] *= 4.*sdv.spec.cx;
				uv[1] *= 9.*sdv.spec.cy;
			    }
			} else {
			    bsdf = val_next[oy];
			    if (ox < sqres-1) {
				if (assignD) {
				    varset("Dx", '=', -iovec[3]);
				    varset("Dy", '=', -iovec[4]);
				    varset("Dz", '=', -iovec[5]);
				    ++eclock;
				}
				val_next[oy] = funvalue(funame, 6, iovec);
			    }
			    if (abs_diff(bsdf, val_next[oy]) > ssamp_thresh ||
				(ox && abs_diff(bsdf, val_last[oy]) > ssamp_thresh) ||
				(oy && abs_diff(bsdf, val_last[oy-1]) > ssamp_thresh) ||
				(oy < sqres-1 &&
				    abs_diff(bsdf, val_next[oy+1]) > ssamp_thresh)) {
				int	ssi;
				double	ssa[4], ssvec[6], sum = 0;
						/* super-sample voxel */
				for (ssi = nssamp; ssi--; ) {
				    SDmultiSamp(ssa, 4, (ssi+frandom()) /
							(double)nssamp);
				    ssvec[0] = 2.*sqfact*(ix+ssa[0]) - 1.;
				    ssvec[1] = zipsgn*sqfact*ssa[1];
				    ssvec[2] = 1. - ssvec[0]*ssvec[0]
							- ssvec[1]*ssvec[1];
				    if (ssvec[2] < .0) {
					ssvec[1] = 0;
					ssvec[2] = 1. - ssvec[0]*ssvec[0];
				    }
				    ssvec[2] = input_orient * sqrt(ssvec[2]);
				    square2disk(ssvec+3, (ox+ssa[2])*sqfact,
						(oy+ssa[3])*sqfact);
				    ssvec[5] = output_orient *
						sqrt(1. - ssvec[3]*ssvec[3] -
							ssvec[4]*ssvec[4]);
				    if (assignD) {
					varset("Dx", '=', -ssvec[3]);
					varset("Dy", '=', -ssvec[4]);
					varset("Dz", '=', -ssvec[5]);
					++eclock;
				    }
				    sum += funvalue(funame, 6, ssvec);
				}
				bsdf = sum / (double)nssamp;
			    }
			}
			if (pctcull >= 0)
				putbinary(&bsdf, sizeof(bsdf), 1, ofp);
			else
				fprintf(ofp, "\t%.3e\n", bsdf);

			if (rbf_colorimetry == RBCtristimulus) {
				if (pctcull >= 0) {
					putbinary(&uv[0], sizeof(*uv), 1, uvfp[0]);
					putbinary(&uv[1], sizeof(*uv), 1, uvfp[1]);
				} else {
					fprintf(uvfp[0], "\t%.3e\n", uv[0]);
					fprintf(uvfp[1], "\t%.3e\n", uv[1]);
				}
			}
			if (val_last != NULL)
				val_last[oy] = bsdf;
		    }
		}
		if (rbf != NULL)
			free(rbf);
		prog_show((ix+1.)*(2.*sqfact));
	}
	prog_done();
	if (val_last != NULL) {
		free(val_last);
		if (val_next != NULL) free(val_next);
		if (sdv_next != NULL) free(sdv_next);
	}
	if (pctcull >= 0) {			/* finish output */
		if (pclose(ofp)) {
			fprintf(stderr, "%s: error running rttree_reduce on Y\n",
					progname);
			exit(1);
		}
		if (rbf_colorimetry == RBCtristimulus &&
				(pclose(uvfp[0]) || pclose(uvfp[1]))) {
			fprintf(stderr, "%s: error running rttree_reduce on uv\n",
					progname);
			exit(1);
		}
	} else {
		for (ix = sqres*sqres*sqres/2; ix--; )
			fputs("\t0\n", ofp);
		fputs("}\n", ofp);
		if (fclose(ofp)) {
			fprintf(stderr, "%s: error writing Y file\n",
					progname);
			exit(1);
		}
		if (rbf_colorimetry == RBCtristimulus) {
			for (ix = sqres*sqres*sqres/2; ix--; ) {
				fputs("\t0\n", uvfp[0]);
				fputs("\t0\n", uvfp[1]);
			}
			fputs("}\n", uvfp[0]);
			fputs("}\n", uvfp[1]);
			if (fclose(uvfp[0]) || fclose(uvfp[1])) {
				fprintf(stderr, "%s: error writing uv file(s)\n",
						progname);
				exit(1);
			}
		}
	}
}

/* Interpolate and output anisotropic BSDF data */
static void
eval_anisotropic(char *funame)
{
	const int	sqres = 1<<samp_order;
	const double	sqfact = 1./(double)sqres;
	float		*val_last = NULL;
	float		*val_next = NULL;
	SDValue		*sdv_next = NULL;
	FILE		*ofp, *uvfp[2];
	int		assignD = 0;
	char		cmd[128];
	int		ix, iy, ox, oy;
	RREAL		iovec[6];
	float		bsdf, uv[2];

	if (pctcull >= 0) {
		const char	*avgopt = (input_orient>0 ^ output_orient>0)
						? "" : recip;
		sprintf(cmd, "rttree_reduce%s -h -ff -r 4 -t %f -g %d > %s",
				avgopt, pctcull, samp_order,
				create_component_file(0));
		ofp = popen(cmd, "w");
		if (ofp == NULL) {
			fprintf(stderr, "%s: cannot create pipe to rttree_reduce\n",
					progname);
			exit(1);
		}
		SET_FILE_BINARY(ofp);
#ifdef getc_unlocked				/* avoid lock/unlock overhead */
		flockfile(ofp);
#endif
		if (rbf_colorimetry == RBCtristimulus) {
			double	uvcull = 100. - (100.-pctcull)*.25;
			sprintf(cmd, "rttree_reduce%s -h -ff -r 4 -t %f -g %d > %s",
					avgopt, uvcull, samp_order,
					create_component_file(1));
			uvfp[0] = popen(cmd, "w");
			sprintf(cmd, "rttree_reduce%s -h -ff -r 4 -t %f -g %d > %s",
					avgopt, uvcull, samp_order,
					create_component_file(2));
			uvfp[1] = popen(cmd, "w");
			if ((uvfp[0] == NULL) | (uvfp[1] == NULL)) {
				fprintf(stderr, "%s: cannot open pipes to uv output\n",
						progname);
				exit(1);
			}
			SET_FILE_BINARY(uvfp[0]); SET_FILE_BINARY(uvfp[1]);
#ifdef getc_unlocked
			flockfile(uvfp[0]); flockfile(uvfp[1]);
#endif
		}
	} else {
		ofp = fopen(create_component_file(0), "w");
		if (ofp == NULL) {
			fprintf(stderr, "%s: cannot create Y output file\n",
					progname);
			exit(1);
		}
		fputs("{\n", ofp);
		if (rbf_colorimetry == RBCtristimulus) {
			uvfp[0] = fopen(create_component_file(1), "w");
			uvfp[1] = fopen(create_component_file(2), "w");
			if ((uvfp[0] == NULL) | (uvfp[1] == NULL)) {
				fprintf(stderr, "%s: cannot create uv output file(s)\n",
						progname);
				exit(1);
			}
			fputs("{\n", uvfp[0]);
			fputs("{\n", uvfp[1]);
		}
	}
	if (funame != NULL)			/* need to assign Dx, Dy, Dz? */
		assignD = (fundefined(funame) < 6);
	val_last = (float *)calloc(sqres, sizeof(float));
	if (funame == NULL)
		sdv_next = (SDValue *)malloc(sizeof(SDValue)*sqres);
	else
		val_next = (float *)malloc(sizeof(float)*sqres);
						/* run through directions */
	for (ix = 0; ix < sqres; ix++)
	    for (iy = 0; iy < sqres; iy++) {
		RBFNODE	*rbf = NULL;		/* Klems reversal */
		square2disk(iovec, 1.-(ix+.5)*sqfact, 1.-(iy+.5)*sqfact);
		iovec[2] = input_orient *
				sqrt(1. - iovec[0]*iovec[0] - iovec[1]*iovec[1]);
		if (funame == NULL)
			rbf = advect_rbf(iovec, lobe_lim);
						/* presample first row */
		for (oy = 0; oy < sqres; oy++) {
		    square2disk(iovec+3, .5*sqfact, (oy+.5)*sqfact);
		    iovec[5] = output_orient *
				sqrt(1. - iovec[3]*iovec[3] - iovec[4]*iovec[4]);
		    if (funame == NULL) {
			eval_rbfcol(&sdv_next[oy], rbf, iovec+3);
		    } else {
			if (assignD) {
			    varset("Dx", '=', -iovec[3]);
			    varset("Dy", '=', -iovec[4]);
			    varset("Dz", '=', -iovec[5]);
			    ++eclock;
			}
			val_next[oy] = funvalue(funame, 6, iovec);
		    }
		}
		for (ox = 0; ox < sqres; ox++) {
		    /*
		     * Super-sample when we detect a difference from before
		     * or after in this row, above or below.
		     */
		    for (oy = 0; oy < sqres; oy++) {
			if (ox < sqres-1) {	/* keeping one row ahead... */
			    square2disk(iovec+3, (ox+1.5)*sqfact, (oy+.5)*sqfact);
			    iovec[5] = output_orient *
				sqrt(1. - iovec[3]*iovec[3] - iovec[4]*iovec[4]);
			}
			if (funame == NULL) {
			    SDValue	sdv = sdv_next[oy];
			    bsdf = sdv.cieY;
			    if (ox < sqres-1)
				eval_rbfcol(&sdv_next[oy], rbf, iovec+3);
			    if (abs_diff(bsdf, sdv_next[oy].cieY) > ssamp_thresh ||
				(ox && abs_diff(bsdf, val_last[oy]) > ssamp_thresh) ||
				(oy && abs_diff(bsdf, val_last[oy-1]) > ssamp_thresh) ||
				(oy < sqres-1 &&
				    abs_diff(bsdf, sdv_next[oy+1].cieY) > ssamp_thresh)) {
				int	ssi;
				double	ssa[2], sum = 0, usum = 0, vsum = 0;
						/* super-sample voxel */
				for (ssi = nssamp; ssi--; ) {
				    SDmultiSamp(ssa, 2, (ssi+frandom()) /
							(double)nssamp);
				    square2disk(iovec+3, (ox+ssa[0])*sqfact,
							(oy+ssa[1])*sqfact);
				    iovec[5] = output_orient *
					sqrt(1. - iovec[3]*iovec[3] - iovec[4]*iovec[4]);
				    eval_rbfcol(&sdv, rbf, iovec+3);
				    sum += sdv.cieY;
				    if (rbf_colorimetry == RBCtristimulus) {
					sdv.cieY /=
					    -2.*sdv.spec.cx + 12.*sdv.spec.cy + 3.;
					usum += 4.*sdv.spec.cx * sdv.cieY;
					vsum += 9.*sdv.spec.cy * sdv.cieY;
				    }
				}
				bsdf = sum / (double)nssamp;
				if (rbf_colorimetry == RBCtristimulus) {
				    uv[0] = usum / (sum+FTINY);
				    uv[1] = vsum / (sum+FTINY);
				}
			    } else if (rbf_colorimetry == RBCtristimulus) {
				uv[0] = uv[1] = 1. /
				    (-2.*sdv.spec.cx + 12.*sdv.spec.cy + 3.);
				uv[0] *= 4.*sdv.spec.cx;
				uv[1] *= 9.*sdv.spec.cy;
			    }
			} else {
			    bsdf = val_next[oy];
			    if (ox < sqres-1) {
				if (assignD) {
				    varset("Dx", '=', -iovec[3]);
				    varset("Dy", '=', -iovec[4]);
				    varset("Dz", '=', -iovec[5]);
				    ++eclock;
				}
				val_next[oy] = funvalue(funame, 6, iovec);
			    }
			    if (abs_diff(bsdf, val_next[oy]) > ssamp_thresh ||
				(ox && abs_diff(bsdf, val_last[oy]) > ssamp_thresh) ||
				(oy && abs_diff(bsdf, val_last[oy-1]) > ssamp_thresh) ||
				(oy < sqres-1 &&
				    abs_diff(bsdf, val_next[oy+1]) > ssamp_thresh)) {
				int	ssi;
				double	ssa[4], ssvec[6], sum = 0;
						/* super-sample voxel */
				for (ssi = nssamp; ssi--; ) {
				    SDmultiSamp(ssa, 4, (ssi+frandom()) /
							(double)nssamp);
				    square2disk(ssvec, 1.-(ix+ssa[0])*sqfact,
						1.-(iy+ssa[1])*sqfact);
				    ssvec[2] = input_orient *
						sqrt(1. - ssvec[0]*ssvec[0] -
							ssvec[1]*ssvec[1]);
				    square2disk(ssvec+3, (ox+ssa[2])*sqfact,
						(oy+ssa[3])*sqfact);
				    ssvec[5] = output_orient *
						sqrt(1. - ssvec[3]*ssvec[3] -
							ssvec[4]*ssvec[4]);
				    if (assignD) {
					varset("Dx", '=', -ssvec[3]);
					varset("Dy", '=', -ssvec[4]);
					varset("Dz", '=', -ssvec[5]);
					++eclock;
				    }
				    sum += funvalue(funame, 6, ssvec);
				}
				bsdf = sum / (double)nssamp;
			    }
			}
			if (pctcull >= 0)
				putbinary(&bsdf, sizeof(bsdf), 1, ofp);
			else
				fprintf(ofp, "\t%.3e\n", bsdf);

			if (rbf_colorimetry == RBCtristimulus) {
				if (pctcull >= 0) {
					putbinary(&uv[0], sizeof(*uv), 1, uvfp[0]);
					putbinary(&uv[1], sizeof(*uv), 1, uvfp[1]);
				} else {
					fprintf(uvfp[0], "\t%.3e\n", uv[0]);
					fprintf(uvfp[1], "\t%.3e\n", uv[1]);
				}
			}
			if (val_last != NULL)
				val_last[oy] = bsdf;
		    }
		}
		if (rbf != NULL)
			free(rbf);
		prog_show((ix*sqres+iy+1.)/(sqres*sqres));
	    }
	prog_done();
	if (val_last != NULL) {
		free(val_last);
		if (val_next != NULL) free(val_next);
		if (sdv_next != NULL) free(sdv_next);
	}
	if (pctcull >= 0) {			/* finish output */
		if (pclose(ofp)) {
			fprintf(stderr, "%s: error running rttree_reduce on Y\n",
					progname);
			exit(1);
		}
		if (rbf_colorimetry == RBCtristimulus &&
				(pclose(uvfp[0]) || pclose(uvfp[1]))) {
			fprintf(stderr, "%s: error running rttree_reduce on uv\n",
					progname);
			exit(1);
		}
	} else {
		fputs("}\n", ofp);
		if (fclose(ofp)) {
			fprintf(stderr, "%s: error writing Y file\n",
					progname);
			exit(1);
		}
		if (rbf_colorimetry == RBCtristimulus) {
			fputs("}\n", uvfp[0]);
			fputs("}\n", uvfp[1]);
			if (fclose(uvfp[0]) || fclose(uvfp[1])) {
				fprintf(stderr, "%s: error writing uv file(s)\n",
						progname);
				exit(1);
			}
		}
	}
}

#if defined(_WIN32) || defined(_WIN64)
/* Execute wrapBSDF command (may never return) */
static int
wrap_up(void)
{
	char	cmd[32700];

	if (bsdf_manuf[0]) {
		add_wbsdf("-f", 1);
		strcpy(cmd, "m=");
		strcpy(cmd+2, bsdf_manuf);
		add_wbsdf(cmd, 0);
	}
	if (bsdf_name[0]) {
		add_wbsdf("-f", 1);
		strcpy(cmd, "n=");
		strcpy(cmd+2, bsdf_name);
		add_wbsdf(cmd, 0);
	}
	if (!convert_commandline(cmd, sizeof(cmd), wrapBSDF)) {
		fputs(progname, stderr);
		fputs(": command line too long in wrap_up()\n", stderr);
		return(1);
	}
	return(system(cmd));
}
#else
/* Execute wrapBSDF command (may never return) */
static int
wrap_up(void)
{
	char	buf[256];
	char	*compath = getpath((char *)wrapBSDF[0], getenv("PATH"), X_OK);

	if (compath == NULL) {
		fprintf(stderr, "%s: cannot locate %s\n", progname, wrapBSDF[0]);
		return(1);
	}
	if (bsdf_manuf[0]) {
		add_wbsdf("-f", 1);
		strcpy(buf, "m=");
		strcpy(buf+2, bsdf_manuf);
		add_wbsdf(buf, 0);
	}
	if (bsdf_name[0]) {
		add_wbsdf("-f", 1);
		strcpy(buf, "n=");
		strcpy(buf+2, bsdf_name);
		add_wbsdf(buf, 0);
	}
	execv(compath, wrapBSDF);	/* successful call never returns */
	perror(compath);
	return(1);
}
#endif

#define	HEAD_BUFLEN	10240
static char	head_buf[HEAD_BUFLEN];
static int	cur_headlen = 0;

/* Record header line as comment associated with this SIR input */
static int
record2header(char *s)
{
	int	len = strlen(s);

	if (cur_headlen+len >= HEAD_BUFLEN-6)
		return(0);
					/* includes EOL */
	strcpy(head_buf+cur_headlen, s);
	cur_headlen += len;

#if defined(_WIN32) || defined(_WIN64)
	if (head_buf[cur_headlen-1] == '\n')
		head_buf[cur_headlen-1] = '\t';
#endif
	return(1);
}

/* Finish off header for this file */
static void
done_header(void)
{
	while (cur_headlen > 0 && isspace(head_buf[cur_headlen-1]))
		--cur_headlen;
	head_buf[cur_headlen] = '\0';
	if (!cur_headlen)
		return;
	add_wbsdf("-C", 1);
	add_wbsdf(head_buf, 0);
	head_buf[cur_headlen=0] = '\0';
}

/* Read in BSDF and interpolate as tensor tree representation */
int
main(int argc, char *argv[])
{
	static const char	tfmt[2][4] = {"t4", "t3"};
	int			dofwd = 0, dobwd = 1;
	int			nsirs = 0;
	char			buf[1024];
	int			i;
						/* set global progname */
	fixargv0(argv[0]);
	esupport |= E_VARIABLE|E_FUNCTION|E_RCONST;
	esupport &= ~(E_INCHAN|E_OUTCHAN);
	scompile("PI:3.14159265358979323846", NULL, 0);
	biggerlib();
	strcpy(buf, "File produced by: ");
	if (convert_commandline(buf+18, sizeof(buf)-18, argv) != NULL) {
		add_wbsdf("-C", 1); add_wbsdf(buf, 0);
	}
	for (i = 1; i < argc; i++)
	    if ((argv[i][0] == '-') | (argv[i][0] == '+')) {
		switch (argv[i][1]) {		/* get option */
		case 'e':
			scompile(argv[++i], NULL, 0);
			if (single_plane_incident < 0)
				single_plane_incident = 0;
			break;
		case 'f':
			if ((argv[i][0] == '-') & !argv[i][2]) {
				if (strchr(argv[++i], '=') != NULL) {
					add_wbsdf("-f", 1);
					add_wbsdf(argv[i], 1);
				} else {
					char	*fpath = getpath(argv[i],
							    getrlibpath(), 0);
					if (fpath == NULL) {
						fprintf(stderr,
						"%s: cannot find file '%s'\n",
							argv[0], argv[i]);
						return(1);
					}
					fcompile(fpath);
					if (single_plane_incident < 0)
						single_plane_incident = 0;
				}
			} else
				dofwd = (argv[i][0] == '+');
			break;
		case 'a':
			recip = (argv[i][0] == '+') ? " -a" : "";
			break;
		case 'b':
			dobwd = (argv[i][0] == '+');
			break;
		case 'n':
			nssamp = atoi(argv[++i]);
			if (nssamp <= 0)
				goto userr;
			break;
		case 's':
			ssamp_thresh = atof(argv[++i]);
			if (ssamp_thresh <= FTINY)
				goto userr;
			break;
		case 't':
			switch (argv[i][2]) {
			case '3':
				single_plane_incident = 1;
				break;
			case '4':
				single_plane_incident = 0;
				break;
			case '\0':
				pctcull = atof(argv[++i]);
				break;
			default:
				goto userr;
			}
			break;
		case 'g':
			samp_order = atoi(argv[++i]);
			break;
		case 'l':
			lobe_lim = atoi(argv[++i]);
			break;
		case 'p':
			do_prog = atoi(argv[i]+2);
			break;
		case 'W':
			add_wbsdf(argv[i], 1);
			break;
		case 'u':
		case 'C':
			add_wbsdf(argv[i], 1);
			add_wbsdf(argv[++i], 1);
			break;
		default:
			goto userr;
		}
	    } else {				/* input SIR or function */
		FILE	*fpin;
		if (!nsirs & (single_plane_incident >= 0))
			break;			/* must be a function */
		if (nsirs >= 4) {
			fprintf(stderr, "At most 4 SIR inputs supported\n");
			goto userr;
		}
		fpin = fopen(argv[i], "rb");	/* open SIR file */
		if (fpin == NULL) {
			fprintf(stderr, "%s: cannot open BSDF interpolant '%s'\n",
					progname, argv[i]);
			return(1);
		}
		sprintf(buf, "%s:\n", argv[i]);
		record2header(buf);
		sir_headshare = &record2header;
		if (!load_bsdf_rep(fpin))
			return(1);
		fclose(fpin);
		done_header();
		sprintf(buf, "Interpolating component '%s'", argv[i]);
		prog_start(buf);
		if (!nsirs++) {
			add_wbsdf("-a", 1);
			add_wbsdf(tfmt[single_plane_incident], 1);
		}
		if (single_plane_incident)
			eval_isotropic(NULL);
		else
			eval_anisotropic(NULL);
	    }
	if (i < argc) {				/* function-based BSDF? */
		void	(*evf)(char *s) = single_plane_incident ?
				eval_isotropic : eval_anisotropic;
		if (i != argc-1 || fundefined(argv[i]) < 3) {
			fprintf(stderr,
	"%s: need single function with 6 arguments: bsdf(ix,iy,iz,ox,oy,oz)\n",
					progname);
			fprintf(stderr, "\tor 3 arguments using Dx,Dy,Dz: bsdf(ix,iy,iz)\n");
			goto userr;
		}
		doptimize(1);			/* optimize definitions */
		++eclock;
		add_wbsdf("-a", 1);
		add_wbsdf(tfmt[single_plane_incident], 1);
		if (dofwd) {
			input_orient = -1;
			output_orient = -1;
			prog_start("Evaluating outside reflectance");
			(*evf)(argv[i]);
			output_orient = 1;
			prog_start("Evaluating outside->inside transmission");
			(*evf)(argv[i]);
		}
		if (dobwd) {
			input_orient = 1;
			output_orient = 1;
			prog_start("Evaluating inside reflectance");
			(*evf)(argv[i]);
			output_orient = -1;
			prog_start("Evaluating inside->outside transmission");
			(*evf)(argv[i]);
		}
	} else if (!nsirs) {			/* else load SIR from stdin? */
		record2header("<stdin>:\n");
		sir_headshare = &record2header;
		if (!load_bsdf_rep(stdin))
			return(1);
		done_header();
		prog_start("Interpolating from standard input");
		add_wbsdf("-a", 1);
		add_wbsdf(tfmt[single_plane_incident], 1);
		if (single_plane_incident)	/* resample dist. */
			eval_isotropic(NULL);
		else
			eval_anisotropic(NULL);
	}
	return(wrap_up());			/* call wrapBSDF */
userr:
	fprintf(stderr,
	"Usage: %s [{+|-}a][-g Nlog2][-t pctcull][-n nss][-s thresh][-l maxlobes][bsdf.sir ..] > bsdf.xml\n",
				progname);
	fprintf(stderr,
	"   or: %s -t{3|4} [{+|-}a][-g Nlog2][-t pctcull][-n nss][-s thresh][{+|-}for[ward]][{+|-}b[ackward]][-e expr][-f file] bsdf_func > bsdf.xml\n",
				progname);
	return(1);
}
