Tipfy Management Utilities
==========================

Translations
------------
To extract and compile translations:

1. Extract all translations. Here we pass two directories to extract:

   pybabel extract -F ./babel.cfg -o messages.pot /path/to/files/to/be/extracted /path/to/files/to/be/extracted2

2. Initialize directories for all translations, using the messages.pot we created in step 1:

   pybabel init -l en_US -d /path/to/locale/dir -i messages.pot
   pybabel init -l es_ES -d /path/to/locale/dir -i messages.pot
   pybabel init -l pt_BR -d /path/to/locale/dir -i messages.pot
   ...

3. After all locales are translated, compile them:

   pybabel compile -f -d /path/to/locale/dir


That's it. Later, if translations change, repeat step 1 and update them using this:


4. pybabel update -l pt_BR -d /path/to/locale/dir -i messages.pot
