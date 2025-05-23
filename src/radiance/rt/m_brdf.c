#ifndef lint
static const char	RCSid[] = "$Id: m_brdf.c,v 2.44 2024/12/18 17:57:06 greg Exp $";
#endif
/*
 *  Shading for materials with arbitrary BRDF's
 */

#include "copyright.h"

#include  "ray.h"
#include  "ambient.h"
#include  "data.h"
#include  "source.h"
#include  "otypes.h"
#include  "rtotypes.h"
#include  "func.h"
#include  "pmapmat.h"

/*
 *	Arguments to this material include the color and specularity.
 *  String arguments include the reflection function and files.
 *  The BRDF is currently used just for the specular component to light
 *  sources.  Reflectance values or data coordinates are functions
 *  of the direction to the light source.  (Data modification functions
 *  are passed the source direction as args 2-4.)
 *	We orient the surface towards the incoming ray, so a single
 *  surface can be used to represent an infinitely thin object.
 *
 *  Arguments for MAT_PFUNC and MAT_MFUNC are:
 *	2+	func	funcfile	transform
 *	0
 *	4+	red	grn	blu	specularity	A5 ..
 *
 *  Arguments for MAT_PDATA and MAT_MDATA are:
 *	4+	func	datafile	funcfile	v0 ..	transform
 *	0
 *	4+	red	grn	blu	specularity	A5 ..
 *
 *  Arguments for MAT_TFUNC are:
 *	2+	func	funcfile	transform
 *	0
 *	6+	red	grn	blu	rspec	trans	tspec	A7 ..
 *
 *  Arguments for MAT_TDATA are:
 *	4+	func	datafile	funcfile	v0 ..	transform
 *	0
 *	6+	red	grn	blu	rspec	trans	tspec	A7 ..
 *
 *  Arguments for the more general MAT_BRTDF are:
 *	10+	rrefl	grefl	brefl
 *		rtrns	gtrns	btrns
 *		rbrtd	gbrtd	bbrtd
 *		funcfile	transform
 *	0
 *	9+	rdf	gdf	bdf
 *		rdb	gdb	bdb
 *		rdt	gdt	bdt	A10 ..
 *
 *	In addition to the normal variables available to functions,
 *  we define the following:
 *		NxP, NyP, NzP -		perturbed surface normal
 *		RdotP -			perturbed ray dot product
 *		CrP, CgP, CbP -		perturbed material color (or pattern)
 */

typedef struct {
	OBJREC  *mp;		/* material pointer */
	RAY  *pr;		/* intersected ray */
	DATARRAY  *dp;		/* data array for PDATA, MDATA or TDATA */
	SCOLOR  mcolor;		/* material (or pattern) color */
	SCOLOR  rdiff;		/* diffuse reflection */
	SCOLOR  tdiff;		/* diffuse transmission */
	double  rspec;		/* specular reflectance (1 for BRDTF) */
	double  trans;		/* transmissivity (.5 for BRDTF) */
	double  tspec;		/* specular transmittance (1 for BRDTF) */
	FVECT  pnorm;		/* perturbed surface normal */
	double  pdot;		/* perturbed dot product */
}  BRDFDAT;		/* BRDF material data */


static int setbrdfunc(BRDFDAT *np);


