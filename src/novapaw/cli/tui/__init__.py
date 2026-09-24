# -*- coding: utf-8 -*-
"""NovaPaw terminal chat UI (TUI).

A Textual front-end, bundled into NovaPaw, that drives the agent over ACP by
spawning ``novapaw acp`` as a subprocess. The UI layer only ever sees the
normalized :class:`~novapaw.cli.tui.transport.base.TuiTransport` interface and
the :mod:`~novapaw.cli.tui.events` event union, so the transport is a swappable
seam: a future in-process transport can replace the ACP subprocess without
touching any widget.

Entry points:

* bare ``novapaw`` (no subcommand) -> :func:`~novapaw.cli.tui.launch.run_tui`
* ``novapaw tui [--agent ... | --resume ...]``

Originally developed as the standalone ``paw`` CLI; relocated here in Phase 1.
"""

from __future__ import annotations

from .__version__ import __version__

__all__ = ["__version__"]
