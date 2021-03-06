Directory Query (dirq)
======================
*WORK IN PROGRESS, NOT READY FOR USE*

This file describes the Directory Query package and associated command-line tool.

The package provides interfaces for common back-end directories such as LDAP or
Microsoft's Active Directory, for the purposes of running primarily short queries
for personnel contact information.

dirq.py
-------
The dirq.py tool provides a shell-based interactive query capability, intended to
provide output comparable to the legacy finger services. A batch-mode capability,
to query a list of requests in serial is intended.

Default output will be plain text with space-based indenting, suitable for a
terminal with a monospace font. Other output formats will include CSV and JSON.

This tool is written from the ground up to replace prior tools that were overly
tied to specific directory implementations.

DEVELOPMENT GOALS
-----------------
Python2.7 is the current target environment, with conscious effort intended to
permit quick switching to Python3.

  * Implement searches against multiple types of back-end directories
    * Permit lookup against LDAP and Active Directory
    * Abstract schemas as much as practical
  * Provide human-readable output
    * Simulate legacy UNIX "finger" output with personnel locator information (name, phone number, email address)
  * Provide human-friendly search interpretation
    * Provide capability to customize for local conditions (e.g., phone extensions)
  * Provide batch-processing capabilities such as in the middle of a larger pipeline
    * Accept multiple search requests, as varied as practical
    * Provide multiple mass-data output formats (CSV, JSON)
