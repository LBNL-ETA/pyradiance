#ifndef lint
static const char RCSid[] = "$Id: mkillum3.c,v 2.15 2023/12/16 18:35:27 greg Exp $";
#endif
/*
 * Routines to print mkillum objects
 */

#include  "mkillum.h"
#include  "paths.h"

char	DATORD[] = "RGB";		/* data ordering */
char	DATSUF[] = ".dat";		/* data file suffix */
char	DSTSUF[] = ".dist";		/* distribution suffix */
char	FNCFNM[] = "illum.cal";		/* function file name */

static void compinv(COLORV *rinv, COLORV *rp, int m);
static void colorout(int p, COLORV *da, int n, int m, double mult, FILE *fp);
static void fputnum(double d, FILE *fp);
static void brightout(COLORV *da, int n, int m, double mult, FILE *fp);
static void fputeol(FILE *fp);
static void compavg(COLOR col, COLORV *da, int n);
static char * dfname(struct illum_args *il, int c);
static FILE * dfopen(struct illum_args *il, int c);


void
printobj(		/* print out an object */
	char  *mod,
	OBJREC  *obj
)
{
	int  i;

	if (issurface(obj->otype) && !strcmp(mod, VOIDID))
		return;		/* don't print void surfaces */
	printf("\n%s %s %s", mod, ofun[obj->otype].funame, obj->oname);
	printf("\n%d", obj->oargs.nsargs);
	for (i = 0; i < obj->oargs.nsargs; i++)
		printf(" %s", obj->oargs.sarg[i]);
#ifdef  IARGS
	printf("\n%d", obj->oargs.niargs);
	for (i = 0; i < obj->oargs.niargs; i++)
		printf(" %d", obj->oargs.iarg[i]);
#else
	printf("\n0");
#endif
	printf("\n%d", obj->oargs.nfargs);
	for (i = 0; i < obj->oargs.nfargs; i++) {
		if (i%3 == 0)
			putchar('\n');
		printf(" %18.12g", obj->oargs.farg[i]);
	}
	putchar('\n');
}


char *
dfname(			/* return data file name */
	struct illum_args  *il,
	int  c
)
{
	char  fname[MAXSTR];
	char  *s;

	s = strcpy(fname, il->datafile);
	s += strlen(s);
	if (c) *s++ = c;
	if (il->dfnum > 0) {
		sprintf(s, "%d", il->dfnum);
		s += strlen(s);
	}
	strcpy(s, DATSUF);
	return(getpath(fname, NULL, 0));
}


static FILE *
dfopen(			/* open data file */
	struct illum_args  *il,
	int  c
)
{
	char  *fn;
	FILE  *fp;
					/* get a usable file name */
	for (fn = dfname(il, c);
			!(il->flags & IL_DATCLB) && access(fn, F_OK) == 0;
			fn = dfname(il, c))
		il->dfnum++;
					/* open it for writing */
	if ((fp = fopen(fn, "w")) == NULL) {
		sprintf(errmsg, "cannot open data file \"%s\"", fn);
		error(SYSTEM, errmsg);
	}
	return(fp);
}


void
flatout(		/* write hemispherical distribution */
	struct illum_args  *il,
	COLORV  *da,
	int  n,
	int  m,
	FVECT  u,
	FVECT  v,
	FVECT  w
)
{
	COLORV  *Ninv;
	FILE  *dfp;
	int  i;

	if ((Ninv = (COLORV *)malloc(3*m*sizeof(COLORV))) == NULL)
		error(SYSTEM, "out of memory in flatout");
	compinv(Ninv, da, m);
	if (il->flags & IL_COLDST) {
		printf("\n%s %s %s%s", VOIDID, ofun[PAT_CDATA].funame,
				il->matname, DSTSUF);
		printf("\n9 red green blue");
		for (i = 0; i < 3; i++) {
			dfp = dfopen(il, DATORD[i]);
			fprintf(dfp, "2\n%f %f %d\n%f %f %d\n",
					1.+.5/n, .5/n, n+1,
					0., 2.*PI, m+1);
			colorout(i, Ninv, 1, m, 1./il->nsamps/il->col[i], dfp);
			colorout(i, da, n, m, 1./il->nsamps/il->col[i], dfp);
			fputeol(dfp);
			fclose(dfp);
			printf(" %s", dfname(il, DATORD[i]));
		}
	} else {
		printf("\n%s %s %s%s", VOIDID, ofun[PAT_BDATA].funame,
				il->matname, DSTSUF);
		printf("\n5 noneg");
		dfp = dfopen(il, 0);
		fprintf(dfp, "2\n%f %f %d\n%f %f %d\n",
				1.+.5/n, .5/n, n+1,
				0., 2.*PI, m+1);
		brightout(Ninv, 1, m, 1./il->nsamps/bright(il->col), dfp);
		brightout(da, n, m, 1./il->nsamps/bright(il->col), dfp);
		fputeol(dfp);
		fclose(dfp);
		printf(" %s", dfname(il, 0));
	}
	printf("\n\t%s il_alth il_azih", FNCFNM);
	printf("\n0\n9\n");
	printf("\t%f\t%f\t%f\n", u[0], u[1], u[2]);
	printf("\t%f\t%f\t%f\n", v[0], v[1], v[2]);
	printf("\t%f\t%f\t%f\n", w[0], w[1], w[2]);
	il->dfnum++;
	free(Ninv);
}


