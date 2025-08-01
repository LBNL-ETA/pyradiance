#ifndef lint
static const char	RCSid[] = "$Id: rtmain.c,v 2.61 2025/06/20 16:34:23 greg Exp $";
#endif
/*
 *  rtmain.c - main for rtrace per-ray calculation program
 */

#include "copyright.h"

#include  <signal.h>

#include  "platform.h"
#include  "rtprocess.h" /* getpid() */
#include  "resolu.h"
#include  "ray.h"
#include  "func.h"
#include  "source.h"
#include  "ambient.h"
#include  "random.h"
#include  "pmapray.h"
					/* persistent processes define */
#ifdef  F_SETLKW
#define  PERSIST	1		/* normal persist */
#define  PARALLEL	2		/* parallel persist */
#define  PCHILD		3		/* child of normal persist */
#endif

char  *sigerr[NSIG];			/* signal error messages */
char  *errfile = NULL;			/* error output file */

int  nproc = 1;				/* number of processes */

extern int  setrtoutput(void);		/* set output values */

int  inform = 'a';			/* input format */
int  outform = 'a';			/* output format */
char  *outvals = "v";			/* output specification */

int  hresolu = 0;			/* horizontal (scan) size */
int  vresolu = 0;			/* vertical resolution */

extern int  castonly;			/* only doing ray-casting? */

int  imm_irrad = 0;			/* compute immediate irradiance? */
int  lim_dist = 0;			/* limit distance? */

#ifndef	MAXMODLIST
#define	MAXMODLIST	1024		/* maximum modifiers we'll track */
#endif

extern void  (*addobjnotify[])();	/* object notification calls */
extern void  tranotify(OBJECT obj);

char  *tralist[MAXMODLIST];		/* list of modifers to trace (or no) */
int  traincl = -1;			/* include == 1, exclude == 0 */

double  (*sens_curve)(const SCOLOR scol) = NULL;	/* spectral conversion for 1-channel */
double  out_scalefactor = 1;		/* output calibration scale factor */
RGBPRIMP  out_prims = stdprims;		/* output color primitives (NULL if spectral) */
static RGBPRIMS  our_prims;		/* private output color primitives */

static int  loadflags = ~IO_FILES;	/* what to load from octree */

static void onsig(int  signo);
static void sigdie(int  signo, char  *msg);
static void printdefaults(void);

#ifdef PERSIST
#define RTRACE_FEATURES	"Persist\nParallelPersist\nMultiprocessing\n" \
			"IrradianceCalc\nImmediateIrradiance\nDistanceLimiting\n" \
			"ParticipatingMedia=Mist\n" \
			"HessianAmbientCache\nAmbientAveraging\n" \
			"AmbientValueSharing\nAdaptiveShadowTesting\n" \
			"InputFormats=a,f,d\nOutputFormats=a,f,d,c\n" \
			"Outputs=o,d,v,V,w,W,l,L,c,p,n,N,s,m,M,r,x,R,X,~\n" \
			"OutputCS=RGB,XYZ,Y,S,M,prims,spec\n"
#else
#define RTRACE_FEATURES	"IrradianceCalc\nIrradianceCalc\nDistanceLimiting\n" \
			"ParticipatingMedia=Mist\n" \
			"HessianAmbientCache\nAmbientAveraging\n" \
			"AmbientValueSharing\nAdaptiveShadowTesting\n" \
			"InputFormats=a,f,d\nOutputFormats=a,f,d,c\n" \
			"Outputs=o,d,v,V,w,W,l,L,c,p,n,N,s,m,M,r,x,R,X,~\n" \
			"OutputCS=RGB,XYZ,Y,S,M,prims,spec\n"
#endif


int
main(int  argc, char  *argv[])
{
#define	 check(ol,al)		if (argv[i][ol] || \
				badarg(argc-i-1,argv+i+1,al)) \
				goto badopt