static void
dirbrdf(		/* compute source contribution */
	SCOLOR  scval,			/* returned coefficient */
	void  *nnp,			/* material data */
	FVECT  ldir,			/* light source direction */
	double  omega			/* light source size */
)
{
	BRDFDAT *np = nnp;
	double  ldot;
	double  dtmp;
	SCOLOR  sctmp;
	COLOR  ctmp;
	FVECT  ldx;
	static double  vldx[5], pt[MAXDDIM];
	char	**sa;
	int	i;
#define lddx (vldx+1)

	scolorblack(scval);
	
	ldot = DOT(np->pnorm, ldir);

	if (ldot <= FTINY && ldot >= -FTINY)
		return;		/* too close to grazing */

	if (ldot < 0.0 ? np->trans <= FTINY : np->trans >= 1.0-FTINY)
		return;		/* wrong side */

	if (ldot > 0.0) {
		/*
		 *  Compute and add diffuse reflected component to returned
		 *  color.  The diffuse reflected component will always be
		 *  modified by the color of the material.
		 */
		copyscolor(sctmp, np->rdiff);
		dtmp = ldot * omega / PI;
		scalescolor(sctmp, dtmp);
		saddscolor(scval, sctmp);
	} else {
		/*
		 *  Diffuse transmitted component.
		 */
		copyscolor(sctmp, np->tdiff);
		dtmp = -ldot * omega / PI;
		scalescolor(sctmp, dtmp);
		saddscolor(scval, sctmp);
	}
	if ((ldot > 0.0 ? np->rspec <= FTINY : np->tspec <= FTINY) ||
			ambRayInPmap(np->pr))
		return;		/* diffuse only */
					/* set up function */
	setbrdfunc(np);
	sa = np->mp->oargs.sarg;
	errno = 0;
					/* transform light vector */
	multv3(ldx, ldir, funcxf.xfm);
	for (i = 0; i < 3; i++)
		lddx[i] = ldx[i]/funcxf.sca;
	lddx[3] = omega;
					/* compute BRTDF */
	if (np->mp->otype == MAT_BRTDF) {
		if (sa[6][0] == '0' && !sa[6][1])	/* special case */
			colval(ctmp,RED) = 0.0;
		else
			colval(ctmp,RED) = funvalue(sa[6], 4, lddx);
		if (sa[7][0] == '0' && !sa[7][1])
			colval(ctmp,GRN) = 0.0;
		else if (!strcmp(sa[7],sa[6]))
			colval(ctmp,GRN) = colval(ctmp,RED);
		else
			colval(ctmp,GRN) = funvalue(sa[7], 4, lddx);
		if (sa[8][0] == '0' && !sa[8][1])
			colval(ctmp,BLU) = 0.0;
		else if (!strcmp(sa[8],sa[6]))
			colval(ctmp,BLU) = colval(ctmp,RED);
		else if (!strcmp(sa[8],sa[7]))
			colval(ctmp,BLU) = colval(ctmp,GRN);
		else
			colval(ctmp,BLU) = funvalue(sa[8], 4, lddx);
		dtmp = bright(ctmp);
	} else if (np->dp == NULL) {
		dtmp = funvalue(sa[0], 4, lddx);
		setcolor(ctmp, dtmp, dtmp, dtmp);
	} else {
		for (i = 0; i < np->dp->nd; i++)
			pt[i] = funvalue(sa[3+i], 4, lddx);
		vldx[0] = datavalue(np->dp, pt);
		dtmp = funvalue(sa[0], 5, vldx);
		setcolor(ctmp, dtmp, dtmp, dtmp);
	}
	if ((errno == EDOM) | (errno == ERANGE)) {
		objerror(np->mp, WARNING, "compute error");
		return;
	}
	if (dtmp <= FTINY)
		return;
	setscolor(sctmp, colval(ctmp,RED), colval(ctmp,GRN), colval(ctmp,BLU));
	if (ldot > 0.0) {
		/*
		 *  Compute reflected non-diffuse component.
		 */
		if ((np->mp->otype == MAT_MFUNC) | (np->mp->otype == MAT_MDATA))
			smultscolor(sctmp, np->mcolor);
		dtmp = ldot * omega * np->rspec;
		scalescolor(sctmp, dtmp);
		saddscolor(scval, sctmp);
	} else {
		/*
		 *  Compute transmitted non-diffuse component.
		 */
		if ((np->mp->otype == MAT_TFUNC) | (np->mp->otype == MAT_TDATA))
			smultscolor(sctmp, np->mcolor);
		dtmp = -ldot * omega * np->tspec;
		scalescolor(sctmp, dtmp);
		saddscolor(scval, sctmp);
	}
#undef lddx
}


