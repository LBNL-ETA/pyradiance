#ifndef lint
static const char	RCSid[] = "$Id: fgetval.c,v 2.9 2023/12/13 20:53:27 greg Exp $";
#endif
/*
 * Read white space separated values from stream
 *
 *  External symbols declared in rtio.h
 */

#include  "rtio.h"

#include  <stdlib.h>
#include  <ctype.h>

int
fgetval(				/* get specified data word */
	FILE	*fp,
	int	ty,
	void	*vp	/* type depends on ty */
)
{
	char	wrd[64];
	char	*cp;
	int	c;
					/* elide comments (# to EOL) */
	do {
		while ((c = getc(fp)) != EOF && isspace(c))
			;
		if (c == '#')
			while ((c = getc(fp)) != EOF && c != '\n')
				;
	} while (c == '\n');
	if (c == EOF)
		return(EOF);
					/* get word */
	cp = wrd;
	do {
		*cp++ = c;
		if (cp - wrd >= sizeof(wrd))
			return(0);
	} while ((c = getc(fp)) != EOF && !isspace(c) && c != '#');
	if (c != EOF)
		ungetc(c, fp);
	*cp = '\0';
	switch (ty) {			/* check and convert it */
	case 'h':			/* short */
		if (!isint(wrd))
			return(0);
		*(short *)vp = c = atoi(wrd);
		if (*(short *)vp != c)
			return(0);
		return(1);
	case 'i':			/* integer */
		if (!isint(wrd))
			return(0);
		*(int *)vp = atoi(wrd);
		return(1);
	case 'l':			/* long */
		if (!isint(wrd))
			return(0);
		*(long *)vp = atol(wrd);
		return(1);
	case 'f':			/* float */
		if (!isflt(wrd))
			return(0);
		*(float *)vp = atof(wrd);
		return(1);
	case 'd':			/* double */
		if (!isflt(wrd))
			return(0);
		*(double *)vp = atof(wrd);
		return(1);
	case 's':			/* string */
		strcpy(vp, wrd);
		return(1);
	default:			/* unsupported type */
		return(0);
	}
}