#define	 check_bool(olen,var)		switch (argv[i][olen]) { \
				case '\0': var = !var; break; \
				case 'y': case 'Y': case 't': case 'T': \
				case '+': case '1': var = 1; break; \
				case 'n': case 'N': case 'f': case 'F': \
				case '-': case '0': var = 0; break; \
				default: goto badopt; }
	extern char  *octname;
	int  persist = 0;
	char  *octnm = NULL;
	char  **tralp = NULL;
	int  duped1 = -1;
	int  rval;
	int  i;
					/* global program name */
	progname = argv[0] = fixargv0(argv[0]);
					/* feature check only? */
	strcat(RFeatureList, RTRACE_FEATURES);
	if (argc > 1 && !strcmp(argv[1], "-features"))
		return feature_status(argc-2, argv+2);
					/* initialize calcomp routines */
	initfunc();
					/* add trace notify function */
	for (i = 0; addobjnotify[i] != NULL; i++)
		;
	addobjnotify[i] = tranotify;
					/* option city */
	for (i = 1; i < argc; i++) {
						/* expand arguments */
		while ((rval = expandarg(&argc, &argv, i)) > 0)
			;
		if (rval < 0) {
			sprintf(errmsg, "cannot expand '%s'", argv[i]);
			error(SYSTEM, errmsg);
		}
		if (argv[i] == NULL || argv[i][0] != '-')
			break;			/* break from options */
		if (!strcmp(argv[i], "-version")) {
			puts(VersionID);
			quit(0);
		}
		if (!strcmp(argv[i], "-defaults") ||
				!strcmp(argv[i], "-help")) {
			printdefaults();
			quit(0);
		}
		rval = getrenderopt(argc-i, argv+i);
		if (rval >= 0) {
			i += rval;
			continue;
		}
		switch (argv[i][1]) {
		case 'n':				/* number of cores */
			check(2,"i");
			nproc = atoi(argv[++i]);
			if (nproc <= 0)
				error(USER, "bad number of processes");
			break;
		case 'x':				/* x resolution */
			check(2,"i");
			hresolu = atoi(argv[++i]);
			break;
		case 'y':				/* y resolution */
			check(2,"i");
			vresolu = atoi(argv[++i]);
			break;
		case 'w':				/* warnings & spectral */
			rval = erract[WARNING].pf != NULL;
			check_bool(2,rval);
			if (rval) erract[WARNING].pf = wputs;
			else erract[WARNING].pf = NULL;
			break;
		case 'e':				/* error file */
			check(2,"s");
			errfile = argv[++i];
			break;
		case 'l':				/* limit distance */
			if (argv[i][2] != 'd')
				goto badopt;
			check_bool(3,lim_dist);
			break;
		case 'I':				/* immed. irradiance */
			check_bool(2,imm_irrad);
			break;
		case 'f':				/* format i/o */
			switch (argv[i][2]) {
			case 'a':				/* ascii */
			case 'f':				/* float */
			case 'd':				/* double */
				inform = argv[i][2];
				break;
			default:
				goto badopt;
			}
			switch (argv[i][3]) {
			case '\0':
				outform = inform;
				break;
			case 'a':				/* ascii */
			case 'f':				/* float */
			case 'd':				/* double */
			case 'c':				/* color */
				check(4,"");
				outform = argv[i][3];
				break;
			default:
				goto badopt;
			}
			break;
		case 'o':				/* output */
			outvals = argv[i]+2;
			break;
		case 'h':				/* header output */
			rval = loadflags & IO_INFO;
			check_bool(2,rval);
			loadflags = rval ? loadflags | IO_INFO :
					loadflags & ~IO_INFO;
			break;
		case 't':				/* trace */
			switch (argv[i][2]) {
			case 'i':				/* include */
			case 'I':
				check(3,"s");
				if (traincl != 1) {
					traincl = 1;
					tralp = tralist;
				}
				if (argv[i][2] == 'I') {	/* file */
					rval = wordfile(tralp, MAXMODLIST-(tralp-tralist),
					getpath(argv[++i],getrlibpath(),R_OK));
					if (rval < 0) {
						sprintf(errmsg,
				"cannot open trace include file \"%s\"",
								argv[i]);
						error(SYSTEM, errmsg);
					}
					tralp += rval;
				} else {
					*tralp++ = argv[++i];
					*tralp = NULL;
				}
				break;
			case 'e':				/* exclude */
			case 'E':
				check(3,"s");
				if (traincl != 0) {
					traincl = 0;
					tralp = tralist;
				}
				if (argv[i][2] == 'E') {	/* file */
					rval = wordfile(tralp, MAXMODLIST-(tralp-tralist),
					getpath(argv[++i],getrlibpath(),R_OK));
					if (rval < 0) {
						sprintf(errmsg,
				"cannot open trace exclude file \"%s\"",
								argv[i]);
						error(SYSTEM, errmsg);
					}
					tralp += rval;
				} else {
					*tralp++ = argv[++i];
					*tralp = NULL;
				}
				break;
			default:
				goto badopt;
			}
			break;
		case 'p':				/* value output */
			switch (argv[i][2]) {
			case 'R':			/* standard RGB output */
				if (strcmp(argv[i]+2, "RGB"))
					goto badopt;
				out_prims = stdprims;
				out_scalefactor = 1;
				sens_curve = NULL;
				break;
			case 'X':			/* XYZ output */
				if (strcmp(argv[i]+2, "XYZ"))
					goto badopt;
				out_prims = xyzprims;
				out_scalefactor = WHTEFFICACY;
				sens_curve = NULL;
				break;
			case 'c': {
				int	j;
				check(3,"ffffffff");
				rval = 0;
				for (j = 0; j < 8; j++) {
					our_prims[0][j] = atof(argv[++i]);
					rval |= fabs(our_prims[0][j]-stdprims[0][j]) > .001;
				}
				if (rval) {
					if (!colorprimsOK(our_prims))
						error(USER, "illegal primary chromaticities");
					out_prims = our_prims;
				} else
					out_prims = stdprims;
				out_scalefactor = 1;
				sens_curve = NULL;
				} break;
			case 'Y':			/* photopic response */
				if (argv[i][3])
					goto badopt;
				sens_curve = scolor_photopic;
				out_scalefactor = WHTEFFICACY;
				break;
			case 'S':			/* scotopic response */
				if (argv[i][3])
					goto badopt;
				sens_curve = scolor_scotopic;
				out_scalefactor = WHTSCOTOPIC;
				break;
			case 'M':			/* melanopic response */
				if (argv[i][3])
					goto badopt;
				sens_curve = scolor_melanopic;
				out_scalefactor = WHTMELANOPIC;
				break;
			default:
				goto badopt;
			}
			break;
#if MAXCSAMP>3
		case 'c':				/* output spectral results */
			if (argv[i][2] != 'o')
				goto badopt;
			rval = (out_prims == NULL) & (sens_curve == NULL);
			check_bool(3,rval);
			if (rval) {
				out_prims = NULL;
				sens_curve = NULL;
			} else if (out_prims == NULL)
				out_prims = stdprims;
			break;
#endif
#ifdef  PERSIST
		case 'P':				/* persist file */
			if (argv[i][2] == 'P') {
				check(3,"s");
				persist = PARALLEL;
			} else {
				check(2,"s");
				persist = PERSIST;
			}
			persistfile(argv[++i]);
			break;
#endif
		default:
			goto badopt;
		}
	}
					/* set/check spectral sampling */
	rval = setspectrsamp(CNDX, WLPART);
	if (rval < 0)
		error(USER, "unsupported spectral sampling");
	if (sens_curve != NULL)
		out_prims = NULL;
	else if (out_prims != NULL) {
		if (!rval)
			error(WARNING, "spectral range incompatible with color output");
	} else if (NCSAMP == 3)
		out_prims = stdprims;	/* 3 samples do not a spectrum make */
	if (nproc > 1 && persist)
		error(USER, "multiprocessing incompatible with persist file");
					/* initialize object types */
	initotypes();
					/* initialize urand */
	reset_random();
					/* set up signal handling */
	sigdie(SIGINT, "Interrupt");
