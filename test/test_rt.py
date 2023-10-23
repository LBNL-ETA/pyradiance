from pyradiance import lib


lib.LIBRC.initotypes()
lib.LIBRC.readoct(octname, loadflags, &thescene, NULL)

lib.LIBRC.ray_init_pmap()
lib.LIBRC.marksources()
lib.LIBRC.setambient()

lib.LIBRC.rtrace
