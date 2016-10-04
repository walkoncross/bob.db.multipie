.. vim: set fileencoding=utf-8 :
.. @author: Manuel Guenther <Manuel.Guenther@idiap.ch>
.. @date:   Thu Dec  6 12:28:25 CET 2012

==============
 User's Guide
==============

This package contains the access API and descriptions for the `Multi-PIE`_ database.
It only contains the Bob_ accessor methods to use the DB directly from python, with our certified protocols.
The actual raw data for the `Multi-PIE`_ database should be downloaded from the original URL.

The Database Interface
----------------------

The :py:class:`bob.db.multipie.Database` complies with the standard biometric verification database as described in `bob.db.base <bob.db.base>`, implementing both interfaces :py:class:`bob.db.base.Database`.

.. todo::
   Explain the particularities of the :py:class:`bob.db.multipie.Database`.


.. _multi-pie: http://www.multipie.org
.. _bob: https://www.idiap.ch/software/bob
