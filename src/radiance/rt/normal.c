#ifndef lint
static const char RCSid[] = "$Id: normal.c,v 2.90 2025/06/20 18:05:30 greg Exp $";
#endif
/*
 *  normal.c - shading function for normal materials.
 *
 *     8/19/85
 *     12/19/85 - added stuff for metals.
 *     6/26/87 - improved specular model.
 *     9/28/87 - added model for translucent materials.
 *     Later changes described in delta comments.
 */

#include "copyright.h"

#include  "ray.h"
#include  "ambient.h"
#include  "source.h"
#include  "otypes.h"
#include  "rtotypes.h"
#include  "random.h"
#include  "pmapmat.h"

#ifndef  MAXITER
#define  MAXITER	10		/* maximum # specular ray attempts */
#endif
					/* estimate of Fresnel function */
#define  FRESNE(ci)	(exp(-5.85*(ci)) - 0.00202943064)
#define  FRESTHRESH	0.017999	/* minimum specularity for approx. */


/*
 *	This routine implements the isotropic Gaussian
 *  model described by Ward in Siggraph `92 article.
 *	We orient the surface towards the incoming ray, so a single
 *  surface can be used to represent an infinitely thin object.
 *
 *  Arguments for MAT_PLASTIC and MAT_METAL are:
 *	red	grn	blu	specular-frac.	facet-slope
 *
 *  Arguments for MAT_TRANS are:
 *	red 	grn	blu	rspec	rough	trans	tspec
 */

				/* specularity flags */
#define  SP_REFL	01		/* has reflected specular component */
#define  SP_TRAN	02		/* has transmitted specular */
#define  SP_PURE	04		/* purely specular (zero roughness) */
#define  SP_FLAT	010		/* flat reflecting surface */
#define  SP_RBLT	020		/* reflection below sample threshold */
#define  SP_TBLT	040		/* transmission below threshold */

typedef struct {
	OBJREC  *mp;		/* material pointer */
	RAY  *rp;		/* ray pointer */
	short  specfl;		/* specularity flags, defined above */
	SCOLOR  mcolor;		/* color of this material */
	SCOLOR  scolor;		/* color of specular component */
	FVECT  prdir;		/* vector in transmitted direction */
	double  alpha2;		/* roughness squared */
	double  rdiff, rspec;	/* reflected specular, diffuse */
	double  trans;		/* transmissivity */
	double  tdiff, tspec;	/* transmitted specular, diffuse */
	FVECT  pnorm;		/* perturbed surface normal */
	double  pdot;		/* perturbed dot product */
}  NORMDAT;		/* normal material data */

static void gaussamp(NORMDAT  *np);


