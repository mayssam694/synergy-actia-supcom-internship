

### How to use

## Build the Docker image
From the project root (where the `Dockerfile` is located):

```bash
docker build -t myapp:latest .


####Start the container in detached mode and map the application port (example:8888):

docker run -d --name myapp -p 8888:8888 myapp:latest
