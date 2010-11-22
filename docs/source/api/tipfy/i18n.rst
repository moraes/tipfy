.. _api.tipfy.i18n:

I18n
====
.. module:: tipfy.i18n


Default configuration
---------------------
.. autodata:: default_config


Middleware
----------
.. autoclass:: I18nMiddleware
   :members: after_dispatch


Classes
-------
.. autoclass:: I18nStore
   :members: __init__, set_locale_for_request, set_timezone_for_request,
             set_locale, set_timezone, load_translations, gettext, ngettext,
             to_local_timezone, to_utc, format_date, format_datetime,
             format_time, format_timedelta, format_number, format_decimal,
             format_currency, format_percent, format_scientific, parse_date,
             parse_datetime, parse_time, parse_number, parse_decimal,
             get_timezone_location


Functions
---------
.. autofunction:: set_locale
.. autofunction:: set_timezone
.. autofunction:: _
.. autofunction:: gettext
.. autofunction:: ngettext
.. autofunction:: lazy_gettext
.. autofunction:: lazy_ngettext
.. autofunction:: to_local_timezone
.. autofunction:: to_utc
.. autofunction:: format_date
.. autofunction:: format_datetime
.. autofunction:: format_time
.. autofunction:: format_timedelta
.. autofunction:: format_number
.. autofunction:: format_decimal
.. autofunction:: format_currency
.. autofunction:: format_percent
.. autofunction:: format_scientific
.. autofunction:: parse_date
.. autofunction:: parse_datetime
.. autofunction:: parse_time
.. autofunction:: parse_number
.. autofunction:: parse_decimal
.. autofunction:: get_timezone_location
.. autofunction:: list_translations
