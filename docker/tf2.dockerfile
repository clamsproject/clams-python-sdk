ARG clams_version
FROM clamsproject/clams-python:$clams_version
LABEL description="clams-python-tf2 image is shipped with clams-python and tensorflow2"

RUN pip install tensorflow==2.*
