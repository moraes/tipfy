All examples in this directory have symlinks to directories and files in the
source dir.

If your system doesn't support symlinks, copy the following files to the example
directory before running them:

    /source/lib
    /source/tipfy
    /source/app.yaml
    /source/main.py

To create a new example, add a new directory then create the symlinks:

    ln -s ../../source/tipfy/ ./tipfy
    ln -s ../../source/lib/ ./lib
    ln -s ../../source/main.py ./main.py
    ln -s ../../source/app.yaml ./app.yaml
