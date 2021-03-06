.. _introduction: 

Getting started
===============

Overview
--------

The CLAMS project has many moving parts to make various computational analysis tools talk to each other to create customized workflow pipelines. However the most important part of the project must be the apps published for the CLAMS platform. The CLAMS Python SDK will help app developers handling MMIF data format with high-level classes and methods in Python, and publishing their code as a CLAMS app that can be easily deployed to the site via CLAMS workflow engines, such as the `CLAMS appliance <https://appliance.clams.ai>`_.

A CLAMS app can be any software that performs automated contents analysis on text, audio, and/or image/video data stream. An app must use `MMIF <https://mmif.clams.ai>`_ as I/O format. When deployed into a CLAMS appliance, an app needs be running as a webapp wrapped in a docker container. In this documentation, we will explain what Python API's and HTTP API's an app must implement. 

Quick Links
-----------

* `CLAMS App Metadata jsonschema <appmetadata.jsonschema>`_. 
* `MMIF specification documentation <https://mmif.clams.ai/>`_. 
* `mmif-python API documentation <https://clams.ai/mmif-python/>`_. 

Prerequisites
-------------

* `Python <https://www.python.org>`_: ``clams-python`` requires Python 3.6 or newer. We have no plan to support `Python 2.7 <https://pythonclock.org/>`_. 
* `Docker <https://www.docker.com>`_: when deployed to the CLAMS appliance, an app must be in a docker container

Installation 
------------

``clams-python`` distribution package is `available at PyPI <https://pypi.org/project/clams-python/>`_. You can use ``pip`` to install the latest version. 

.. code-block:: bash 

    pip install clams-python

Note that installing ``clams-python`` will also install ``mmif-python`` PyPI package, which is a companion python library related to the MMIF data format.

I/O Specification 
------------------

A CLAMS app must be able to take a MMIF json as input as well as to return a MMIF json as output. MMIF is a JSON(-LD)-based open source data format. For more details and discussions, please visit the `MMIF website <https://mmif.clams.ai>`_ and the `issue tracker <https://github.com/clamsproject/mmif/issues>`_. 


``mmif`` package
^^^^^^^^^^^^^^^^^
``mmif-python`` PyPI package comes together with the installation of ``clams-python``, and with it, you can use ``mmif`` python package.

.. code-block:: python 

    import mmif
    from mmif.serialize import Mmif
    new_mmif = Mmif()
    # this will fail because an empty MMIF will fail to validate against MMIF JSON schema

Because API's of the ``mmf`` package is well documented in the `mmif-python website <http://clams.ai/mmif>`_, we won't go into more details here. Please refer to the website. 

Note on versions
^^^^^^^^^^^^^^^^
``clams-python`` is under active development, so is ``mmif-python``, which is a separate PyPI distribution package providing Python classes and methods to handle MMIF JSON string. Because of this rapid version cycles, it is possible that a MMIF file of a specific version does not work with a CLAMS app that is based on a incompatible version of ``mmif-python``. In every MMIF files, there must be the MMIF version encoded at the top of the file. Please keep in mind the versions of Python libraries you're using and their target specification version. To see the MMIF specification version targeted by the installed ``mmif-python`` package, look at ``mmif.__specver__`` variable (installing ``clams-python`` will also install ``mmif-python``).

.. code-block:: python

    import mmif
    mmif.__specver__

A CLAMS app must report which MMIF specification version it targets in its metadata (see :ref:`appmetadata`). And when an app targets a specific version, it means; 

#. the app can only process input MMIF files that are compatible with the target version.
#. the app will output MMIF files exactly versioned as the target version.

Finally, for two different specifications to be compatible to each other, their ``major`` and ``minor`` version numbers should be the same. For example, ``0.4.2`` is compatible either with ``0.4.10`` or ``0.4.0``, but is not compatible with ``0.3.0`` or ``0.7.2``. 

For more information on the relation between ``mmif-python`` versions and MMIF specification versions, or MMIF version compatibility, please take time to read our decision on the subject `here <https://mmif.clams.ai/versioning/>`_. You can also find a table with all public ``clams-python`` packages and their target MMIF versions in :ref:`target-versions`. This is a seemingly complicated issue, but also is very crucial to build CLAMS as a platform. 

CLAMS App API
-------------
A CLAMS Python app is a python class that implements and exposes two core methods; ``annotate()``, ``appmetadata()``. 

