docker run --platform=linux/amd64 --rm -p 8888:8888 -v "%CD%/scripts:/workspace/scripts" -v "%CD%/notebooks:/workspace/notebooks" -v "%CD%/dataset:/workspace/dataset" -it nilmtk