int
m_brdf(			/* color a ray that hit a BRDTfunc material */
	OBJREC  *m,
	RAY  *r
)
{
	BRDFDAT  nd;
	RAY  sr;
	int  hasrefl, hastrans;
	int  hastexture;
	SCOLOR  sctmp;
	FVECT  vtmp;
	double  d;
	MFUNC  *mf;
	int  i;
						/* check arguments */
	if ((m->oargs.nsargs < 10) | (m->oargs.nfargs < 9))
		objerror(m, USER, "bad # arguments");
	nd.mp = m;
	nd.pr = r;
						/* dummy values */
	nd.rspec = nd.tspec = 1.0;
	nd.trans = 0.5;
						/* diffuse reflectance */
	if (r->rod > 0.0)
		setscolor(nd.rdiff, m->oargs.farg[0],
				m->oargs.farg[1],
				m->oargs.farg[2]);
	else
		setscolor(nd.rdiff, m->oargs.farg[3],
				m->oargs.farg[4],
				m->oargs.farg[5]);
						/* diffuse transmittance */
	setscolor(nd.tdiff, m->oargs.farg[6],
			m->oargs.farg[7],
			m->oargs.farg[8]);
						/* get modifiers */
	raytexture(r, m->omod);
	hastexture = (DOT(r->pert,r->pert) > FTINY*FTINY);
	if (hastexture) {			/* perturb normal */
		nd.pdot = raynormal(nd.pnorm, r);
	} else {
		VCOPY(nd.pnorm, r->ron);
		nd.pdot = r->rod;
	}
	if (r->rod < 0.0) {			/* orient perturbed values */
		nd.pdot = -nd.pdot;
		for (i = 0; i < 3; i++) {
			nd.pnorm[i] = -nd.pnorm[i];
			r->pert[i] = -r->pert[i];
		}
	}
	copyscolor(nd.mcolor, r->pcol);		/* get pattern color */
	smultscolor(nd.rdiff, nd.mcolor);	/* modify diffuse values */
	smultscolor(nd.tdiff, nd.mcolor);
	hasrefl = (sintens(nd.rdiff) > FTINY);
	hastrans = (sintens(nd.tdiff) > FTINY);
						/* load cal file */
	nd.dp = NULL;
	mf = getfunc(m, 9, 0x3F, 0);
						/* compute transmitted ray */
	setbrdfunc(&nd);
	errno = 0;
	setscolor(sctmp, evalue(mf->ep[3]),
			evalue(mf->ep[4]),
			evalue(mf->ep[5]));
	if ((errno == EDOM) | (errno == ERANGE))
		objerror(m, WARNING, "compute error");
	else if (rayorigin(&sr, TRANS, r, sctmp) == 0) {
		if (hastexture && !(r->crtype & (SHADOW|AMBIENT))) {
						/* perturb direction */
			VSUB(sr.rdir, r->rdir, r->pert);
			if (normalize(sr.rdir) == 0.0) {
				objerror(m, WARNING, "illegal perturbation");
				VCOPY(sr.rdir, r->rdir);
			}
		} else {
			VCOPY(sr.rdir, r->rdir);
		}
		rayvalue(&sr);
		smultscolor(sr.rcol, sr.rcoef);
		saddscolor(r->rcol, sr.rcol);
		if ((!hastexture || r->crtype & (SHADOW|AMBIENT)) &&
				nd.tspec > pbright(nd.tdiff) + pbright(nd.rdiff))
			r->rxt = r->rot + raydistance(&sr);
	}
	if (r->crtype & SHADOW)			/* the rest is shadow */
		return(1);

						/* compute reflected ray */
	setbrdfunc(&nd);
	errno = 0;
	setscolor(sctmp, evalue(mf->ep[0]),
			evalue(mf->ep[1]),
			evalue(mf->ep[2]));
	if ((errno == EDOM) | (errno == ERANGE))
		objerror(m, WARNING, "compute error");
	else if (rayorigin(&sr, REFLECTED, r, sctmp) == 0) {
		VSUM(sr.rdir, r->rdir, nd.pnorm, 2.*nd.pdot);
		checknorm(sr.rdir);
		rayvalue(&sr);
		smultscolor(sr.rcol, sr.rcoef);
		copyscolor(r->mcol, sr.rcol);
		saddscolor(r->rcol, sr.rcol);
		r->rmt = r->rot;
		if (r->ro != NULL && isflat(r->ro->otype) &&
				!hastexture | (r->crtype & AMBIENT))
			r->rmt += raydistance(&sr);
	}
						/* compute ambient */
	if (hasrefl) {
		copyscolor(sctmp, nd.rdiff);
		multambient(sctmp, r, nd.pnorm);
		saddscolor(r->rcol, sctmp);	/* add to returned color */
	}
	if (hastrans) {				/* from other side */
		vtmp[0] = -nd.pnorm[0];
		vtmp[1] = -nd.pnorm[1];
		vtmp[2] = -nd.pnorm[2];
		copyscolor(sctmp, nd.tdiff);
		multambient(sctmp, r, vtmp);
		saddscolor(r->rcol, sctmp);
	}
	if (hasrefl | hastrans || m->oargs.sarg[6][0] != '0')
		direct(r, dirbrdf, &nd);	/* add direct component */

	return(1);
}



