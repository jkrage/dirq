Musings
=======
Design thoughts/notes/musings.

Auto-magic Query Interpreter
----------------------------
* Allow creation via config/plugin file?
* UID handling (%10d)
* Phone number, extension
  * US 10-digit:
        `\d{3}[-. ]\d{3}[-. ]\d{4}`
  * US 7-digit:
    `\d{3}[-. ]\d{4}`
  * Phone extension, 4-5 digits, with/without prefix x:
    `x?\d{1}[-. ]\d{3-4}`
* AUID/username
* Surname/Common Name/Nickname/Exact

Directory Filter Construction
-----------------------------
* Classes for filter pieces
* Extensible mapping from query->filter

Attribute Handling
------------------
* Address multi-line attributes (e.g., description, userCertificate)
* Synthetic attributes (combine/mangle multiple attributes
  into a new one, add new meta attributes)
* Re-write attributes (e.g., phone numbers)
* Decode AD attributes (e.g., account lockout)

Output Options
--------------
* Multiple output formats ("finger", CSV)
  * Output handler class
* User-custom formats/arrangements
  * print().format(*attributes)
 
Configuration File
------------------
* Initially .json format, nested tree:
  * Service
    * name -- reference label for the service
    * Server
      * name -- reference label for the server
      * uris[] -- one or more server URIs to query
      * base -- base OU for queries
      * add_attributes[] -- extra attributes to request on each query
    * Searches
      * name -- reference label for the search
      * search -- filter to apply during search
    * Outputs
      * name -- reference label for the output type
      * string -- output string format (Python "".format())

Stretch Goals
-------------
* Base64 UTF-8 decoding from LDIF (e.g., for kana)
* Integration with OSX Keychain for authentication
* Download S/MIME certificates to a keystore
* Simple GUI via TK/wx
* Parse AD attributes for account-oriented queries (e.g., lockout)
