#!/bin/bash

# docker run --platform=linux/amd64 --rm -v ./scripts:/workspace/scripts -v ./dataset:/workspace/dataset -it nilmtk /bin/bash
docker run --platform=linux/amd64 --rm -v "C:/Rayen/Projects/actia/RAYEN-ALLAYA-NILM-LIVRABLE/NILMTK/scripts:/workspace/scripts" -v "C:/Rayen/Projects/actia/RAYEN-ALLAYA-NILM-LIVRABLE/NILMTK/dataset:/workspace/dataset" -it nilmtk /bin/bash