static void
dirnorm(		/* compute source contribution */
	SCOLOR  scval,			/* returned coefficient */
	void  *nnp,			/* material data */
	FVECT  ldir,			/* light source direction */
	double  omega			/* light source size */
)
{
	NORMDAT *np = nnp;
	double  ldot;
	double  lrdiff, ltdiff;
	double  dtmp, d2, d3, d4;
	FVECT  vtmp;
	SCOLOR  sctmp;

	scolorblack(scval);

	ldot = DOT(np->pnorm, ldir);

	if (ldot < 0.0 ? np->trans <= FTINY : np->trans >= 1.0-FTINY)
		return;		/* wrong side */

				/* Fresnel estimate */
	lrdiff = np->rdiff;
	ltdiff = np->tdiff;
	if (np->specfl & SP_PURE && np->rspec >= FRESTHRESH &&
			(lrdiff > FTINY) | (ltdiff > FTINY)) {
		dtmp = 1. - FRESNE(fabs(ldot));
		lrdiff *= dtmp;
		ltdiff *= dtmp;
	}

	if ((ldot > FTINY) & (lrdiff > FTINY)) {
		/*
		 *  Compute and add diffuse reflected component to returned
		 *  color.  The diffuse reflected component will always be
		 *  modified by the color of the material.
		 */
		copyscolor(sctmp, np->mcolor);
		dtmp = ldot * omega * lrdiff * (1.0/PI);
		scalescolor(sctmp, dtmp);
		saddscolor(scval, sctmp);
	}

	if ((ldot < -FTINY) & (ltdiff > FTINY)) {
		/*
		 *  Compute diffuse transmission.
		 */
		copyscolor(sctmp, np->mcolor);
		dtmp = -ldot * omega * ltdiff * (1.0/PI);
		scalescolor(sctmp, dtmp);
		saddscolor(scval, sctmp);
	}

	if (ambRayInPmap(np->rp))
		return;		/* specular already in photon map */

	if ((ldot > FTINY) & ((np->specfl&(SP_REFL|SP_PURE)) == SP_REFL)) {
		/*
		 *  Compute specular reflection coefficient using
		 *  Gaussian distribution model.
		 */
						/* roughness */
		dtmp = np->alpha2;
						/* + source if flat */
		if (np->specfl & SP_FLAT)
			dtmp += (1. - dstrsrc) * omega * (0.25/PI);
						/* half vector */
		VSUB(vtmp, ldir, np->rp->rdir);
		d2 = DOT(vtmp, np->pnorm);
		d2 *= d2;
		d3 = DOT(vtmp,vtmp);
		d4 = (d3 - d2) / d2;
						/* new W-G-M-D model */
		dtmp = exp(-d4/dtmp) * d3 / (PI * d2*d2 * dtmp);
						/* worth using? */
		if (dtmp > FTINY) {
			copyscolor(sctmp, np->scolor);
			dtmp *= ldot * omega;
			scalescolor(sctmp, dtmp);
			saddscolor(scval, sctmp);
		}
	}
	

	if ((ldot < -FTINY) & ((np->specfl&(SP_TRAN|SP_PURE)) == SP_TRAN)) {
		/*
		 *  Compute specular transmission.  Specular transmission
		 *  is always modified by material color.
		 */
						/* roughness + source */
		dtmp = np->alpha2 + omega*(1.0/PI);
						/* Gaussian */
		dtmp = exp((2.*DOT(np->prdir,ldir)-2.)/dtmp)/(PI*dtmp);
						/* worth using? */
		if (dtmp > FTINY) {
			copyscolor(sctmp, np->mcolor);
			dtmp *= np->tspec * omega * sqrt(-ldot/np->pdot);
			scalescolor(sctmp, dtmp);
			saddscolor(scval, sctmp);
		}
	}
}


