#ifndef lint
static const char RCSid[] = "$Id: glass.c,v 2.29 2023/11/15 18:02:52 greg Exp $";
#endif
/*
 *  glass.c - simpler shading function for thin glass surfaces.
 */

#include "copyright.h"

#include  "ray.h"
#include  "otypes.h"
#include  "rtotypes.h"
#include  "pmapmat.h"

/*
 *  This definition of glass provides for a quick calculation
 *  using a single surface where two closely spaced parallel
 *  dielectric surfaces would otherwise be used.  The chief
 *  advantage to using this material is speed, since internal
 *  reflections are avoided.
 *
 *  The specification for glass is as follows:
 *
 *	modifier glass id
 *	0
 *	0
 *	3+ red grn blu [refractive_index]
 *
 *  The color is used for the transmission at normal incidence.
 *  To compute transmissivity (tn) from transmittance (Tn) use:
 *
 *	tn = (sqrt(.8402528435+.0072522239*Tn*Tn)-.9166530661)/.0036261119/Tn
 *
 *  The transmissivity of standard 88% transmittance glass is 0.96.
 *  A refractive index other than the default can be used by giving
 *  it as the fourth real argument.  The above formula no longer applies.
 *
 *  If we appear to hit the back side of the surface, then we
 *  turn the normal around.
 */

#define  RINDEX		1.52		/* refractive index of glass */


int
m_glass(		/* color a ray which hit a thin glass surface */
	OBJREC  *m,
	RAY  *r
)
{
	COLOR  mcolor;
	SCOLOR  scoef;
	double	ctemp[3];
	double  pdot;
	FVECT  pnorm;
	double  rindex=0, cos2;
	int  hastexture, hastrans;
	double  d, r1e, r1m;
	RAY  p;
	int  i;

	/* PMAP: skip refracted shadow or ambient ray if accounted for in 
	   photon map */
	if (shadowRayInPmap(r) || ambRayInPmap(r))
		return(1);
						/* check arguments */
	if (m->oargs.nfargs == 3)
		rindex = RINDEX;		/* default value of n */
	else if (m->oargs.nfargs == 4)
		rindex = m->oargs.farg[3];	/* use their value */
	else
		objerror(m, USER, "bad arguments");
						/* check back face visibility */
	if (!backvis && r->rod <= 0.0) {
		raytrans(r);
		return(1);
	}
						/* check transmission */
	setcolor(mcolor, m->oargs.farg[0], m->oargs.farg[1], m->oargs.farg[2]);
	if ((hastrans = (intens(mcolor) > 1e-15))) {
		for (i = 0; i < 3; i++)
			if (colval(mcolor,i) < 1e-15)
				colval(mcolor,i) = 1e-15;
	} else if (r->crtype & SHADOW)
		return(1);
						/* get modifiers */
	raytexture(r, m->omod);
	if (r->rod < 0.0)			/* reorient if necessary */
		flipsurface(r);
						/* perturb normal */
	hastexture = (DOT(r->pert,r->pert) > FTINY*FTINY);
	if (hastexture) {
		pdot = raynormal(pnorm, r);
	} else {
		VCOPY(pnorm, r->ron);
		pdot = r->rod;
	}
						/* angular transmission */
	cos2 = sqrt( (1.0-1.0/(rindex*rindex)) +
		     pdot*pdot/(rindex*rindex) );
	if (hastrans)
		setcolor(mcolor, pow(colval(mcolor,RED), 1.0/cos2),
				 pow(colval(mcolor,GRN), 1.0/cos2),
				 pow(colval(mcolor,BLU), 1.0/cos2));

						/* compute reflection */
	r1e = (pdot - rindex*cos2) / (pdot + rindex*cos2);
	r1e *= r1e;
	r1m = (1.0/pdot - rindex/cos2) / (1.0/pdot + rindex/cos2);
	r1m *= r1m;
						/* compute transmission */
	if (hastrans) {
		for (i = 0; i < 3; i++) {
			d = colval(mcolor, i);
			ctemp[i] = .5*(1.0-r1e)*(1.0-r1e)*d /
							(1.0-r1e*r1e*d*d) +
					.5*(1.0-r1m)*(1.0-r1m)*d /
							(1.0-r1m*r1m*d*d);
		}
		setscolor(scoef, ctemp[RED], ctemp[GRN], ctemp[BLU]);
		smultscolor(scoef, r->pcol);	/* modify by pattern */
						/* transmitted ray */
		if (rayorigin(&p, TRANS, r, scoef) == 0) {
			if (!(r->crtype & (SHADOW|AMBIENT)) && hastexture) {
				VSUM(p.rdir, r->rdir, r->pert, 2.*(1.-rindex));
				if (normalize(p.rdir) == 0.0) {
					objerror(m, WARNING, "bad perturbation");
					VCOPY(p.rdir, r->rdir);
				}
			} else {
				VCOPY(p.rdir, r->rdir);
			}
			rayvalue(&p);
			smultscolor(p.rcol, p.rcoef);
			saddscolor(r->rcol, p.rcol);
			if (!hastexture || r->crtype & (SHADOW|AMBIENT))
				r->rxt = r->rot + raydistance(&p);
		}
	}
	if (r->crtype & SHADOW)			/* skip reflected ray */
		return(1);
						/* compute reflectance */
	for (i = 0; i < 3; i++) {
		d = colval(mcolor, i);
		d *= d;
		ctemp[i] = .5*r1e*(1.0+(1.0-2.0*r1e)*d)/(1.0-r1e*r1e*d) +
				.5*r1m*(1.0+(1.0-2.0*r1m)*d)/(1.0-r1m*r1m*d);
	}
	setscolor(scoef, ctemp[RED], ctemp[GRN], ctemp[BLU]);
						/* reflected ray */
	if (rayorigin(&p, REFLECTED, r, scoef) == 0) {
		VSUM(p.rdir, r->rdir, pnorm, 2.*pdot);
		checknorm(p.rdir);
		rayvalue(&p);
		smultscolor(p.rcol, p.rcoef);
		copyscolor(r->mcol, p.rcol);
		saddscolor(r->rcol, p.rcol);
		r->rmt = r->rot;
		if (r->ro != NULL && isflat(r->ro->otype) &&
				!hastexture | (r->crtype & AMBIENT))
			r->rmt += raydistance(&p);
	}
	return(1);
}