int
m_brdf2(			/* color a ray that hit a BRDF material */
	OBJREC  *m,
	RAY  *r
)
{
	BRDFDAT  nd;
	SCOLOR  sctmp;
	FVECT  vtmp;
	double  dtmp;
						/* always a shadow */
	if (r->crtype & SHADOW)
		return(1);
						/* check for back side */
	if (r->rod < 0.0) {
		if (!backvis) {
			raytrans(r);
			return(1);
		}
		raytexture(r, m->omod);
		flipsurface(r);			/* reorient if backvis */
	} else
		raytexture(r, m->omod);
						/* check arguments */
	if ((m->oargs.nsargs < (hasdata(m->otype)?4:2)) | (m->oargs.nfargs <
			((m->otype==MAT_TFUNC)|(m->otype==MAT_TDATA)?6:4)))
		objerror(m, USER, "bad # arguments");

	nd.mp = m;
	nd.pr = r;
						/* get material color */
	setscolor(nd.mcolor, m->oargs.farg[0],
			m->oargs.farg[1],
			m->oargs.farg[2]);
						/* get specular component */
	nd.rspec = m->oargs.farg[3];
						/* compute transmittance */
	if ((m->otype == MAT_TFUNC) | (m->otype == MAT_TDATA)) {
		nd.trans = m->oargs.farg[4]*(1.0 - nd.rspec);
		nd.tspec = nd.trans * m->oargs.farg[5];
		dtmp = nd.trans - nd.tspec;
		setscolor(nd.tdiff, dtmp, dtmp, dtmp);
	} else {
		nd.tspec = nd.trans = 0.0;
		scolorblack(nd.tdiff);
	}
						/* compute reflectance */
	dtmp = 1.0 - nd.trans - nd.rspec;
	setscolor(nd.rdiff, dtmp, dtmp, dtmp);
	nd.pdot = raynormal(nd.pnorm, r);	/* perturb normal */
	smultscolor(nd.mcolor, r->pcol);	/* modify material color */
	smultscolor(nd.rdiff, nd.mcolor);
	smultscolor(nd.tdiff, nd.mcolor);
						/* load auxiliary files */
	if (hasdata(m->otype)) {
		nd.dp = getdata(m->oargs.sarg[1]);
		getfunc(m, 2, 0, 0);
	} else {
		nd.dp = NULL;
		getfunc(m, 1, 0, 0);
	}
						/* compute ambient */
	if (nd.trans < 1.0-FTINY) {
		copyscolor(sctmp, nd.mcolor);	/* modified by material color */
		scalescolor(sctmp, 1.0-nd.trans);
		multambient(sctmp, r, nd.pnorm);
		saddscolor(r->rcol, sctmp);	/* add to returned color */
	}
	if (nd.trans > FTINY) {			/* from other side */
		vtmp[0] = -nd.pnorm[0];
		vtmp[1] = -nd.pnorm[1];
		vtmp[2] = -nd.pnorm[2];
		copyscolor(sctmp, nd.mcolor);
		scalescolor(sctmp, nd.trans);
		multambient(sctmp, r, vtmp);
		saddscolor(r->rcol, sctmp);
	}
						/* add direct component */
	direct(r, dirbrdf, &nd);

	return(1);
}


static int
setbrdfunc(			/* set up brdf function and variables */
	BRDFDAT  *np
)
{
	FVECT  vec;
	COLOR  ctmp;

	if (setfunc(np->mp, np->pr) == 0)
		return(0);	/* it's OK, setfunc says we're done */
				/* else (re)assign special variables */
	multv3(vec, np->pnorm, funcxf.xfm);
	varset("NxP`", '=', vec[0]/funcxf.sca);
	varset("NyP`", '=', vec[1]/funcxf.sca);
	varset("NzP`", '=', vec[2]/funcxf.sca);
	varset("RdotP`", '=', np->pdot);
	scolor_color(ctmp, np->mcolor);		/* should use scolor_rgb()? */
	varset("CrP", '=', colval(ctmp,RED));
	varset("CgP", '=', colval(ctmp,GRN));
	varset("CbP", '=', colval(ctmp,BLU));
	return(1);
}