#ifdef SIGHUP
	sigdie(SIGHUP, "Hangup");
#endif
	sigdie(SIGTERM, "Terminate");
#ifdef SIGPIPE
	sigdie(SIGPIPE, "Broken pipe");
#endif
#ifdef SIGALRM
	sigdie(SIGALRM, "Alarm clock");
#endif
#ifdef	SIGXCPU
	sigdie(SIGXCPU, "CPU limit exceeded");
	sigdie(SIGXFSZ, "File size exceeded");
#endif
					/* open error file */
	if (errfile != NULL) {
		if (freopen(errfile, "a", stderr) == NULL)
			quit(2);
		fprintf(stderr, "**************\n*** PID %5d: ",
				getpid());
		printargs(argc, argv, stderr);
		putc('\n', stderr);
		fflush(stderr);
	}
#ifdef	NICE
	nice(NICE);			/* lower priority */
#endif
					/* get octree */
	if (i == argc)
		octnm = NULL;
	else if (i == argc-1)
		octnm = argv[i];
	else
		goto badopt;
	if (octnm == NULL)
		error(USER, "missing octree argument");
					/* set up output */
#ifdef  PERSIST
	if (persist) {
		duped1 = dup(fileno(stdout));	/* don't lose our output */
		openheader();
	}
#endif
	if (outform != 'a')
		SET_FILE_BINARY(stdout);
	rval = setrtoutput();
	octname = savqstr(octnm);
	readoct(octname, loadflags, &thescene, NULL);
	nsceneobjs = nobjects;

	if (loadflags & IO_INFO) {	/* print header */
		printargs(i, argv, stdout);
		printf("SOFTWARE= %s\n", VersionID);
		fputnow(stdout);
		if (rval > 0)		/* saved from setrtoutput() call */
			fputncomp(rval, stdout);
		if (NCSAMP > 3)
			fputwlsplit(WLPART, stdout);
		if ((out_prims != stdprims) & (out_prims != NULL))
			fputprims(out_prims, stdout);
		if ((outform == 'f') | (outform == 'd'))
			fputendian(stdout);
		fputformat(formstr(outform), stdout);
		fputc('\n', stdout);	/* end of header */
	}

	if (!castonly) {	/* any actual ray traversal to do? */

		ray_init_pmap();	/* PMAP: set up & load photon maps */
		
		marksources();		/* find and mark sources */

		setambient();		/* initialize ambient calculation */
	} else
		distantsources();	/* else mark only distant sources */

	fflush(stdout);			/* in case we're duplicating header */

