#-------------------------------------------------------------------------
#
# Makefile--
#    Makefile for entity_sync
#
# By default, this builds against an existing PostgreSQL installation
# (the one identified by whichever pg_config is first in your path).
# Within a configured source tree, you can say "gmake NO_PGXS=1 all"
# to build using the surrounding source tree.
#
# copied from:
#    $PostgreSQL: pgsql/src/tutorial/Makefile,v 1.21 2008/04/07 14:15:58 petere Exp $
#
# just run:
# $ make
# to build
#-------------------------------------------------------------------------

MODULES = entity_sync
DATA_built = entity_sync.sql

ifdef NO_PGXS
subdir = src/tutorial
top_builddir = ../..
include $(top_builddir)/src/Makefile.global
include $(top_srcdir)/src/makefiles/pgxs.mk
else
PG_CONFIG = pg_config
PGXS := $(shell $(PG_CONFIG) --pgxs)
include $(PGXS)
endif

%.sql: %.source
	rm -f $@; \
	C=`pwd`; \
	sed -e "s:_OBJWD_:$$C:g" < $< > $@
