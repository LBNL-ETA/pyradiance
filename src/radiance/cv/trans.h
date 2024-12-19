/* RCSid: $Id: trans.h,v 2.5 2023/06/09 15:19:19 greg Exp $ */
/*
 * Translator definitions
 *
 *	Greg Ward
 */
#ifndef _RAD_TRANS_H_
#define _RAD_TRANS_H_
#ifdef __cplusplus
extern "C" {
#endif


#define MAXSTR		128	/* maximum input string length */

#define VOIDID		"void"	/* null modifier */

				/* qualifier list */
typedef struct {
	int	nquals;			/* number of qualifiers */
	char	**qual;			/* qualifier array */
} QLIST;
				/* identifier */
typedef struct {
	char	*name;			/* string, NULL if number */
	int	number;
} ID;
				/* identifier list */
typedef struct {
	int	nids;			/* number of ids */
	ID	*id;			/* id array */
} IDLIST;
				/* identifier range */
typedef struct {
	char	*nam;			/* string, NULL if range */
	int	min, max;		/* accepted range */
} IDMATCH;
				/* mapping rule */
typedef struct rule {
	char	*mnam;			/* material name */
	long	qflg;			/* qualifier condition flags */
	struct rule	*next;		/* next rule in mapping */
	/* followed by the IDMATCH array */
} RULEHD;
				/* useful macros */
#define doneid(idp)	if ((idp)->name != NULL) freestr((idp)->name)
#define FL(qn)		(1L<<(qn))
#define rulsiz(nq)	(sizeof(RULEHD)+(nq)*sizeof(IDMATCH))
#define idm(rp)		((IDMATCH *)((rp)+1))


	/* defined in common/savestr.c - XXX one of several declarations */
char	*savestr(const char *str);
	/* defined in trans.c */
RULEHD	*getmapping(char *file, QLIST *qlp);

extern int fgetid(ID *idp, char *dls, FILE *fp);
extern int findid(IDLIST *idl, ID *idp, int insert);
extern int matchid(ID *it, IDMATCH *im);
extern void write_quals(QLIST *qlp, IDLIST idl[], FILE *fp);


#ifdef __cplusplus
}
#endif
#endif /* _RAD_TRANS_H_ */