void
roundout(			/* write spherical distribution */
	struct illum_args  *il,
	COLORV  *da,
	int  n,
	int  m
)
{
	COLORV  *Ninv, *Sinv;
	FILE  *dfp;
	int  i;

	if ((Ninv = (COLORV *)malloc(3*m*sizeof(COLORV))) == NULL ||
			(Sinv = (COLORV *)malloc(3*m*sizeof(COLORV))) == NULL)
		error(SYSTEM, "out of memory in roundout");
	compinv(Ninv, da, m);
	compinv(Sinv, da+3*m*(n-1), m);
	if (il->flags & IL_COLDST) {
		printf("\n%s %s %s%s", VOIDID, ofun[PAT_CDATA].funame,
				il->matname, DSTSUF);
		printf("\n9 red green blue");
		for (i = 0; i < 3; i++) {
			dfp = dfopen(il, DATORD[i]);
			fprintf(dfp, "2\n%f %f %d\n%f %f %d\n",
					1.+1./n, -1.-1./n, n+2,
					0., 2.*PI, m+1);
			colorout(i, Ninv, 1, m, 1./il->nsamps/il->col[i], dfp);
			colorout(i, da, n, m, 1./il->nsamps/il->col[i], dfp);
			colorout(i, Sinv, 1, m, 1./il->nsamps/il->col[i], dfp);
			fputeol(dfp);
			fclose(dfp);
			printf(" %s", dfname(il, DATORD[i]));
		}
	} else {
		printf("\n%s %s %s%s", VOIDID, ofun[PAT_BDATA].funame,
				il->matname, DSTSUF);
		printf("\n5 noneg");
		dfp = dfopen(il, 0);
		fprintf(dfp, "2\n%f %f %d\n%f %f %d\n",
				1.+1./n, -1.-1./n, n+2,
				0., 2.*PI, m+1);
		brightout(Ninv, 1, m, 1./il->nsamps/bright(il->col), dfp);
		brightout(da, n, m, 1./il->nsamps/bright(il->col), dfp);
		brightout(Sinv, 1, m, 1./il->nsamps/bright(il->col), dfp);
		fputeol(dfp);
		fclose(dfp);
		printf(" %s", dfname(il, 0));
	}
	printf("\n\t%s il_alt il_azi", FNCFNM);
	printf("\n0\n0\n");
	il->dfnum++;
	free(Ninv);
	free(Sinv);
}


void
illumout(		/* print illum object */
	struct illum_args  *il,
	OBJREC  *ob
)
{
	double  cout[3];

	if (il->sampdens <= 0)
		printf("\n%s ", VOIDID);
	else
		printf("\n%s%s ", il->matname, DSTSUF);
	printf("%s %s", ofun[il->flags&IL_LIGHT?MAT_LIGHT:MAT_ILLUM].funame,
			il->matname);
	if (il->flags & IL_LIGHT || !strcmp(il->altmat,VOIDID))
		printf("\n0");
	else
		printf("\n1 %s", il->altmat);
	if (il->flags & IL_COLAVG) {
		cout[0] = il->col[0];
		cout[1] = il->col[1];
		cout[2] = il->col[2];
	} else {
		cout[0] = cout[1] = cout[2] = bright(il->col);
	}
	printf("\n0\n3 %f %f %f\n", cout[0], cout[1], cout[2]);

	printobj(il->matname, ob);
}


static void
compavg(		/* compute average for set of data values */
	COLOR  col,
	COLORV  *da,
	int  n
)
{
	int  i;

	setcolor(col, 0.0, 0.0, 0.0);
	i = n;
	while (i-- > 0) {
		addcolor(col, da);
		da += 3;
	}
	scalecolor(col, 1./(double)n);
}


static void
compinv(		/* compute other side of row average */
	COLORV  *rinv,
	COLORV  *rp,
	int  m
)
{
	COLOR  avg;

	compavg(avg, rp, m);		/* row average */
	while (m-- > 0) {
		*rinv++ = 2.*avg[0] - *rp++;
		*rinv++ = 2.*avg[1] - *rp++;
		*rinv++ = 2.*avg[2] - *rp++;
	}
}


int
average(		/* evaluate average value for distribution */
	struct illum_args  *il,
	COLORV  *da,
	int  n
)
{
	compavg(il->col, da, n);	/* average */
	if (il->nsamps > 1) {
		il->col[0] /= (double)il->nsamps;
		il->col[1] /= (double)il->nsamps;
		il->col[2] /= (double)il->nsamps;
	}
					/* brighter than minimum? */
	return(bright(il->col) > il->minbrt+FTINY);
}


static int	colmcnt = 0;	/* count of columns written */

static void
fputnum(			/* put out a number to fp */
	double  d,
	FILE  *fp
)
{
	if (colmcnt++ % 5 == 0)
		putc('\n', fp);
	fprintf(fp, " %11e", d);
}


static void
fputeol(			/* write end of line to fp */
	FILE  *fp
)
{
	putc('\n', fp);
	colmcnt = 0;
}


static void
colorout(	/* put out color distribution data */
	int  p,
	COLORV  *da,
	int  n,
	int  m,
	double  mult,
	FILE  *fp
)
{
	int  i, j;

	for (i = 0; i < n; i++) {
		for (j = 0; j < m; j++) {
			fputnum(mult*da[p], fp);
			da += 3;
		}
		fputnum(mult*da[p-3*m], fp);	/* wrap phi */
	}
}


static void
brightout(	/* put out brightness distribution data */
	COLORV  *da,
	int  n,
	int  m,
	double  mult,
	FILE  *fp
)
{
	int  i, j;

	for (i = 0; i < n; i++) {
		for (j = 0; j < m; j++) {
			fputnum(mult*bright(da), fp);
			da += 3;
		}
		fputnum(mult*bright(da-3*m), fp);	/* wrap phi */
	}
}
