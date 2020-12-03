ARG clams_version
FROM clamsproject/clams-python-ffmpeg:$clams_version
LABEL description="clams-python-opencv image is shipped with clams-python, ffmpeg, and opencv4 with their python bindings"

ARG OPENCV_VERSION=4.5.0
ARG OPENCV_PATH=/opt/opencv-${OPENCV_VERSION}
ARG OPENCV_EXTRA_PATH=/opt/opencv_contrib-${OPENCV_VERSION}

# opencv dependencies
RUN pip install numpy
RUN apt-get install -y g++ cmake make wget unzip libavcodec-dev libavformat-dev libavutil-dev libswscale-dev
# opencv download
RUN mkdir /opt || echo '/opt is already there'
WORKDIR /opt
RUN wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip -O opencv.zip 
RUN unzip -q opencv.zip
RUN rm opencv.zip
RUN wget https://github.com/opencv/opencv_contrib/archive/${OPENCV_VERSION}.zip -O opencv_contrib.zip
RUN unzip -q opencv_contrib.zip
RUN rm opencv_contrib.zip

RUN mkdir -p ${OPENCV_PATH}/build
WORKDIR ${OPENCV_PATH}/build
RUN cmake \
      -D BUILD_PYTHON_SUPPORT=ON \
      -D BUILD_DOCS=OFF \
      -D BUILD_PERF_TESTS=OFF \
      -D BUILD_TESTS=OFF \
      -D CMAKE_INSTALL_PREFIX=/usr/local \
      -D OPENCV_EXTRA_MODULES_PATH=${OPENCV_EXTRA_MODULES_PATH} \
      -D BUILD_opencv_python3=ON \
      -D BUILD_opencv_python3=OFF \
      -D PYTHON3_EXECUTABLE=$(which python3) \
      -D PYTHON_DEFAULT_EXECUTABLE=$(which python3) \
      -D BUILD_EXAMPLES=OFF \
      -D WITH_FFMPEG=ON \
      ..
RUN make -j$(nproc) && make install && ldconfig
# cleanup
WORKDIR /
RUN rm -rf ${OPENCV_PATH} ${OPENCV_EXTRA_PATH}
RUN apt-get remove -y g++ cmake make wget unzip libavcodec-dev libavformat-dev libavutil-dev libswscale-dev && apt-get autoremove -y
RUN pip install opencv-python~=4.4.0
