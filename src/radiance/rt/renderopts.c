#ifndef lint
static const char	RCSid[] = "$Id: renderopts.c,v 2.28 2025/04/22 18:08:48 greg Exp $";
#endif
/*
 *  renderopts.c - process common rendering options
 *
 *  External symbols declared in ray.h
 */

#include "copyright.h"

#include  "ray.h"
#include  "func.h"
#include  "paths.h"
#include  "pmapopt.h"

extern char	*progname;	/* global argv[0] */

char	RFeatureList[2048] =	/* newline-separated feature list */
		"VirtualSources\nSecondarySources\nSourceSubsampling\n"
		"SourceVisibility\nAmbientModifierSelection\n"
		"PathTracing\nRussianRoulette\nLowDiscrepancySeq\n"
		"SpecularSampling\nMaterialMixtures\nAntimatter\nBackFaceVisibility\n"
		"ScatteringModels=WGMD,Ashikhmin-Shirley\n"
		"TabulatedBSDFs=DataFile,KlemsXML,TensorTreeXML,+ViewPeakExtraction\n"
		"Instancing=Octree,TriangleMesh\nAliases\n"
#if MAXCSAMP>3
		"Hyperspectral\n"
#endif
#if !defined(SHADCACHE) || SHADCACHE > 0
		"ShadowCache\n"
#endif
#ifdef  DISPERSE
		"DielectricDispersion\n"
#endif
/*		PMAP_FEATURES	XXX @Roland: need to define this in pmapopt.h */
;


static char *
get_feature(		/* find a specific feature (with optional sublist) */
	const char *feat
)
{
	char	*cp = RFeatureList;
	int	n = 0;

	while ((feat[n] != '\0') & (feat[n] != '='))
		n++;
	if (!n)
		return(NULL);
	while (*cp) {
		if (!strncmp(cp, feat, n) && (cp[n] == '\n') | !feat[n] | (cp[n] == feat[n]))
			return(cp);
		while (*cp++ != '\n')
			;
	}
	return(NULL);
}


static int
match_subfeatures(	/* check if subfeatures are supported */
	char *mysublist,
	char *reqs
)
{
	if (mysublist)
		mysublist = strchr(mysublist, '=');
	if (!mysublist++ | !reqs)
		return(0);		/* not a feature list */
	while (*reqs) {			/* check each of their subfeature requests */
		char	subfeat[64];
		char	*cp = subfeat;
		int	n;
		while (*reqs && (*cp = *reqs++) != ',')
			cp++;
		*cp = '\0';
		if (!(n = cp - subfeat))
			continue;	/* empty subfeature */
		for (cp = mysublist; (cp = strstr(cp, subfeat)) != NULL; cp++)
			if ((cp[-1] == ',') | (cp[-1] == '=') &&
					(cp[n] == ',') | (cp[n] == '\n'))
				break;	/* match */
		if (!cp)
			return(0);	/* missing this one! */
	}
	return(1);			/* matched them all */
}


int
feature_status(		/* report active feature list / check specifics */
	int  ac,
	char  *av[]
)
{
	if (ac <= 0)			/* report entire list? */
		fputs(RFeatureList, stdout);

	for ( ; ac-- > 0; av++) {	/* check each argument */
		char	*cp;
		if (!*av[0]) continue;
		if ((cp = strchr(av[0], '=')) != NULL) {
			if (!match_subfeatures(get_feature(av[0]), cp+1))
				goto missing_feature;
		} else if ((cp = get_feature(av[0])) != NULL) {
			char	*tp = strchr(cp, '=');
			if (tp && tp < strchr(cp, '\n'))
				do
					fputc(*cp, stdout);
				while (*cp++ != '\n');
		} else
			goto missing_feature;
	}
	return(0);			/* return satisfactory status */
missing_feature:			/* or report error */
	fprintf(stderr, "%s: missing feature - %s\n", progname, av[0]);
	return(1);
}


int
getrenderopt(		/* get next render option */
	int  ac,
	char  *av[]
)
{
#define	 check(ol,al)		if (av[0][ol] || \
				badarg(ac-1,av+1,al)) \
				return(-1)
