=======
Plugins
=======

esc bundles only a small number of built-in operations
so you can decide what operations will be useful to you
and avoid staring all day at operations you never use.
Any remaining operations you need can be added via plugins.


Plugin location
===============

Plugins are Python modules (``.py`` files)
stored in the ``plugins`` subdirectory of your esc configuration directory.
By default your esc configuration directory is ``~/.esc``,
where ``~`` represents your home or user directory.
If this directory doesn't exist but ``$XDG_CONFIG_HOME/esc``
(or ``~/.config/esc`` if that environment variable is unset)
does, that is used instead.
(See `here <xdg-here>`_
for why you might want to use the XDG folders specification.)

.. _xdg-here: https://ploum.net/207-modify-your-application-to-use-xdg-folders/


Installing plugins
==================

To install a plugin,
you simply copy its ``.py`` file into your plugins directory
(see :ref:`Plugin location`).
You can create the ``.esc`` and/or ``plugins`` directories
if they don't exist.
The next time you start esc, the plugins will be loaded.

.. warning::
    esc plugins can execute arbitrary Python code on your computer,
    which could include malicious code,
    so you should not install esc plugins from sources that you do not trust.

.. tip::
    Plugins are loaded
    and their operations placed in the :guilabel:`Commands` window
    in alphabetical order by their filename.
    To control the order, you can prefix their filenames with numbers,
    e.g., ``01_trig.py``, ``02_log.py``.


Finding plugins
===============

You can write your own plugins
(see the :ref:`Developer Manual`)
or get plugins from someone else.
Some plugins providing common features like trig and log functions
are available for download in the esc repository
under `esc-plugins`_.

.. _esc-plugins: https://github.com/sobjornstad/esc/tree/master/esc-plugins
