Tipfy Installation
==================
Tipfy is a small but powerful framework made specifically for Google App
Engine. Here are some quick instructions to get started with it. More details
are available in tipfy's wiki:

  http://www.tipfy.org/wiki/guide/installation/

Our goal gere is to provide a smooth installation process so that you can see
a tipfy application up and running in a few minutes. If you have any problems,
please post a message to the discussion group:

  http://groups.google.com/group/tipfy


All-in-one installation
-----------------------
If you downloaded the all-in-one pack, all you need to do is to start the
development server pointing to the /app dir inside the uncompressed archive:

- Run the dev_appserver tool from the App Engine SDK (or the App Engine
  Launcher) pointing to the /app directory inside the uncompressed archive:

    dev_appserver.py /path/to/project/app

- Open a browser and test the URLs:

    http://localhost:8080/
    http://localhost:8080/pretty

You should see a Hello, World! message. If you do, that's all. Now you have
a project environment to start developing your app.


Do-it-yourself installation
---------------------------
If you downloaded the do-it-yourself pack, you need to first install the
needed libraries before running de development server. Here's how:

- Access the project directory and call the bootstrap script using your
  Python 2.5 interpreter. We pass the command --distribute because it
  is preferable to the default setuptools. This will prepare buildout to run:

    python bootstrap.py --distribute

- Build the project calling bin/buildout. This will download and setup
  tipfy and all libraries inside the /app directory. It may take a while.

    bin/buildout

- Start the development server calling bin/dev_appserver. It will use the
  application from /app by default:

    bin/dev_appserver

- Open a browser and test the URLs:

    http://localhost:8080/
    http://localhost:8080/pretty

You should see a Hello, World! message. If you do, that's all. Now you have
a project environment to start developing your app.