#define	 check_bool(olen,var)		switch (av[0][olen]) { \
				case '\0': var = !var; break; \
				case 'y': case 'Y': case 't': case 'T': \
				case '+': case '1': var = 1; break; \
				case 'n': case 'N': case 'f': case 'F': \
				case '-': case '0': var = 0; break; \
				default: return(-1); }
	static char  **amblp;		/* pointer to build ambient list */
	int	rval;
					/* is it even an option? */
	if (ac < 1 || av[0] == NULL || av[0][0] != '-')
		return(-1);
					/* check if it's one we know */
	switch (av[0][1]) {
	case 'u':				/* uncorrelated sampling */
		check_bool(2,rand_samp);
		return(0);
	case 'b':				/* back face vis. */
		if (av[0][2] == 'v') {
			check_bool(3,backvis);
			return(0);
		}
		break;
	case 'd':				/* direct */
		switch (av[0][2]) {
		case 't':				/* threshold */
			check(3,"f");
			shadthresh = atof(av[1]);
			return(1);
		case 'c':				/* certainty */
			check(3,"f");
			shadcert = atof(av[1]);
			return(1);
		case 'j':				/* jitter */
			check(3,"f");
			dstrsrc = atof(av[1]);
			return(1);
		case 'r':				/* relays */
			check(3,"i");
			directrelay = atoi(av[1]);
			return(1);
		case 'p':				/* pretest */
			check(3,"i");
			vspretest = atoi(av[1]);
			return(1);
		case 'v':				/* visibility */
			check_bool(3,directvis);
			return(0);
		case 's':				/* size */
			check(3,"f");
			srcsizerat = atof(av[1]);
			return(1);
		}
		break;
	case 's':				/* specular */
		switch (av[0][2]) {
		case 't':				/* threshold */
			check(3,"f");
			specthresh = atof(av[1]);
			return(1);
		case 's':				/* sampling */
			check(3,"f");
			specjitter = atof(av[1]);
			return(1);
		}
		break;
	case 'l':				/* limit */
		switch (av[0][2]) {
		case 'r':				/* recursion */
			check(3,"i");
			maxdepth = atoi(av[1]);
			return(1);
		case 'w':				/* weight */
			check(3,"f");
			minweight = atof(av[1]);
			return(1);
		}
		break;
	case 'i':				/* irradiance */
		check_bool(2,do_irrad);
		return(0);
	case 'a':				/* ambient */
		switch (av[0][2]) {
		case 'v':				/* value */
			check(3,"fff");
			setcolor(ambval, atof(av[1]),
					atof(av[2]),
					atof(av[3]));
			return(3);
		case 'w':				/* weight */
			check(3,"i");
			ambvwt = atoi(av[1]);
			return(1);
		case 'a':				/* accuracy */
			check(3,"f");
			ambacc = atof(av[1]);
			return(1);
		case 'r':				/* resolution */
			check(3,"i");
			ambres = atoi(av[1]);
			return(1);
		case 'd':				/* divisions */
			check(3,"i");
			ambdiv = atoi(av[1]);
			return(1);
		case 's':				/* super-samp */
			check(3,"i");
			ambssamp = atoi(av[1]);
			return(1);
		case 'b':				/* bounces */
			check(3,"i");
			ambounce = atoi(av[1]);
			return(1);
		case 'i':				/* include */
		case 'I':
			check(3,"s");
			if (ambincl != 1) {
				ambincl = 1;
				amblp = amblist;
			}
			if (av[0][2] == 'I') {	/* file */
				rval = wordfile(amblp, AMBLLEN-(amblp-amblist),
					getpath(av[1],getrlibpath(),R_OK));
				if (rval < 0) {
					sprintf(errmsg,
			"cannot open ambient include file \"%s\"", av[1]);
					error(SYSTEM, errmsg);
				}
				amblp += rval;
			} else {
				*amblp++ = savqstr(av[1]);
				*amblp = NULL;
			}
			return(1);
		case 'e':				/* exclude */
		case 'E':
			check(3,"s");
			if (ambincl != 0) {
				ambincl = 0;
				amblp = amblist;
			}
			if (av[0][2] == 'E') {	/* file */
				rval = wordfile(amblp, AMBLLEN-(amblp-amblist),
					getpath(av[1],getrlibpath(),R_OK));
				if (rval < 0) {
					sprintf(errmsg,
			"cannot open ambient exclude file \"%s\"", av[1]);
					error(SYSTEM, errmsg);
				}
				amblp += rval;
			} else {
				*amblp++ = savqstr(av[1]);
				*amblp = NULL;
			}
			return(1);
		case 'f':				/* file */
			check(3,"s");
			ambfile = savqstr(av[1]);
			return(1);
		}
		break;
	case 'm':				/* medium */
		switch (av[0][2]) {
		case 'e':				/* extinction */
			check(3,"fff");
			setcolor(cextinction, atof(av[1]),
					atof(av[2]),
					atof(av[3]));
			return(3);
		case 'a':				/* albedo */
			check(3,"fff");
			setcolor(salbedo, atof(av[1]),
					atof(av[2]),
					atof(av[3]));
			return(3);
		case 'g':				/* eccentr. */
			check(3,"f");
			seccg = atof(av[1]);
			return(1);
		case 's':				/* sampling */
			check(3,"f");
			ssampdist = atof(av[1]);
			return(1);
		}
		break;
	case 'f':				/* .cal file */
		check(2,"s");
		loadfunc(av[1]);
		return(1);
	case 'e':				/* .cal expression */
		check(2,"s");
		if (!strchr(av[1], '=') && !strchr(av[1], ':'))
			break;
		scompile(av[1], NULL, 0);
		return(1);
#if MAXCSAMP>3
	case 'c':				/* spectral sampling */
		switch (av[0][2]) {
		case 's':			/* spectral bin count */
			check(3,"i");
			NCSAMP = atoi(av[1]);
			return(1);
		case 'w':			/* wavelength extrema */
			check(3,"ff");
			WLPART[0] = atof(av[1]);
			WLPART[3] = atof(av[2]);
			return(2);
		}
		break;
#endif
	}
	
	/* PMAP: Parse photon mapping options */
	return(getPmapRenderOpt(ac, av));
	