int
m_normal(			/* color a ray that hit something normal */
	OBJREC  *m,
	RAY  *r
)
{
	NORMDAT  nd;
	double  fest;
	int	hastexture;
	double	d;
	SCOLOR  sctmp;
	int  i;

	/* PMAP: skip transmitted shadow ray if accounted for in photon map */
	/* No longer needed?
	if (shadowRayInPmap(r) || ambRayInPmap(r))
		return(1); */		
		
						/* easy shadow test */
	if (r->crtype & SHADOW && m->otype != MAT_TRANS)
		return(1);

	if (m->oargs.nfargs != (m->otype == MAT_TRANS ? 7 : 5))
		objerror(m, USER, "bad number of arguments");
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
	nd.mp = m;
	nd.rp = r;
						/* get material color */
	setscolor(nd.mcolor, m->oargs.farg[0],
			   m->oargs.farg[1],
			   m->oargs.farg[2]);
						/* get roughness */
	nd.specfl = 0;
	nd.alpha2 = m->oargs.farg[4];
	if ((nd.alpha2 *= nd.alpha2) <= FTINY)
		nd.specfl |= SP_PURE;

	if ( (hastexture = (DOT(r->pert,r->pert) > FTINY*FTINY)) ) {
		nd.pdot = raynormal(nd.pnorm, r);	/* perturb normal */
	} else {
		VCOPY(nd.pnorm, r->ron);
		nd.pdot = r->rod;
	}
	if (!hastexture && r->ro != NULL && isflat(r->ro->otype))
		nd.specfl |= SP_FLAT;
	if (nd.pdot < .001)
		nd.pdot = .001;			/* non-zero for dirnorm() */
	smultscolor(nd.mcolor, r->pcol);	/* modify material color */
	nd.rspec = m->oargs.farg[3];
						/* compute Fresnel approx. */
	if (nd.specfl & SP_PURE && nd.rspec >= FRESTHRESH) {
		fest = FRESNE(nd.pdot);
		nd.rspec += fest*(1. - nd.rspec);
	} else
		fest = 0.;
						/* compute transmission */
	if (m->otype == MAT_TRANS) {
		nd.trans = m->oargs.farg[5]*(1.0 - nd.rspec);
		nd.tspec = nd.trans * m->oargs.farg[6];
		nd.tdiff = nd.trans - nd.tspec;
		if (nd.tspec > FTINY) {
			nd.specfl |= SP_TRAN;
							/* check threshold */
			if (!(nd.specfl & SP_PURE) &&
					specthresh >= nd.tspec-FTINY)
				nd.specfl |= SP_TBLT;
			if (!hastexture || r->crtype & (SHADOW|AMBIENT)) {
				VCOPY(nd.prdir, r->rdir);
			} else {
							/* perturb */
				VSUB(nd.prdir, r->rdir, r->pert);
				if (DOT(nd.prdir, r->ron) < -FTINY)
					normalize(nd.prdir);	/* OK */
				else
					VCOPY(nd.prdir, r->rdir);
			}
		}
	} else
		nd.tdiff = nd.tspec = nd.trans = 0.0;
						/* diffuse reflection */
	nd.rdiff = 1.0 - nd.trans - nd.rspec;
						/* transmitted ray */
	if ((nd.specfl&(SP_TRAN|SP_PURE|SP_TBLT)) == (SP_TRAN|SP_PURE)) {
		RAY  lr;
		copyscolor(lr.rcoef, nd.mcolor);	/* modified by color */
		scalescolor(lr.rcoef, nd.tspec);
		if (rayorigin(&lr, TRANS, r, lr.rcoef) == 0) {
			VCOPY(lr.rdir, nd.prdir);
			rayvalue(&lr);
			smultscolor(lr.rcol, lr.rcoef);
			saddscolor(r->rcol, lr.rcol);
			if (nd.tspec >= 1.0-FTINY) {
						/* completely transparent */
				smultscolor(lr.mcol, lr.rcoef);
				copyscolor(r->mcol, lr.mcol);
				r->rmt = r->rot + lr.rmt;
				r->rxt = r->rot + lr.rxt;
			} else if (nd.tspec > nd.tdiff + nd.rdiff)
				r->rxt = r->rot + raydistance(&lr);
		}
	}

	if (r->crtype & SHADOW)			/* the rest is shadow */
		return(1);
						/* get specular reflection */
	if (nd.rspec > FTINY) {
		nd.specfl |= SP_REFL;
						/* compute specular color */
		if (m->otype != MAT_METAL) {
			setscolor(nd.scolor, nd.rspec, nd.rspec, nd.rspec);
		} else if (fest > FTINY) {
			d = m->oargs.farg[3]*(1. - fest);
			for (i = NCSAMP; i--; )
				nd.scolor[i] = fest + nd.mcolor[i]*d;
		} else {
			copyscolor(nd.scolor, nd.mcolor);
			scalescolor(nd.scolor, nd.rspec);
		}
						/* check threshold */
		if (!(nd.specfl & SP_PURE) && specthresh >= nd.rspec-FTINY)
			nd.specfl |= SP_RBLT;
	}
						/* reflected ray */
	if ((nd.specfl&(SP_REFL|SP_PURE|SP_RBLT)) == (SP_REFL|SP_PURE)) {
		RAY  lr;
		if (rayorigin(&lr, REFLECTED, r, nd.scolor) == 0) {
						/* compute reflected ray */
			VSUM(lr.rdir, r->rdir, nd.pnorm, 2.*nd.pdot);
						/* penetration? */
			if (hastexture && DOT(lr.rdir, r->ron) <= FTINY)
				VSUM(lr.rdir, r->rdir, r->ron, 2.*r->rod);
			checknorm(lr.rdir);
			rayvalue(&lr);
			smultscolor(lr.rcol, lr.rcoef);
			copyscolor(r->mcol, lr.rcol);
			saddscolor(r->rcol, lr.rcol);
			r->rmt = r->rot;
			if (nd.specfl & SP_FLAT && r->crtype & AMBIENT)
				r->rmt += raydistance(&lr);
		}
	}

	if (nd.specfl & SP_PURE && nd.rdiff <= FTINY && nd.tdiff <= FTINY)
		return(1);			/* 100% pure specular */

	if (!(nd.specfl & SP_PURE))
		gaussamp(&nd);			/* checks *BLT flags */

	if (nd.rdiff > FTINY) {		/* ambient from this side */
		copyscolor(sctmp, nd.mcolor);	/* modified by material color */
		scalescolor(sctmp, nd.rdiff);
		if (nd.specfl & SP_RBLT)	/* add in specular as well? */
			saddscolor(sctmp, nd.scolor);
		multambient(sctmp, r, nd.pnorm);
		saddscolor(r->rcol, sctmp);	/* add to returned color */
	}
	if (nd.tdiff > FTINY) {		/* ambient from other side */
		FVECT  bnorm;
		copyscolor(sctmp, nd.mcolor);	/* modified by color */
		if (nd.specfl & SP_TBLT) {
			scalescolor(sctmp, nd.trans);
		} else {
			scalescolor(sctmp, nd.tdiff);
		}
		bnorm[0] = -nd.pnorm[0];
		bnorm[1] = -nd.pnorm[1];
		bnorm[2] = -nd.pnorm[2];
		multambient(sctmp, r, bnorm);
		saddscolor(r->rcol, sctmp);
	}
					/* add direct component */
	direct(r, dirnorm, &nd);

	return(1);
}


