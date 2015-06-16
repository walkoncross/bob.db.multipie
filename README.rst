.. vim: set fileencoding=utf-8 :
.. Manuel Guenther <manuel.guenther@idiap.ch>
.. Fri Oct 31 14:18:57 CET 2014

.. image:: http://img.shields.io/badge/docs-stable-yellow.png
   :target: http://pythonhosted.org/bob.db.multipie/index.html
.. image:: http://img.shields.io/badge/docs-latest-orange.png
   :target: https://www.idiap.ch/software/bob/docs/latest/bioidiap/bob.db.multipie/master/index.html
.. image:: https://travis-ci.org/bioidiap/bob.db.multipie.svg?branch=v2.0.2
   :target: https://travis-ci.org/bioidiap/bob.db.multipie
.. image:: https://coveralls.io/repos/bioidiap/bob.db.multipie/badge.png
   :target: https://coveralls.io/r/bioidiap/bob.db.multipie
.. image:: https://img.shields.io/badge/github-master-0000c0.png
   :target: https://github.com/bioidiap/bob.db.multipie/tree/master
.. image:: http://img.shields.io/pypi/v/bob.db.multipie.png
   :target: https://pypi.python.org/pypi/bob.db.multipie
.. image:: http://img.shields.io/pypi/dm/bob.db.multipie.png
   :target: https://pypi.python.org/pypi/bob.db.multipie
.. image:: https://img.shields.io/badge/original-data--files-a000a0.png
   :target: http://www.multipie.org

======================================
 Multi-PIE Database Interface for Bob
======================================

This package contains an interface for the evaluation protocol of the `Multi-PIE`_ database.
This package does not contain the original `Multi-PIE`_ data files, which need to be obtained through the link above.


Installation
------------
To install this package -- alone or together with other `Packages of Bob <https://github.com/idiap/bob/wiki/Packages>`_ -- please read the `Installation Instructions <https://github.com/idiap/bob/wiki/Installation>`_.
For Bob_ to be able to work properly, some dependent packages are required to be installed.
Please make sure that you have read the `Dependencies <https://github.com/idiap/bob/wiki/Dependencies>`_ for your operating system.

Documentation
-------------
For further documentation on this package, please read the `Stable Version <http://pythonhosted.org/bob.db.multipie/index.html>`_ or the `Latest Version <https://www.idiap.ch/software/bob/docs/latest/bioidiap/bob.db.multipie/master/index.html>`_ of the documentation.
For a list of tutorials on this or the other packages ob Bob_, or information on submitting issues, asking questions and starting discussions, please visit its website.


Reducing the Protocols
----------------------
For simplicity, when you download this package from our PyPI_ page, by default all provided protocols are enabled.
This makes the database query a bit slow.
If you don't want to wait each time you query the database, you can re-create the database on your own.
For that, you have to follow the "download from git" recipe.
After doing the bootstrap/buildout step (see `here <http://www.idiap.ch/software/bob/docs/releases/last/sphinx/html/OrganizeYourCode.html>`_ for details) in your main directory, you have to go to the (newly created) directory ``src/bob.db.multipie`` and do the same bootstrap/buildout step again.
Finally, you can use the `Bob <http://www.idiap.ch/software/bob/>`_ API: ``./bin/bob_dbmanage.py multipie create --help`` to regenerate the SQLite file based on your criteria.

Afterward, only the requested protocols should be available.
If not, please `file a bug <https://github.com/bioidiap/bob.db.multipie/issues>`_ to get help.


Note to the package maintainers
-------------------------------

On PyPI, we used to provide the database with all the protocols enabled.
This means that the database has to be generated as follows, before the packaging: ``./bin/bob_dbmanage.py multipie create -P -E``.

.. _bob: https://www.idiap.ch/software/bob
.. _multi-pie: http://www.multipie.org
.. _pypi: http://pypi.python.org/pypi/bob.db.multipie

