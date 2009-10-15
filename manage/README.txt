Tipfy Management Utilities
==========================

* Template compilation
  To boost performance, templates can be precompiled to Python code. For
  convenience, when in development only the non-compiled templates are used.

  To precompile templates, use the manage script:

  $ manage.py precompile /path/to/project

  It'll compile all templates located in /path/to/project/templates to
  /path/to/project/templates_compiled.
