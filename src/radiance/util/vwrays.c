#ifndef lint
static const char	RCSid[] = "$Id: vwrays.c,v 3.26 2025/06/03 21:31:51 greg Exp $";
#endif
/*
 * Compute rays corresponding to a given picture or view.
 */

#include "platform.h"
#include "standard.h"
#include "random.h"
#include "view.h"

typedef void putfunc(FVECT ro, FVECT rd);
static putfunc puta;
static putfunc putf;
static putfunc putd;
static void pix2rays(FILE *fp);
static void putrays(void);

static putfunc *putr = puta;

VIEW	vw = STDVIEW;

RESOLU	rs = {PIXSTANDARD, 512, 512};

double	pa = 1.;

double  pj = 0.;

double  pd = 0.;

int	zfd = -1;

int	fromstdin = 0;

int	unbuffered = 0;

int	repeatcnt = 1;


int
main(
	int	argc,
	char	*argv[]
)
{
	char	*err;
	int	rval, getdim = 0;
	int	i;

	fixargv0(argv[0]);		/* sets global progname */
	if (argc < 2)
		goto userr;
	for (i = 1; i < argc && argv[i][0] == '-'; i++)
		switch (argv[i][1]) {
		case 'f':			/* output format */
			switch (argv[i][2]) {
			case 'a':			/* ASCII */
				putr = puta;
				break;
			case 'f':			/* float */
				putr = putf;
				SET_FILE_BINARY(stdout);
				break;
			case 'd':			/* double */
				putr = putd;
				SET_FILE_BINARY(stdout);
				break;
			default:
				goto userr;
			}
			break;
		case 'v':			/* view file or option */
			if (argv[i][2] == 'f') {
				rval = viewfile(argv[++i], &vw, NULL);
				if (rval <= 0) {
					fprintf(stderr,
						"%s: no view in file\n",
							argv[i]);
					return(1);
				}
				break;
			}
			rval = getviewopt(&vw, argc-i, argv+i);
			if (rval < 0)
				goto userr;
			i += rval;
			break;
		case 'd':			/* report dimensions only */
			getdim++;
			break;
		case 'x':			/* x resolution */
			rs.xr = atoi(argv[++i]);
			if (rs.xr <= 0) {
				fprintf(stderr, "%s: bad x resolution\n",
						progname);
				return(1);
			}
			break;
		case 'y':			/* y resolution */
			rs.yr = atoi(argv[++i]);
			if (rs.yr <= 0) {
				fprintf(stderr, "%s: bad y resolution\n",
						progname);
				return(1);
			}
			break;
		case 'c':			/* repeat count */
			repeatcnt = atoi(argv[++i]);
			if (repeatcnt < 1) repeatcnt = 1;
			break;
		case 'p':			/* pixel aspect or jitter */
			if (argv[i][2] == 'a')
				pa = atof(argv[++i]);
			else if (argv[i][2] == 'j')
				pj = atof(argv[++i]);
			else if (argv[i][2] == 'd')
				pd = atof(argv[++i]);
			else
				goto userr;
			break;
		case 'i':			/* get pixels from stdin */
			fromstdin = 1;
			break;
		case 'u':			/* unbuffered output */
			unbuffered = 1;
			break;
		default:
			goto userr;
		}
	if ((i > argc) | (i+2 < argc))
		goto userr;
	if (i < argc) {
		rval = viewfile(argv[i], &vw, &rs);
		if (rval <= 0) {
			fprintf(stderr, "%s: no view in picture\n", argv[i]);
			return(1);
		}
		if (!getdim & (i+1 < argc)) {
			zfd = open_float_depth(argv[i+1], (long)rs.xr*rs.yr);
			if (zfd < 0)
				return(1);
		}
	}
	if ((err = setview(&vw)) != NULL) {
		fprintf(stderr, "%s: %s\n", progname, err);
		return(1);
	}
	if (i == argc)
		normaspect(viewaspect(&vw), &pa, &rs.xr, &rs.yr);
	if (getdim) {
		printf("-x %d -y %d%s\n", rs.xr, rs.yr,
				(vw.vaft > FTINY) ? " -ld+" : "");
		return(0);
	}
	if ((repeatcnt > 1) & (pj > FTINY))
		initurand(1024);
	if (fromstdin)
		pix2rays(stdin);
	else
		putrays();
	return(0);
userr:
	fprintf(stderr,
	"Usage: %s [ -i -u -f{a|f|d} -c rept | -d ] { view opts .. | picture [zbuf] }\n",
			progname);
	return(1);
}


static void
jitterloc(
	RREAL	loc[2]
)
{
	static int	nsamp;
	double		xyr[2];

	if (pj <= FTINY)
		return;

	if (repeatcnt == 1) {
		xyr[0] = frandom();
		xyr[1] = frandom();
	} else				/* stratify samples */
		multisamp(xyr, 2, urand(nsamp++));

	loc[0] += pj*(.5 - xyr[0])/rs.xr;
	loc[1] += pj*(.5 - xyr[1])/rs.yr;
}


