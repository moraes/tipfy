.. _api.tipfy.ext.db:

tipfy.ext.db
============
This module provides several utilities to work with ``google.appengine.ext.db``,
including serialization functions, decorators and useful extra ``db.Property``
classes.

.. module:: tipfy.ext.db


``db.Model`` utilities
----------------------
.. autofunction:: get_protobuf_from_entity
.. autofunction:: get_entity_from_protobuf
.. autofunction:: get_reference_key
.. autofunction:: populate_entity
.. autofunction:: get_property_dict
.. autofunction:: get_or_insert_with_flag
.. autofunction:: get_or_404
.. autofunction:: get_by_id_or_404
.. autofunction:: get_by_key_name_or_404


Decorators
----------
.. autofunction:: retry_on_timeout
.. autofunction:: load_entity


Extra ``db.Property`` classes
-----------------------------
.. autoclass:: EtagProperty
.. autoclass:: JsonProperty
.. autoclass:: PickleProperty
.. autoclass:: SlugProperty
.. autoclass:: TimezoneProperty


.. _Nick's Blog: http://blog.notdot.net/2009/9/Efficient-model-memcaching
.. _Kay: http://code.google.com/p/kay-framework/
.. _aetycoon: http://github.com/Arachnid/aetycoon/
