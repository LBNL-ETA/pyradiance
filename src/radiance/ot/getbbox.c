#ifndef lint
static const char	RCSid[] = "$Id: getbbox.c,v 2.7 2023/02/06 22:40:21 greg Exp $";
#endif
/*
 *  getbbox.c - compute bounding box for scene files
 *
 *  Adapted from oconv.c 29 May 1991
 */

#include  "standard.h"
#include  "octree.h"
#include  "object.h"
#include  "oconv.h"

char  *progname;			/* argv[0] */

int  nowarn = 0;			/* supress warnings? */

void  (*addobjnotify[])() = {NULL};	/* new object notifier functions */

FVECT  bbmin, bbmax;			/* bounding box */

static void addobject(OBJREC	*o);



static void
addobject(			/* add object to bounding box */
	OBJREC	*o
)
{
	add2bbox(o, bbmin, bbmax);
}


int
main(		/* read object files and compute bounds */
	int  argc,
	char  **argv
)
{
	extern char  *getenv();
	int  nohead = 0;
	int  i;

	progname = argv[0];

	for (i = 1; i < argc && argv[i][0] == '-'; i++) {
		switch (argv[i][1]) {
		case 'w':
			nowarn = 1;
			continue;
		case 'h':
			nohead = 1;
			continue;
		}
		break;
	}
						/* find bounding box */
	bbmin[0] = bbmin[1] = bbmin[2] = FHUGE;
	bbmax[0] = bbmax[1] = bbmax[2] = -FHUGE;
						/* read input */
	if (i >= argc)
		readobj2(NULL, addobject);
	else
		for ( ; i < argc; i++)
			if (!strcmp(argv[i], "-"))	/* from stdin */
				readobj2(NULL, addobject);
			else				/* from file */
				readobj2(argv[i], addobject);
						/* print bounding box */
	if (!nohead)
		printf(
"     xmin      xmax      ymin      ymax      zmin      zmax\n");

	printf("%9g %9g %9g %9g %9g %9g\n", bbmin[0], bbmax[0],
			bbmin[1], bbmax[1], bbmin[2], bbmax[2]);
	quit(0);
	return 0; /* pro forma return */
}


void
quit(				/* exit program */
	int  code
)
{
	exit(code);
}


void
cputs(void)					/* interactive error */
{
	/* referenced, but not used */
}


void
wputs(				/* warning message */
	const char  *s
)
{
	if (!nowarn)
		eputs(s);
}


void
eputs(				/* put string to stderr */
	const char  *s
)
{
	static int  inln = 0;

	if (!inln++) {
		fputs(progname, stderr);
		fputs(": ", stderr);
	}
	fputs(s, stderr);
	if (*s && s[strlen(s)-1] == '\n')
		inln = 0;
}