#ifdef  PERSIST
	if (persist) {
						/* reconnect stdout */
		dup2(duped1, fileno(stdout));
		close(duped1);
		if (persist == PARALLEL) {	/* multiprocessing */
			cow_memshare();		/* preloads scene */
			while ((rval=fork()) == 0) {	/* keep on forkin' */
				pflock(1);
				pfhold();
				ambsync();		/* load new values */
			}
			if (rval < 0)
				error(SYSTEM, "cannot fork child for persist function");
			pfdetach();		/* parent will run then exit */
		}
	}
runagain:
	if (persist)
		dupheader();			/* send header to stdout */
#endif
					/* trace rays */
	rtrace(NULL, nproc);
					/* flush ambient file */
	ambsync();
#ifdef  PERSIST
	if (persist == PERSIST) {	/* first run-through */
		if ((rval=fork()) == 0) {	/* child loops until killed */
			pflock(1);
			persist = PCHILD;
		} else {			/* original process exits */
			if (rval < 0)
				error(SYSTEM, "cannot fork child for persist function");
			pfdetach();		/* parent exits */
		}
	}
	if (persist == PCHILD) {	/* wait for a signal then go again */
		pfhold();
		raynum = nrays = 0;		/* reinitialize */
		goto runagain;
	}
#endif

	ray_done_pmap();           /* PMAP: free photon maps */
	
	quit(0);

badopt:
	sprintf(errmsg, "command line error at '%s'", argv[i]);
	error(USER, errmsg);
	return 1; /* pro forma return */

#undef	check
#undef	check_bool
}


void
wputs(				/* warning output function */
	const char	*s
)
{
	int  lasterrno = errno;
	if (erract[WARNING].pf == NULL)
		return;		/* called by calcomp or someone */
	eputs(s);
	errno = lasterrno;
}


void
eputs(				/* put string to stderr */
	const char  *s
)
{
	static int  midline = 0;

	if (!*s)
		return;
	if (!midline++) {
		fputs(progname, stderr);
		fputs(": ", stderr);
	}
	fputs(s, stderr);
	if (s[strlen(s)-1] == '\n') {
		fflush(stderr);
		midline = 0;
	}
}


