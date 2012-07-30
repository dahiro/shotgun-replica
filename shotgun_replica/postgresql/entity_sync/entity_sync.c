/*
 * $PostgreSQL: pgsql/src/tutorial/complex.c,v 1.15 2009/06/11 14:49:15 momjian Exp $
 *
 ******************************************************************************
 This file contains routines that can be bound to a Postgres backend and
 called by the backend in the process of processing queries.  The calling
 format for these routines is dictated by Postgres architecture.
 ******************************************************************************/
#include "postgres.h"
#include "fmgr.h"
#include "executor/executor.h"  /* for GetAttributeByName() */

PG_MODULE_MAGIC

;

const int UNKNOWN = -1;

int compare_int(int a, int b);
int compare_int_noequal(int a, int b, int dflt);

Datum entity_sync_abs_lt(PG_FUNCTION_ARGS);
Datum entity_sync_abs_le(PG_FUNCTION_ARGS);
Datum entity_sync_abs_eq(PG_FUNCTION_ARGS);
Datum entity_sync_abs_ne(PG_FUNCTION_ARGS);
Datum entity_sync_abs_ge(PG_FUNCTION_ARGS);
Datum entity_sync_abs_gt(PG_FUNCTION_ARGS);
Datum entity_sync_abs_cmp(PG_FUNCTION_ARGS);

int compare_int(int a, int b) {
	if (a < b)
		return -1;
	if (a > b)
		return 1;
	return 0;
}

int compare_int_noequal(int a, int b, int dflt) {
	if (a < b)
		return -1;
	if (a > b)
		return 1;
	return dflt;
}

static int entity_sync_abs_cmp_internal(HeapTupleHeader *a, HeapTupleHeader *b) {
	bool isnull;
	char* type_a, *type_b;
	Datum type_a_datum, type_b_datum, id_a_datum, id_b_datum, remote_id_a_datum,
			remote_id_b_datum;
	VarChar *type_a_varchar, *type_b_varchar;
	int32 id_a, id_b;
	int32 remote_id_a, remote_id_b;
	int typeCmp;
	int siz_a, siz_b;

	type_a_datum = GetAttributeByName(*a, "type", &isnull);
	type_a_varchar = DatumGetVarCharPCopy(type_a_datum);
	siz_a = VARSIZE(type_a_varchar) - VARHDRSZ;
	type_a = (char *) VARDATA(type_a_varchar);

	id_a_datum = GetAttributeByName(*a, "id", &isnull);
	id_a = DatumGetInt32(id_a_datum);

	remote_id_a_datum = GetAttributeByName(*a, "remote_id", &isnull);
	remote_id_a = DatumGetInt32(remote_id_a_datum);

	type_b_datum = GetAttributeByName(*b, "type", &isnull);
	type_b_varchar = DatumGetVarCharPCopy(type_b_datum);
	siz_b = VARSIZE(type_b_varchar) - VARHDRSZ;
	type_b = (char *) VARDATA(type_b_varchar);

	id_b_datum = GetAttributeByName(*b, "id", &isnull);
	id_b = DatumGetInt32(id_b_datum);

	remote_id_b_datum = GetAttributeByName(*b, "remote_id", &isnull);
	remote_id_b = DatumGetInt32(remote_id_b_datum);

//	ereport(WARNING,
//			(errcode(ERRCODE_WARNING), errmsg("sizes\n  %d \"%s\"\n  %d \"%s\"", siz_a, type_a, siz_b, type_b)));

	if (siz_a == siz_b)
		typeCmp = strncmp(type_a, type_b, siz_a);
	else {
		if (siz_a > siz_b)
			typeCmp = strncmp(type_a, type_b, siz_b);
		else
			typeCmp = strncmp(type_a, type_b, siz_a);

		if (typeCmp == 0) {
			if (siz_a > siz_b)
				return 1;
			else
				return -1;
		}

		return typeCmp;
	}

//	ereport(WARNING,
//			(errcode(ERRCODE_WARNING), errmsg("entity_a: %d \"%s\", %d\nentity_b: %d \"%s\", %d\n%d",
//					siz_a, type_a, id_a, siz_b, type_b, id_b, typeCmp)));
	

	if (typeCmp == 0) {
		if (remote_id_a != UNKNOWN && remote_id_b != UNKNOWN)
			return compare_int(remote_id_a, remote_id_b);
		if (id_a != UNKNOWN && id_b != UNKNOWN)
			return compare_int(id_a, id_b);
		if (id_a != UNKNOWN && remote_id_b != UNKNOWN)
			return compare_int_noequal(id_a, remote_id_b, -1);
		if (remote_id_a != UNKNOWN && id_b != UNKNOWN)
			return compare_int_noequal(remote_id_a, id_b, 1);
	}
	return typeCmp;
}

