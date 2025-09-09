FROM continuumio/anaconda3:2022.10

# Install system tools
RUN apt-get update && apt-get install -y \
    vim \
    p7zip-full \
    unzip \
 && rm -rf /var/lib/apt/lists/*

# Set up conda environment
ARG ENV_NAME=nilmtk-env
ENV CONDA_DEFAULT_ENV=${ENV_NAME}
ENV PATH /opt/conda/envs/${ENV_NAME}/bin:$PATH

# Create conda environment with Python 3.11.5 (matches nilmtk-contrib requirements)
RUN conda config --add channels conda-forge && \
    conda create -y -n ${ENV_NAME} python=3.11.5 && \
    conda clean -a

# Activate env and install dependencies
COPY files/requirements.nilmtk_contrib.txt /tmp/

RUN /opt/conda/envs/${ENV_NAME}/bin/pip install --upgrade pip && \
    /opt/conda/envs/${ENV_NAME}/bin/pip install -r /tmp/requirements.nilmtk_contrib.txt && \
    /opt/conda/envs/${ENV_NAME}/bin/pip install --no-deps git+https://github.com/nilmtk/nilmtk@0.4.3 && \
    /opt/conda/envs/${ENV_NAME}/bin/pip install --no-deps git+https://github.com/nilmtk/nilm_metadata@0.2.4 && \
    /opt/conda/envs/${ENV_NAME}/bin/pip install --no-deps git+https://github.com/nilmtk/nilmtk-contrib

# Overwrite custom disaggregation files
COPY files/nilmtk-contrib/nilmtk_contrib/disaggregate/ /opt/conda/envs/${ENV_NAME}/lib/python3.11/site-packages/nilmtk_contrib/disaggregate/

# Install Jupyter kernel inside environment
RUN /opt/conda/envs/${ENV_NAME}/bin/python -m ipykernel install --user --name ${ENV_NAME} --display-name "Python3.11 (nilmtk-env)"

# Copy Jupyter config
ENV HOME=/root
RUN mkdir -p $HOME/.jupyter
COPY files/jupyter_notebook_config.py $HOME/.jupyter/

WORKDIR /workspace

EXPOSE 8888

CMD ["conda", "run", "--no-capture-output", "-n", "nilmtk-env", "jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--allow-root", "--no-browser", "--NotebookApp.token=''"]