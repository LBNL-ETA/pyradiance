/* RCSid $Id: lookup.h,v 2.15 2011/02/18 00:40:25 greg Exp $ */
/*
 * Header file for general associative table lookup routines
 */
#ifndef _RAD_LOOKUP_H_
#define _RAD_LOOKUP_H_

#ifdef __cplusplus
extern "C" {
#endif

typedef void lut_free_t(void *p);
typedef unsigned long lut_hashf_t(const char *);
typedef int lut_keycmpf_t(const char *, const char *);

typedef struct {
	char	*key;			/* key name */
	unsigned long	hval;		/* key hash value (for efficiency) */
	char	*data;			/* pointer to client data */
} LUENT;

typedef struct {
	lut_hashf_t *hashf;		/* key hash function */
	lut_keycmpf_t *keycmp;		/* key comparison function */
	lut_free_t *freek;		/* free a key */
	lut_free_t *freed;		/* free the data */
	int	tsiz;			/* current table size */
	LUENT	*tabl;			/* table, if allocated */
	int	ndel;			/* number of deleted entries */
} LUTAB;


/*
 * The lu_init routine is called to initialize a table.  The number of
 * elements passed is not a limiting factor, as a table can grow to
 * any size permitted by memory.  However, access will be more efficient
 * if this number strikes a reasonable balance between default memory use
 * and the expected (minimum) table size.  The value returned is the
 * actual allocated table size (or zero if there was insufficient memory).
 *
 * The hashf, keycmp, freek and freed member functions must be assigned
 * separately.  If the hash value is sufficient to guarantee equality
 * between keys, then the keycmp pointer may be NULL.  Otherwise, it
 * should return 0 if the two passed keys match.  If it is not necessary
 * (or possible) to free the key and/or data values, then the freek and/or
 * freed member functions may be NULL.
 *
 * It isn't fully necessary to call lu_init to initialize the LUTAB structure.
 * If tsiz is 0, then the first call to lu_find will allocate a minimal table.
 * The LU_SINIT macro provides a convenient static declaration for character
 * string keys.
 *
 * The lu_find routine returns the entry corresponding to the given
 * key.  If the entry does not exist, the corresponding key field will
 * be NULL.  If the entry has been previously deleted but not yet freed,
 * then only the data field will be NULL.  It is the caller's
 * responsibility to (allocate and) assign the key and data fields when
 * creating a new entry.  The only case where lu_find returns NULL is when
 * the system has run out of memory.
 *
 * The lu_delete routine frees an entry's data (if any) by calling
 * the freed member function, but does not free the key field.  This
 * will be freed later during (or instead of) table reallocation.
 * It is therefore an error to reuse or do anything with the key
 * field after calling lu_delete.
 *
 * The lu_doall routine loops through every filled table entry, calling
 * the given function once on each entry.  If a NULL pointer is passed
 * for this function, then lu_doall simply returns the total number of
 * active entries.  Otherwise, it returns the sum of all the function
 * evaluations.
 *
 * The lu_done routine calls the given free function once for each
 * assigned table entry (i.e. each entry with an assigned key value).
 * The user must define these routines to free the key and the data
 * in the LU_TAB structure.  The final action of lu_done is to free the
 * allocated table itself.
 */

typedef int lut_doallf_t(const LUENT *e, void *p);

extern int	lu_init(LUTAB *tbl, int nel);
extern lut_hashf_t	lu_shash;
extern LUENT	*lu_find(LUTAB *tbl, const char *key);
extern void	lu_delete(LUTAB *tbl, const char *key);
extern int	lu_doall(const LUTAB *tbl, lut_doallf_t *f, void *p);
extern void	lu_done(LUTAB *tbl);

#define LU_SINIT(fk,fd) {lu_shash,strcmp,fk,fd,0,NULL,0}

#ifdef __cplusplus
}
#endif
#endif /* _RAD_LOOKUP_H_ */

