#!/bin/bash

# Set password
# docker run -e PASSWORD=nilm --platform=linux/amd64 --rm -p 8888:8888 -v ./notebooks:/workspace/notebooks -v ./dataset:/workspace/dataset -it nilmtk

# docker run --platform=linux/amd64 --rm -p 8888:8888 -v ./notebooks:/workspace/notebooks -v ./dataset:/workspace/dataset -it nilmtk


docker run --platform=linux/amd64 --rm -p 8888:8888 -v "C:/Rayen/Projects/actia/RAYEN-ALLAYA-NILM-LIVRABLE/2-NILMTK/scripts:/workspace/scripts" -v "C:/Rayen/Projects/actia/RAYEN-ALLAYA-NILM-LIVRABLE/2-NILMTK/notebooks:/workspace/notebooks" -v "C:/Rayen/Projects/actia/RAYEN-ALLAYA-NILM-LIVRABLE/2-NILMTK/dataset:/workspace/dataset" -it nilmtk