* :meth:`~clams.app.ClamsApp.appmetadata`: Returns JSON-formatted :class:`str` that contains metadata about the app. 
* :meth:`~clams.app.ClamsApp.annotate`: Takes a MMIF as the only input and processes the MMIF input, then returns serialized MMIF :class:`str`.

A good place to start writing a CLAMS app is to start with inheriting :class:`clams.app.ClamsApp`. And if you're doing so, you might want to implement two private methods instead of two public methods above. That's because the implementation of the public methods in the super class internally call these private methods respectively. 

* :meth:`~clams.app.ClamsApp._appmetadata` (using a :py:class:`~mmif.serialize.mmif.Mmif` object) and 
* :meth:`~clams.app.ClamsApp._annotate` (using a :class:`~clams.appmetadata.AppMetadata` object)  

We provide a tutorial for writing with a real world example at <:ref:`tutorial`>. We highly recommend you to go through it. 

Note on App metadata
^^^^^^^^^^^^^^^^^^^^^
App metadata is a map where important information about the app itself is stored as key-value pairs. 
See <:ref:`appmetadata`> for the specification. 
In the future the app metadata will be used for automatic generation of CLAMS App index in the :ref:`appdirectory`, as well as automatic integration to Galaxy in the appliance deployment. 

HTTP webapp
-----------
To be integrated into the CLAMS appliance, a CLAMS app needs to serve as a webapp. Once your application class is ready, you can use :class:`clams.restify.Restifier` to wrap your app as a `Flask <https://palletsprojects.com/p/flask/>`_-based web application. 

.. code-block:: python 

    from clams.app import ClamsApp
    from clams.restify import Restifier

    class AnApp(ClamsApp):
        # Implements an app that does this and that. 
        # Must implement `_appmetadata`, `_annotate` methods

    if __name__ == "__main__":
        app = AnApp()
        webapp = Restifier(app)
        webapp.run()

When running the above code, Python will start a web server and host your CLAMS app. By default the serve will listen to ``0.0.0.0:5000``, but you can adjust hostname and port number. In this webapp, ``appmetadata`` and ``annotate`` will be respectively mapped to ``GET``, and ``POST`` to the root route. Hence, for example, you can ``POST`` a MMIF file to the web app and get a response with the annotated MMIF string in the body.

In the above example, :py:meth:`clams.restify.Restifier.run` will start the webapp in debug mode on a `Werkzeug <https://palletsprojects.com/p/werkzeug/>`_ server, which is not always suitable for a production server. For a more robust server that can handle multiple requests asynchronously, you might want to use a production-ready HTTP server. In such a case you can use :py:meth:`~clams.restify.Restifier.serve_production`, which will spin up a multi-worker `Gunicorn <https://docs.gunicorn.org>`_ server. If you don't like it (for example, gunicorn does not support Windows OS), you can write your own HTTP wrapper. In the end of the day, all you need is a webapp that maps ``appmetadata`` and ``annotate`` on ``GET`` and ``POST`` requests.

Dockerization 
-------------
In addition to the HTTP service, a CLAMS app is expected to be containerized. Concretely, the appliance maker expects a CLAMS app to have a ``Dockerfile`` at the project root. Independently from being compatible with the CLAMS appliance, containerization of your app is recommended especially when your app processes video streams and dependent on complicated system-level video processing libraries (e.g. `OpenCV <https://opencv.org/>`_, `FFmpeg <https://ffmpeg.org/>`_). 

Refer to the `official documentation <https://docs.docker.com/engine/reference/builder/>`_ to learn how to write a ``Dockerfile``. To integrate to the CLAMS appliance, a dockerized CLAMS app must automatically start itself as a webapp when instantiated as a container, and listen to ``5000`` port in the container. 

We have a `public docker hub <https://hub.docker.com/orgs/clamsproject/repositories>`_, and publishing Debian-based base images to help developers write ``Dockerfile`` and save build time to install common libraries. At the moment we have a basic image with Python 3.6 and ``clams-python`` installed. We will publish more images built with commonly used video and audio processing libraries. 

CLAMS appliance integration 
----------------------------

Finally, here are requirements for an app to be appliance compatible. 

#. App code is hosted on a public git repository. 
#. App is dockerized
#. The app docker image will automatically start the app as a webapp, and listen to port 5000. 
#. ``Dockerfile`` for the dockerization is placed in the root of the git repository

To learn how to deploy your app on an appliance instance, please refer to the `appliance documentation <https://appliance.clams.ai/>`_. 

