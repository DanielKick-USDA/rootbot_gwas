#!/usr/bin/bash
singularity exec \
  --bind run:/run \
  --bind var-lib-rstudio-server:/var/lib/rstudio-server \
  --bind database.conf:/etc/rstudio/database.conf \
  --bind home:/home \
  rstudio.sif \
  /usr/lib/rstudio-server/bin/rserver \
  --www-address=127.0.0.1 \
  --www-port=8700 \
  --server-user=rstudio
