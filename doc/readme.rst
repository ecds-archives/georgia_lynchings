================
Project Overview
================

.. include:: ../README

Importing Data
==============

Importing or updating data from the PCA datasource is primarily done by importing pre-
formatted CSV exports from PCAce.  Each has a required format and is run through a
manage.py command. Data should be imported in the following order and way.

Demographic Data
----------------

Data about counties and related population information is maintained in the demographics
app in the site.  Data should not need to be refreshed and will be loaded from 
`~georgia_lynchings/georgia_lynchings/demographics/fixtures/initial_data.json` this data
was compiled the `Historic Cencus Browser from University of Virginia Library 
<http://mapserver.lib.virginia.edu/>`_.

Victim Data
-----------

.. automodule:: georgia_lynchings.lynchings.management.commands.import_victims

Article Data
------------

.. automodule:: georgia_lynchings.lynchings.management.commands.rebuild_articles