static void
pix2rays(
	FILE *fp
)
{
	static FVECT	rorg, rdir;
	float	zval;
	double	px, py;
	RREAL	loc[2];
	int	pp[2];
	double	d;
	int	i, c;

	while (fscanf(fp, "%lf %lf", &px, &py) == 2) {
		px += .5; py += .5;
		loc[0] = px/rs.xr; loc[1] = py/rs.yr;
		if (zfd >= 0) {
			if ((loc[0] < 0) | (loc[0] >= 1) |
					(loc[1] < 0) | (loc[1] >= 1)) {
				fprintf(stderr, "%s: input pixel outside image\n",
						progname);
				exit(1);
			}
			loc2pix(pp, &rs, loc[0], loc[1]);
			if (lseek(zfd,
				(pp[1]*scanlen(&rs)+pp[0])*sizeof(float),
						SEEK_SET) < 0 ||
					read(zfd, &zval, sizeof(float))
						< sizeof(float)) {
				fprintf(stderr, "%s: depth buffer read error\n",
						progname);
				exit(1);
			}
		}
		for (c = repeatcnt; c-- > 0; ) {
			jitterloc(loc);
			d = viewray(rorg, rdir, &vw, loc[0], loc[1]);
			if (d < -FTINY || !jitteraperture(rorg, rdir, &vw, pd))
				rorg[0] = rorg[1] = rorg[2] =
				rdir[0] = rdir[1] = rdir[2] = 0.;
			else if (zfd >= 0)
				for (i = 0; i < 3; i++) {
					rorg[i] += rdir[i]*zval;
					rdir[i] = -rdir[i];
				}
			else if (d > FTINY) {
				rdir[0] *= d; rdir[1] *= d; rdir[2] *= d;
			}
			(*putr)(rorg, rdir);
			if (c) {
				loc[0] = px/rs.xr; loc[1] = py/rs.yr;
			}
		}
		if (unbuffered)
			fflush(stdout);
	}
	if (!feof(fp)) {
		fprintf(stderr, "%s: expected px py on input\n", progname);
		exit(1);
	}
}


static void
putrays(void)
{
	RREAL	loc[2];
	FVECT	rorg, rdir;
	float	*zbuf = NULL;
	int	sc;
	double	d;
	int	si, i, c;

	if (zfd >= 0) {
		zbuf = (float *)malloc(scanlen(&rs)*sizeof(float));
		if (zbuf == NULL) {
			fprintf(stderr, "%s: not enough memory\n", progname);
			exit(1);
		}
	}
	for (sc = 0; sc < numscans(&rs); sc++) {
		if (zfd >= 0) {
			if (read(zfd, zbuf, scanlen(&rs)*sizeof(float)) <
					scanlen(&rs)*sizeof(float)) {
				fprintf(stderr, "%s: depth buffer read error\n",
						progname);
				exit(1);
			}
		}
		for (si = 0; si < scanlen(&rs); si++) {
		    for (c = repeatcnt; c-- > 0; ) {
			pix2loc(loc, &rs, si, sc);
			jitterloc(loc);
			d = viewray(rorg, rdir, &vw, loc[0], loc[1]);
			if (d < -FTINY || !jitteraperture(rorg, rdir, &vw, pd))
				rorg[0] = rorg[1] = rorg[2] =
				rdir[0] = rdir[1] = rdir[2] = 0.;
			else if (zfd >= 0)
				for (i = 0; i < 3; i++) {
					rdir[i] = -rdir[i]*zbuf[si];
					rorg[i] -= rdir[i];
				}
			else if (d > FTINY) {
				rdir[0] *= d; rdir[1] *= d; rdir[2] *= d;
			}
			(*putr)(rorg, rdir);
		    }
		}
	}
	if (zfd >= 0)
		free((void *)zbuf);
}


static void
puta(		/* put out ray in ASCII format */
	FVECT	ro,
	FVECT	rd
)
{
	printf("%.5e %.5e %.5e %.5e %.5e %.5e\n",
			ro[0], ro[1], ro[2],
			rd[0], rd[1], rd[2]);
}


static void
putf(		/* put out ray in float format */
	FVECT	ro,
	FVECT	rd
)
{
	float v[6];

	v[0] = ro[0]; v[1] = ro[1]; v[2] = ro[2];
	v[3] = rd[0]; v[4] = rd[1]; v[5] = rd[2];
	putbinary(v, sizeof(float), 6, stdout);
}


static void
putd(		/* put out ray in double format */
	FVECT	ro,
	FVECT	rd
)
{
	double v[6];

	v[0] = ro[0]; v[1] = ro[1]; v[2] = ro[2];
	v[3] = rd[0]; v[4] = rd[1]; v[5] = rd[2];
	putbinary(v, sizeof(double), 6, stdout);
}