static void
onsig(				/* fatal signal */
	int  signo
)
{
	static int  gotsig = 0;

	if (gotsig++)			/* two signals and we're gone! */
		_exit(signo);

#ifdef SIGALRM
	alarm(15);			/* allow 15 seconds to clean up */
	signal(SIGALRM, SIG_DFL);	/* make certain we do die */
#endif
	eputs("signal - ");
	eputs(sigerr[signo]);
	eputs("\n");
	quit(3);
}


static void
sigdie(			/* set fatal signal */
	int  signo,
	char  *msg
)
{
	if (signal(signo, onsig) == SIG_IGN)
		signal(signo, SIG_IGN);
	sigerr[signo] = msg;
}


static void
printdefaults(void)			/* print default values to stdout */
{
	char  *cp;

	printf(erract[WARNING].pf != NULL ?
			"-w+\t\t\t\t# warning messages on\n" :
			"-w-\t\t\t\t# warning messages off\n");
	if (imm_irrad)
		printf("-I+\t\t\t\t# immediate irradiance on\n");
	printf("-n %-2d\t\t\t\t# number of rendering processes\n", nproc);
	printf("-x %-9d\t\t\t# %s\n", hresolu,
			vresolu && hresolu ? "x resolution" : "flush interval");
	printf("-y %-9d\t\t\t# y resolution\n", vresolu);
	printf(lim_dist ? "-ld+\t\t\t\t# limit distance on\n" :
			"-ld-\t\t\t\t# limit distance off\n");
	printf(loadflags & IO_INFO ? "-h+\t\t\t\t# output header\n" :
			"-h-\t\t\t\t# no header\n");
	printf("-f%c%c\t\t\t\t# format input/output = %s/%s\n",
			inform, outform, formstr(inform), formstr(outform));
	printf("-o%-9s\t\t\t# output", outvals);
	for (cp = outvals; *cp; cp++)
		switch (*cp) {
		case 't': case 'T': printf(" trace"); break;
		case 'o': printf(" origin"); break;
		case 'd': printf(" direction"); break;
		case 'r': printf(" reflect_contrib"); break;
		case 'R': printf(" reflect_length"); break;
		case 'x': printf(" unreflect_contrib"); break;
		case 'X': printf(" unreflect_length"); break;
		case 'v': printf(" value"); break;
		case 'V': printf(" contribution"); break;
		case 'l': printf(" length"); break;
		case 'L': printf(" first_length"); break;
		case 'p': printf(" point"); break;
		case 'n': printf(" normal"); break;
		case 'N': printf(" unperturbed_normal"); break;
		case 's': printf(" surface"); break;
		case 'w': printf(" weight"); break;
		case 'W': printf(" coefficient"); break;
		case 'm': printf(" modifier"); break;
		case 'M': printf(" material"); break;
		case '~': printf(" tilde"); break;
		}
	fputc('\n', stdout);
	if (sens_curve == scolor_photopic)
		printf("-pY\t\t\t\t# photopic output\n");
	else if (sens_curve == scolor_scotopic)
		printf("-pS\t\t\t\t# scotopic output\n");
	else if (sens_curve == scolor_melanopic)
		printf("-pM\t\t\t\t# melanopic output\n");
	else if (out_prims == stdprims)
		printf("-pRGB\t\t\t\t# standard RGB color output\n");
	else if (out_prims == xyzprims)
		printf("-pXYZ\t\t\t\t# CIE XYZ color output\n");
	else if (out_prims != NULL)
		printf("-pc %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f\t# output color primaries and white point\n",
				out_prims[RED][0], out_prims[RED][1],
				out_prims[GRN][0], out_prims[GRN][1],
				out_prims[BLU][0], out_prims[BLU][1],
				out_prims[WHT][0], out_prims[WHT][1]);
	if ((sens_curve == NULL) & (NCSAMP > 3))
		printf(out_prims != NULL ? "-co-\t\t\t\t# output tristimulus colors\n" :
				"-co+\t\t\t\t# output spectral values\n");
	print_rdefaults();
}
