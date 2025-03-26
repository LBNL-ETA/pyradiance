/* RCSid: $Id: warp3d.h,v 3.5 2004/03/28 20:33:14 schorsch Exp $ */
/*
 * Header file for 3D warping routines.
 */
#ifndef _RAD_WARP3D_H_
#define _RAD_WARP3D_H_

#include "lookup.h"

#ifdef __cplusplus
extern "C" {
#endif

				/* interpolation flags */
#define W3EXACT		01		/* no interpolation (slow) */
#define W3FAST		02		/* discontinuous approx. (fast) */

				/* return flags for warp3d() */
#define W3OK		0		/* normal return status */
#define W3GAMUT		01		/* out of gamut */
#define W3BADMAP	02		/* singular map */
#define W3ERROR		04		/* system error (check errno) */

#define GNBITS	6		/* number of bits per grid size <= 8 */
#define MAXGN	(1<<GNBITS)	/* maximum grid dimension */

typedef unsigned char	GNDX[3];	/* grid index type */

typedef float	W3VEC[3];	/* vector type for 3D warp maps */

struct grid3d {
	unsigned char	flags;		/* interpolation flags */
	GNDX	gn;			/* grid dimensions */
	W3VEC	gmin, gstep;		/* grid corner and voxel size */
	LUTAB	gtab;			/* grid lookup table */
};				/* a regular, sparse warping grid */

typedef struct {
	W3VEC	*ip, *ov;		/* discrete input/displ. pairs */
	int	npts;			/* number of point pairs */
	W3VEC	llim, ulim;		/* lower and upper input limits */
	double	d2min, d2max;		/* min. and max. point distance^2 */
	struct grid3d	grid;		/* point conversion grid */
} WARP3D;			/* a warp map */

extern int warp3d(W3VEC po, W3VEC pi, WARP3D *wp);
extern int add3dpt(WARP3D* wp, W3VEC pti, W3VEC pto);
extern WARP3D* new3dw(int flgs);
extern WARP3D* load3dw(char *fn, WARP3D *wp);
extern void free3dw(WARP3D *wp);
extern int set3dwfl(WARP3D *wp, int flgs);

#define  W3VCPY(v1,v2)	((v1)[0]=(v2)[0],(v1)[1]=(v2)[1],(v1)[2]=(v2)[2])

#ifdef __cplusplus
}
#endif
#endif /* _RAD_WARP3D_H_ */

