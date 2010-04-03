All examples in this directory have symlinks to directories and files in the
source dir.

If your system doesn't support symlinks, copy the linked files to the example
directory tou want to run before running it.

To create a new example, add a new directory then create the symlinks, if
needed:

    ln -s ../../source/lib ./lib
    ln -s ../../source/tipfy ./tipfy
    ln -s ../../source/static ./static
    ln -s ../../source/app.yaml ./app.yaml
    ln -s ../../source/main.py ./main.py