PG_FUNCTION_INFO_V1(entity_sync_abs_lt);

Datum entity_sync_abs_lt(PG_FUNCTION_ARGS) {
	HeapTupleHeader a = PG_GETARG_HEAPTUPLEHEADER(0);
	HeapTupleHeader b = PG_GETARG_HEAPTUPLEHEADER(1);

	PG_RETURN_BOOL(entity_sync_abs_cmp_internal(&a, &b) < 0);
}

PG_FUNCTION_INFO_V1(entity_sync_abs_le);

Datum entity_sync_abs_le(PG_FUNCTION_ARGS) {
	HeapTupleHeader a = PG_GETARG_HEAPTUPLEHEADER(0);
	HeapTupleHeader b = PG_GETARG_HEAPTUPLEHEADER(1);

	PG_RETURN_BOOL(entity_sync_abs_cmp_internal(&a, &b) <= 0);
}

PG_FUNCTION_INFO_V1(entity_sync_abs_ne);

Datum entity_sync_abs_ne(PG_FUNCTION_ARGS) {
	HeapTupleHeader a = PG_GETARG_HEAPTUPLEHEADER(0);
	HeapTupleHeader b = PG_GETARG_HEAPTUPLEHEADER(1);

	PG_RETURN_BOOL(entity_sync_abs_cmp_internal(&a, &b) != 0);
}

PG_FUNCTION_INFO_V1(entity_sync_abs_eq);

Datum entity_sync_abs_eq(PG_FUNCTION_ARGS) {
	HeapTupleHeader a = PG_GETARG_HEAPTUPLEHEADER(0);
	HeapTupleHeader b = PG_GETARG_HEAPTUPLEHEADER(1);

	PG_RETURN_BOOL(entity_sync_abs_cmp_internal(&a, &b) == 0);
}

PG_FUNCTION_INFO_V1(entity_sync_abs_ge);

Datum entity_sync_abs_ge(PG_FUNCTION_ARGS) {
	HeapTupleHeader a = PG_GETARG_HEAPTUPLEHEADER(0);
	HeapTupleHeader b = PG_GETARG_HEAPTUPLEHEADER(1);

	PG_RETURN_BOOL(entity_sync_abs_cmp_internal(&a, &b) >= 0);
}

PG_FUNCTION_INFO_V1(entity_sync_abs_gt);

Datum entity_sync_abs_gt(PG_FUNCTION_ARGS) {
	HeapTupleHeader a = PG_GETARG_HEAPTUPLEHEADER(0);
	HeapTupleHeader b = PG_GETARG_HEAPTUPLEHEADER(1);

	PG_RETURN_BOOL(entity_sync_abs_cmp_internal(&a, &b) > 0);
}

PG_FUNCTION_INFO_V1(entity_sync_abs_cmp);

Datum entity_sync_abs_cmp(PG_FUNCTION_ARGS) {
	HeapTupleHeader a = PG_GETARG_HEAPTUPLEHEADER(0);
	HeapTupleHeader b = PG_GETARG_HEAPTUPLEHEADER(1);

	PG_RETURN_INT32(entity_sync_abs_cmp_internal(&a, &b));
}