static void
gaussamp(			/* sample Gaussian specular */
	NORMDAT  *np
)
{
	RAY  sr;
	FVECT  u, v, h;
	double  rv[2];
	double  d, sinp, cosp;
	SCOLOR  scol;
	int  maxiter, ntrials, nstarget, nstaken;
	int  i;
					/* quick test */
	if ((np->specfl & (SP_REFL|SP_RBLT)) != SP_REFL &&
			(np->specfl & (SP_TRAN|SP_TBLT)) != SP_TRAN)
		return;
					/* set up sample coordinates */
	getperpendicular(u, np->pnorm, rand_samp);
	fcross(v, np->pnorm, u);
					/* compute reflection */
	if ((np->specfl & (SP_REFL|SP_RBLT)) == SP_REFL &&
			rayorigin(&sr, RSPECULAR, np->rp, np->scolor) == 0) {
		nstarget = 1;
		if (specjitter > 1.5) {	/* multiple samples? */
			nstarget = specjitter*np->rp->rweight + .5;
			if (sr.rweight <= minweight*nstarget)
				nstarget = sr.rweight/minweight;
			if (nstarget > 1) {
				d = 1./nstarget;
				scalescolor(sr.rcoef, d);
				sr.rweight *= d;
			} else
				nstarget = 1;
		}
		scolorblack(scol);
		dimlist[ndims_inc()] = (int)(size_t)np->mp;
		maxiter = MAXITER*nstarget;
		for (nstaken = ntrials = 0; nstaken < nstarget &&
						ntrials < maxiter; ntrials++) {
			if (ntrials)
				d = frandom();
			else
				d = urand(ilhash(dimlist,ndims)+samplendx);
			multisamp(rv, 2, d);
			d = 2.0*PI * rv[0];
			cosp = tcos(d);
			sinp = tsin(d);
			if ((0. <= specjitter) & (specjitter < 1.))
				rv[1] = 1.0 - specjitter*rv[1];
			if (rv[1] <= FTINY)
				d = 1.0;
			else
				d = sqrt( np->alpha2 * -log(rv[1]) );
			for (i = 0; i < 3; i++)
				h[i] = np->pnorm[i] + d*(cosp*u[i] + sinp*v[i]);
			d = -2.0 * DOT(h, np->rp->rdir) / (1.0 + d*d);
			VSUM(sr.rdir, np->rp->rdir, h, d);
						/* sample rejection test */
			if ((d = DOT(sr.rdir, np->rp->ron)) <= FTINY)
				continue;
			checknorm(sr.rdir);
			if (nstarget > 1) {	/* W-G-M-D adjustment */
				if (nstaken) rayclear(&sr);
				rayvalue(&sr);
				d = 2./(1. + np->rp->rod/d);
				scalescolor(sr.rcol, d);
				saddscolor(scol, sr.rcol);
			} else {
				rayvalue(&sr);
				smultscolor(sr.rcol, sr.rcoef);
				saddscolor(np->rp->rcol, sr.rcol);
			}
			++nstaken;
		}
		if (nstarget > 1) {		/* final W-G-M-D weighting */
			smultscolor(scol, sr.rcoef);
			d = (double)nstarget/ntrials;
			scalescolor(scol, d);
			saddscolor(np->rp->rcol, scol);
		}
		dec_ndims();
	}
					/* compute transmission */
	copyscolor(sr.rcoef, np->mcolor);	/* modified by color */
	scalescolor(sr.rcoef, np->tspec);
	if ((np->specfl & (SP_TRAN|SP_TBLT)) == SP_TRAN &&
			rayorigin(&sr, TSPECULAR, np->rp, sr.rcoef) == 0) {
		nstarget = 1;
		if (specjitter > 1.5) {	/* multiple samples? */
			nstarget = specjitter*np->rp->rweight + .5;
			if (sr.rweight <= minweight*nstarget)
				nstarget = sr.rweight/minweight;
			if (nstarget > 1) {
				d = 1./nstarget;
				scalescolor(sr.rcoef, d);
				sr.rweight *= d;
			} else
				nstarget = 1;
		}
		dimlist[ndims_inc()] = (int)(size_t)np->mp;
		maxiter = MAXITER*nstarget;
		for (nstaken = ntrials = 0; nstaken < nstarget &&
						ntrials < maxiter; ntrials++) {
			if (ntrials)
				d = frandom();
			else
				d = urand(ilhash(dimlist,ndims)+samplendx);
			multisamp(rv, 2, d);
			d = 2.0*PI * rv[0];
			cosp = tcos(d);
			sinp = tsin(d);
			if ((0. <= specjitter) & (specjitter < 1.))
				rv[1] = 1.0 - specjitter*rv[1];
			if (rv[1] <= FTINY)
				d = 1.0;
			else
				d = sqrt( np->alpha2 * -log(rv[1]) );
			for (i = 0; i < 3; i++)
				sr.rdir[i] = np->prdir[i] + d*(cosp*u[i] + sinp*v[i]);
						/* sample rejection test */
			if (DOT(sr.rdir, np->rp->ron) >= -FTINY)
				continue;
			normalize(sr.rdir);	/* OK, normalize */
			if (nstaken)		/* multi-sampling */
				rayclear(&sr);
			rayvalue(&sr);
			smultscolor(sr.rcol, sr.rcoef);
			saddscolor(np->rp->rcol, sr.rcol);
			++nstaken;
		}
		dec_ndims();
	}
}