/*	return(-1); */		/* unknown option */

#undef	check
#undef	check_bool
}


void
print_rdefaults(void)		/* print default render values to stdout */
{
	printf(do_irrad ? "-i+\t\t\t\t# irradiance calculation on\n" :
			"-i-\t\t\t\t# irradiance calculation off\n");
	printf(rand_samp ? "-u+\t\t\t\t# uncorrelated Monte Carlo sampling\n" :
			"-u-\t\t\t\t# correlated quasi-Monte Carlo sampling\n");
	printf(backvis ? "-bv+\t\t\t\t# back face visibility on\n" :
			"-bv-\t\t\t\t# back face visibility off\n");
	printf("-dt %f\t\t\t# direct threshold\n", shadthresh);
	printf("-dc %f\t\t\t# direct certainty\n", shadcert);
	printf("-dj %f\t\t\t# direct jitter\n", dstrsrc);
	printf("-ds %f\t\t\t# direct sampling\n", srcsizerat);
	printf("-dr %-9d\t\t\t# direct relays\n", directrelay);
	printf("-dp %-9d\t\t\t# direct pretest density\n", vspretest);
	printf(directvis ? "-dv+\t\t\t\t# direct visibility on\n" :
			"-dv-\t\t\t\t# direct visibility off\n");
	printf("-ss %f\t\t\t# specular sampling\n", specjitter);
	printf("-st %f\t\t\t# specular threshold\n", specthresh);
	printf("-av %f %f %f\t# ambient value\n", colval(ambval,RED),
			colval(ambval,GRN), colval(ambval, BLU));
	printf("-aw %-9d\t\t\t# ambient value weight\n", ambvwt);
	printf("-ab %-9d\t\t\t# ambient bounces\n", ambounce);
	printf("-aa %f\t\t\t# ambient accuracy\n", ambacc);
	printf("-ar %-9d\t\t\t# ambient resolution\n", ambres);
	printf("-ad %-9d\t\t\t# ambient divisions\n", ambdiv);
	printf("-as %-9d\t\t\t# ambient super-samples\n", ambssamp);
	printf("-me %.2e %.2e %.2e\t# mist extinction coefficient\n",
			colval(cextinction,RED),
			colval(cextinction,GRN),
			colval(cextinction,BLU));
	printf("-ma %f %f %f\t# mist scattering albedo\n", colval(salbedo,RED),
			colval(salbedo,GRN), colval(salbedo,BLU));
	printf("-mg %f\t\t\t# mist scattering eccentricity\n", seccg);
	printf("-ms %f\t\t\t# mist sampling distance\n", ssampdist);
	if (NCSAMP > 3) {
		printf("-cs %-2d\t\t\t\t# number of spectral bins\n", NCSAMP);
		printf("-cw %3.0f %3.0f\t\t\t# wavelength limits (nm)\n",
				WLPART[3], WLPART[0]);
	}
	printf("-lr %-9d\t\t\t# limit reflection%s\n", maxdepth,
			maxdepth<=0 ? " (Russian roulette)" : "");
	printf("-lw %.2e\t\t\t# limit weight\n", minweight);
	
	/* PMAP: output photon map defaults */
	printPmapDefaults();
}
