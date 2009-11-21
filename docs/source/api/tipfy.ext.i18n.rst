tipfy.ext.i18n
==============
.. module:: tipfy.ext.i18n

.. toctree::
   :maxdepth: 5

.. _Babel: http://babel.edgewall.org/
.. _gae-pytz: http://code.google.com/p/gae-pytz/
.. _Kay: http://code.google.com/p/kay-framework/

This module provides internationalization utilities: a translations store,
a middleware to set locale for the current request, functions to manipulate
dates according to timezones or translate and localize strings and dates.

Tipfy uses `Babel`_ to manage translations of strings and localization of dates
and times, and `gae-pytz`_ to handle timezones.


Middlewares
-----------
.. autoclass:: I18nMiddleware


Translation functions
---------------------
These functions provide functionality to translate strings in templates or in
the app code.

.. autofunction:: set_locale
.. autofunction:: gettext
.. autofunction:: ngettext
.. autofunction:: lazy_gettext
.. autofunction:: lazy_ngettext


Date and time functions
-----------------------
The preferred way of dealing with dates and times is to always store and work
internally with them in UTC, converting to localtime time only when generating
output.

UTC is the default timezone in App Engine and is used when ``auto_now``
or ``auto_now_add`` are set to `True` in ``db.DateProperty``,
``db.DateTimeProperty`` or ``db.TimeProperty``.

To convert dates and times stored in UTC to a localized version with timezone
applied, use the functions :func:`format_date`, :func:`format_datetime` or
:func:`format_time`.

.. autofunction:: format_date
.. autofunction:: format_datetime
.. autofunction:: format_time

Timezone functions
------------------
These functions help to convert internal datetime values to different timezones.

.. autofunction:: get_tzinfo
.. autofunction:: to_local_timezone
.. autofunction:: to_utc
