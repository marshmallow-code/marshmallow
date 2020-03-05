Changelog
---------

2.21.0 (2020-03-05)
+++++++++++++++++++

Bug fixes:

- Don't match string-ending newlines in ``URL`` and ``Email`` fields
  (:issue:`1522`). Thanks :user:`nbanmp` for the PR.

Other changes:

- Drop support for Python 3.4 (:pr:`1525`).


2.20.5 (2019-09-15)
+++++++++++++++++++

Bug fixes:

- Fix behavior when a non-list collection is passed to the ``validate`` argument of ``fields.Email`` and ``fields.URL`` (:issue:`1400`).

2.20.4 (2019-09-11)
+++++++++++++++++++

Bug fixes:

- Respect the ``many`` value on ``Schema`` instances passed to ``Nested`` (:issue:`1160`).
  Thanks :user:`Kamforka` for reporting.

2.20.3 (2019-09-04)
+++++++++++++++++++

Bug fixes:

- Don't swallow ``TypeError`` exceptions raised by ``Field._bind_to_schema`` or ``Schema.on_bind_field``.

2.20.2 (2019-08-20)
+++++++++++++++++++

Bug fixes:

- Prevent warning about importing from ``collections`` on Python 3.7
  (:pr:`1354`). Thanks :user:`nicktimko` for the PR.

2.20.1 (2019-08-13)
+++++++++++++++++++

Bug fixes:

- Fix bug that raised ``TypeError`` when invalid data type is
  passed to a nested schema with ``@validates`` (:issue:`1342`).

2.20.0 (2019-08-10)
+++++++++++++++++++

Bug fixes:

- Fix deprecated functions' compatibility with Python 2 (:issue:`1337`).
  Thanks :user:`airstandley` for the catch and patch.
- Fix error message consistency for invalid input types on nested fields (:issue:`1303`).
  This is a backport of the fix in :pr:`857`. Thanks :user:`cristi23` for the
  thorough bug report and the PR.

Deprecation/Removal:

- Python 2.6 is no longer officially supported (:issue:`1274`).

2.19.5 (2019-06-18)
+++++++++++++++++++

Bug fixes:

- Fix deserializing ISO8601-formatted datetimes with less than 6-digit
  miroseconds (:issue:`1251`). Thanks :user:`diego-plan9` for reporting.

2.19.4 (2019-06-16)
+++++++++++++++++++

Bug fixes:

- Microseconds no longer gets lost when deserializing datetimes without dateutil
  installed (:issue:`1147`).

2.19.3 (2019-06-15)
+++++++++++++++++++

Bug fixes:

- Fix bug where nested fields in ``Meta.exclude`` would not work on
  multiple instantiations (:issue:`1212`). Thanks :user:`MHannila` for
  reporting.

2.19.2 (2019-03-30)
+++++++++++++++++++

Bug fixes:

- Handle ``OverflowError`` when (de)serializing large integers with
  ``fields.Float`` (:pr:`1177`). Thanks :user:`brycedrennan` for the PR.

2.19.1 (2019-03-16)
+++++++++++++++++++

Bug fixes:

- Fix bug where ``Nested(many=True)`` would skip first element when
  serializing a generator (:issue:`1163`). Thanks :user:`khvn26` for the
  catch and patch.

2.19.0 (2019-03-07)
+++++++++++++++++++

Deprecation/Removal:

- A `RemovedInMarshmallow3` warning is raised when using
  `fields.FormattedString`. Use `fields.Method` or `fields.Function`
  instead (:issue:`1141`).

2.18.1 (2019-02-15)
+++++++++++++++++++

Bug fixes:

- A ``ChangedInMarshmallow3Warning`` is no longer raised when
  ``strict=False`` (:issue:`1108`). Thanks :user:`Aegdesil` for
  reporting.

2.18.0 (2019-01-13)
+++++++++++++++++++

Features:

- Add warnings for functions in ``marshmallow.utils`` that are removed in
  marshmallow 3.

Bug fixes:

- Copying ``missing`` with ``copy.copy`` or ``copy.deepcopy`` will not
  duplicate it (:pr:`1099`).

2.17.0 (2018-12-26)
+++++++++++++++++++

Features:

- Add ``marshmallow.__version_info__`` (:pr:`1074`).
- Add warnings for API that is deprecated or changed to help users
  prepare for marshmallow 3 (:pr:`1075`).

2.16.3 (2018-11-01)
+++++++++++++++++++

Bug fixes:

- Prevent memory leak when dynamically creating classes with ``type()``
  (:issue:`732`). Thanks :user:`asmodehn` for writing the tests to
  reproduce this issue.

2.16.2 (2018-10-30)
+++++++++++++++++++

Bug fixes:

- Prevent warning about importing from ``collections`` on Python 3.7
  (:issue:`1027`). Thanks :user:`nkonin` for reporting and
  :user:`jmargeta` for the PR.

2.16.1 (2018-10-17)
+++++++++++++++++++

Bug fixes:

- Remove spurious warning about implicit collection handling
  (:issue:`998`). Thanks :user:`lalvarezguillen` for reporting.

2.16.0 (2018-10-10)
+++++++++++++++++++

Bug fixes:

- Allow username without password in basic auth part of the url in
  ``fields.Url`` (:pr:`982`). Thanks user:`alefnula` for the PR.

Other changes:

- Drop support for Python 3.3 (:pr:`987`).

2.15.6 (2018-09-20)
+++++++++++++++++++

Bug fixes:

- Prevent ``TypeError`` when a non-collection is passed to a ``Schema`` with ``many=True``.
  Instead, raise ``ValidationError`` with ``{'_schema': ['Invalid input type.']}`` (:issue:`906`).
- Fix ``root`` attribute for nested container fields on list
  on inheriting schemas (:issue:`956`). Thanks :user:`bmcbu`
  for reporting.

These fixes were backported from 3.0.0b15 and 3.0.0b16.


2.15.5 (2018-09-15)
+++++++++++++++++++

Bug fixes:

- Handle empty SQLAlchemy lazy lists gracefully when dumping (:issue:`948`).
  Thanks :user:`vke-code` for the catch and :user:`YuriHeupa` for the patch.

2.15.4 (2018-08-04)
+++++++++++++++++++

Bug fixes:

- Respect ``load_from`` when reporting errors for ``@validates('field_name')``
  (:issue:`748`). Thanks :user:`m-novikov` for the catch and patch.

2.15.3 (2018-05-20)
+++++++++++++++++++

Bug fixes:

- Fix passing ``only`` as a string to ``nested`` when the passed field
  defines ``dump_to`` (:issue:`800`, :issue:`822`). Thanks
  :user:`deckar01` for the catch and patch.

2.15.2 (2018-05-10)
+++++++++++++++++++

Bug fixes:

- Fix a race condition in validation when concurrent threads use the
  same ``Schema`` instance (:issue:`783`). Thanks :user:`yupeng0921` and
  :user:`lafrech` for the fix.
- Fix serialization behavior of
  ``fields.List(fields.Integer(as_string=True))`` (:issue:`788`). Thanks
  :user:`cactus` for reporting and :user:`lafrech` for the fix.
- Fix behavior of ``exclude`` parameter when passed from parent to
  nested schemas (:issue:`728`). Thanks :user:`timc13` for reporting and
  :user:`deckar01` for the fix.

2.15.1 (2018-04-25)
+++++++++++++++++++

Bug fixes:

- :cve:`CVE-2018-17175`: Fix behavior when an empty list is passed as the ``only`` argument
  (:issue:`772`). Thanks :user:`deckar01` for reporting and thanks
  :user:`lafrech` for the fix.

2.15.0 (2017-12-02)
+++++++++++++++++++

Bug fixes:

- Handle ``UnicodeDecodeError`` when deserializing ``bytes`` with a
  ``String`` field (:issue:`650`). Thanks :user:`dan-blanchard` for the
  suggestion and thanks :user:`4lissonsilveira` for the PR.

2.14.0 (2017-10-23)
+++++++++++++++++++

Features:

- Add ``require_tld`` parameter to ``validate.URL`` (:issue:`664`).
  Thanks :user:`sduthil` for the suggestion and the PR.

2.13.6 (2017-08-16)
+++++++++++++++++++

Bug fixes:

- Fix serialization of types that implement `__getitem__`
  (:issue:`669`). Thanks :user:`MichalKononenko`.

2.13.5 (2017-04-12)
+++++++++++++++++++

Bug fixes:

- Fix validation of iso8601-formatted dates (:issue:`556`). Thanks :user:`lafrech` for reporting.

2.13.4 (2017-03-19)
+++++++++++++++++++

Bug fixes:

- Fix symmetry of serialization and deserialization behavior when passing a dot-delimited path to the ``attribute`` parameter of fields (:issue:`450`). Thanks :user:`itajaja` for reporting.

2.13.3 (2017-03-11)
+++++++++++++++++++

Bug fixes:

- Restore backwards-compatibility of ``SchemaOpts`` constructor (:issue:`597`). Thanks :user:`Wesmania` for reporting and thanks :user:`frol` for the fix.

2.13.2 (2017-03-10)
+++++++++++++++++++

Bug fixes:

- Fix inheritance of ``ordered`` option when ``Schema`` subclasses define ``class Meta`` (:issue:`593`). Thanks :user:`frol`.

Support:

- Update contributing docs.

2.13.1 (2017-03-04)
+++++++++++++++++++

Bug fixes:

- Fix sorting on Schema subclasses when ``ordered=True`` (:issue:`592`). Thanks :user:`frol`.

2.13.0 (2017-02-18)
+++++++++++++++++++

Features:

- Minor optimizations (:issue:`577`). Thanks :user:`rowillia` for the PR.

2.12.2 (2017-01-30)
+++++++++++++++++++

Bug fixes:

- Unbound fields return `None` rather returning the field itself. This fixes a corner case introduced in :issue:`572`. Thanks :user:`touilleMan` for reporting and :user:`YuriHeupa` for the fix.

2.12.1 (2017-01-23)
+++++++++++++++++++

Bug fixes:

- Fix behavior when a ``Nested`` field is composed within a ``List`` field (:issue:`572`). Thanks :user:`avish` for reporting and :user:`YuriHeupa` for the PR.

2.12.0 (2017-01-22)
+++++++++++++++++++

Features:

- Allow passing nested attributes (e.g. ``'child.field'``) to the ``dump_only`` and ``load_only`` parameters of ``Schema`` (:issue:`572`). Thanks :user:`YuriHeupa` for the PR.
- Add ``schemes`` parameter to ``fields.URL`` (:issue:`574`). Thanks :user:`mosquito` for the PR.

2.11.1 (2017-01-08)
+++++++++++++++++++

Bug fixes:

- Allow ``strict`` class Meta option to be overriden by constructor (:issue:`550`). Thanks :user:`douglas-treadwell` for reporting and thanks :user:`podhmo` for the PR.

2.11.0 (2017-01-08)
+++++++++++++++++++

Features:

- Import ``marshmallow.fields`` in ``marshmallow/__init__.py`` to save an import when importing the ``marshmallow`` module (:issue:`557`). Thanks :user:`mindojo-victor`.

Support:

- Documentation: Improve example in "Validating Original Input Data" (:issue:`558`). Thanks :user:`altaurog`.
- Test against Python 3.6.

2.10.5 (2016-12-19)
+++++++++++++++++++

Bug fixes:

- Reset user-defined kwargs passed to ``ValidationError`` on each ``Schema.load`` call (:issue:`565`). Thanks :user:`jbasko` for the catch and patch.

Support:

- Tests: Fix redefinition of ``test_utils.test_get_value()`` (:issue:`562`). Thanks :user:`nelfin`.

2.10.4 (2016-11-18)
+++++++++++++++++++

Bug fixes:

- `Function` field works with callables that use Python 3 type annotations (:issue:`540`). Thanks :user:`martinstein` for reporting and thanks :user:`sabinem`, :user:`lafrech`, and :user:`maximkulkin` for the work on the PR.

2.10.3 (2016-10-02)
+++++++++++++++++++

Bug fixes:

- Fix behavior for serializing missing data with ``Number`` fields when ``as_string=True`` is passed (:issue:`538`). Thanks :user:`jessemyers` for reporting.

2.10.2 (2016-09-25)
+++++++++++++++++++

Bug fixes:

- Use fixed-point notation rather than engineering notation when serializing with ``Decimal`` (:issue:`534`). Thanks :user:`gdub`.
- Fix UUID validation on serialization and deserialization of ``uuid.UUID`` objects (:issue:`532`). Thanks :user:`pauljz`.

2.10.1 (2016-09-14)
+++++++++++++++++++

Bug fixes:

- Fix behavior when using ``validate.Equal(False)`` (:issue:`484`). Thanks :user:`pktangyue` for reporting and thanks :user:`tuukkamustonen` for the fix.
- Fix ``strict`` behavior when errors are raised in ``pre_dump``/``post_dump`` processors (:issue:`521`). Thanks :user:`tvuotila` for the catch and patch.
- Fix validation of nested fields on dumping (:issue:`528`). Thanks again :user:`tvuotila`.

2.10.0 (2016-09-05)
+++++++++++++++++++

Features:

- Errors raised by pre/post-load/dump methods will be added to a schema's errors dictionary (:issue:`472`). Thanks :user:`dbertouille` for the suggestion and for the PR.

2.9.1 (2016-07-21)
++++++++++++++++++

Bug fixes:

- Fix serialization of ``datetime.time`` objects with microseconds (:issue:`464`). Thanks :user:`Tim-Erwin` for reporting and thanks :user:`vuonghv` for the fix.
- Make ``@validates`` consistent with field validator behavior: if validation fails, the field will not be included in the deserialized output (:issue:`391`). Thanks :user:`martinstein` for reporting and thanks :user:`vuonghv` for the fix.

2.9.0 (2016-07-06)
++++++++++++++++++

- ``Decimal`` field coerces input values to a string before deserializing to a `decimal.Decimal` object in order to avoid transformation of float values under 12 significant digits (:issue:`434`, :issue:`435`). Thanks :user:`davidthornton` for the PR.

2.8.0 (2016-06-23)
++++++++++++++++++

Features:

- Allow ``only`` and ``exclude`` parameters to take nested fields, using dot-delimited syntax (e.g. ``only=['blog.author.email']``) (:issue:`402`). Thanks :user:`Tim-Erwin` and :user:`deckar01` for the discussion and implementation.

Support:

- Update tasks.py for compatibility with invoke>=0.13.0. Thanks :user:`deckar01`.

2.7.3 (2016-05-05)
++++++++++++++++++

- Make ``field.parent`` and ``field.name`` accessible to ``on_bind_field`` (:issue:`449`). Thanks :user:`immerrr`.

2.7.2 (2016-04-27)
++++++++++++++++++

No code changes in this release. This is a reupload in order to distribute an sdist for the last hotfix release. See :issue:`443`.

Support:

- Update license entry in setup.py to fix RPM distributions (:issue:`433`). Thanks :user:`rrajaravi` for reporting.

2.7.1 (2016-04-08)
++++++++++++++++++

Bug fixes:

- Only add Schemas to class registry if a class name is provided. This allows Schemas to be
  constructed dynamically using the ``type`` constructor without getting added to the class registry (which is useful for saving memory).

2.7.0 (2016-04-04)
++++++++++++++++++

Features:

- Make context available to ``Nested`` field's ``on_bind_field`` method (:issue:`408`). Thanks :user:`immerrr` for the PR.
- Pass through user ``ValidationError`` kwargs (:issue:`418`). Thanks :user:`russelldavies` for helping implement this.

Other changes:

- Remove unused attributes ``root``, ``parent``, and ``name`` from ``SchemaABC`` (:issue:`410`). Thanks :user:`Tim-Erwin` for the PR.

2.6.1 (2016-03-17)
++++++++++++++++++

Bug fixes:

- Respect `load_from` when reporting errors for nested required fields (:issue:`414`). Thanks :user:`yumike`.

2.6.0 (2016-02-01)
++++++++++++++++++

Features:

- Add ``partial`` argument to ``Schema.validate`` (:issue:`379`). Thanks :user:`tdevelioglu` for the PR.
- Add ``equal`` argument to ``validate.Length``. Thanks :user:`daniloakamine`.
- Collect all validation errors for each item deserialized by a ``List`` field (:issue:`345`). Thanks :user:`maximkulkin` for the report and the PR.

2.5.0 (2016-01-16)
++++++++++++++++++

Features:

- Allow a tuple of field names to be passed as the ``partial`` argument to ``Schema.load`` (:issue:`369`). Thanks :user:`tdevelioglu` for the PR.
- Add ``schemes`` argument to ``validate.URL`` (:issue:`356`).

2.4.2 (2015-12-08)
++++++++++++++++++

Bug fixes:

- Prevent duplicate error messages when validating nested collections (:issue:`360`). Thanks :user:`alexmorken` for the catch and patch.

2.4.1 (2015-12-07)
++++++++++++++++++

Bug fixes:

- Serializing an iterator will not drop the first item (:issue:`343`, :issue:`353`). Thanks :user:`jmcarp` for the patch. Thanks :user:`edgarallang` and :user:`jmcarp` for reporting.

2.4.0 (2015-12-06)
++++++++++++++++++

Features:

- Add ``skip_on_field_errors`` parameter to ``validates_schema`` (:issue:`323`). Thanks :user:`jjvattamattom` for the suggestion and :user:`d-sutherland` for the PR.

Bug fixes:

- Fix ``FormattedString`` serialization (:issue:`348`). Thanks :user:`acaird` for reporting.
- Fix ``@validates`` behavior when used when ``attribute`` is specified and ``strict=True`` (:issue:`350`). Thanks :user:`density` for reporting.

2.3.0 (2015-11-22)
++++++++++++++++++

Features:

- Add ``dump_to`` parameter to fields (:issue:`310`). Thanks :user:`ShayanArmanPercolate` for the suggestion. Thanks :user:`franciscod` and :user:`ewang` for the PRs.
- The ``deserialize`` function passed to ``fields.Function`` can optionally receive a ``context`` argument (:issue:`324`). Thanks :user:`DamianHeard`.
- The ``serialize`` function passed to ``fields.Function`` is optional (:issue:`325`). Thanks again :user:`DamianHeard`.
- The ``serialize`` function passed to ``fields.Method`` is optional (:issue:`329`). Thanks :user:`justanr`.

Deprecation/Removal:

- The ``func`` argument of ``fields.Function`` has been renamed to ``serialize``.
- The ``method_name`` argument of ``fields.Method`` has been renamed to ``serialize``.

``func`` and ``method_name`` are still present for backwards-compatibility, but they will both be removed in marshmallow 3.0.

2.2.1 (2015-11-11)
++++++++++++++++++

Bug fixes:

- Skip field validators for fields that aren't included in ``only`` (:issue:`320`). Thanks :user:`carlos-alberto` for reporting and :user:`eprikazc` for the PR.

2.2.0 (2015-10-26)
++++++++++++++++++

Features:

- Add support for partial deserialization with the ``partial`` argument to ``Schema`` and ``Schema.load`` (:issue:`290`). Thanks :user:`taion`.

Deprecation/Removals:

- ``Query`` and ``QuerySelect`` fields are removed.
- Passing of strings to ``required`` and ``allow_none`` is removed. Pass the ``error_messages`` argument instead.

Support:

- Add example of Schema inheritance in docs (:issue:`225`). Thanks :user:`martinstein` for the suggestion and :user:`juanrossi` for the PR.
- Add "Customizing Error Messages" section to custom fields docs.

2.1.3 (2015-10-18)
++++++++++++++++++

Bug fixes:

- Fix serialization of collections for which `iter` will modify position, e.g. Pymongo cursors (:issue:`303`). Thanks :user:`Mise` for the catch and patch.

2.1.2 (2015-10-14)
++++++++++++++++++

Bug fixes:

- Fix passing data to schema validator when using ``@validates_schema(many=True)`` (:issue:`297`). Thanks :user:`d-sutherland` for reporting.
- Fix usage of ``@validates`` with a nested field when ``many=True`` (:issue:`298`). Thanks :user:`nelfin` for the catch and patch.

2.1.1 (2015-10-07)
++++++++++++++++++

Bug fixes:

- ``Constant`` field deserializes to its value regardless of whether its field name is present in input data (:issue:`291`). Thanks :user:`fayazkhan` for reporting.

2.1.0 (2015-09-30)
++++++++++++++++++

Features:

- Add ``Dict`` field for arbitrary mapping data (:issue:`251`). Thanks :user:`dwieeb` for adding this and :user:`Dowwie` for the suggestion.
- Add ``Field.root`` property, which references the field's Schema.

Deprecation/Removals:

- The ``extra`` param of ``Schema`` is deprecated. Add extra data in a ``post_load`` method instead.
- ``UnmarshallingError`` and ``MarshallingError`` are removed.

Bug fixes:

- Fix storing multiple schema-level validation errors (:issue:`287`). Thanks :user:`evgeny-sureev` for the patch.
- If ``missing=None`` on a field, ``allow_none`` will be set to ``True``.

Other changes:

- A ``List's`` inner field will have the list field set as its parent. Use ``root`` to access the ``Schema``.

2.0.0 (2015-09-25)
++++++++++++++++++

Features:

- Make error messages configurable at the class level and instance level (``Field.default_error_messages`` attribute and ``error_messages`` parameter, respectively).

Deprecation/Removals:

- Remove ``make_object``. Use a ``post_load`` method instead (:issue:`277`).
- Remove the ``error`` parameter and attribute of ``Field``.
- Passing string arguments to ``required`` and ``allow_none`` is deprecated. Pass the ``error_messages`` argument instead. **This API will be removed in version 2.2**.
- Remove ``Arbitrary``, ``Fixed``, and ``Price`` fields (:issue:`86`). Use ``Decimal`` instead.
- Remove ``Select`` / ``Enum`` fields (:issue:`135`). Use the ``OneOf`` validator instead.

Bug fixes:

- Fix error format for ``Nested`` fields when ``many=True``. Thanks :user:`alexmorken`.
- ``pre_dump`` methods are invoked before implicit field creation. Thanks :user:`makmanalp` for reporting.
- Return correct "required" error message for ``Nested`` field.
- The ``only`` argument passed to a ``Schema`` is bounded by the ``fields`` option (:issue:`183`). Thanks :user:`lustdante` for the suggestion.

Changes from 2.0.0rc2:

- ``error_handler`` and ``accessor`` options are replaced with the ``handle_error`` and ``get_attribute`` methods :issue:`284`.
- Remove ``marshmallow.compat.plain_function`` since it is no longer used.
- Non-collection values are invalid input for ``List`` field (:issue:`231`). Thanks :user:`density` for reporting.
- Bug fix: Prevent infinite loop when validating a required, self-nested field. Thanks :user:`Bachmann1234` for the fix.

2.0.0rc2 (2015-09-16)
+++++++++++++++++++++

Deprecation/Removals:

- ``make_object`` is deprecated. Use a ``post_load`` method instead (:issue:`277`). **This method will be removed in the final 2.0 release**.
- ``Schema.accessor`` and ``Schema.error_handler`` decorators are deprecated. Define the ``accessor`` and ``error_handler`` class Meta options instead.

Bug fixes:

- Allow non-field names to be passed to ``ValidationError`` (:issue:`273`). Thanks :user:`evgeny-sureev` for the catch and patch.

Changes from 2.0.0rc1:

- The ``raw`` parameter of the ``pre_*``, ``post_*``, ``validates_schema`` decorators was renamed to ``pass_many`` (:issue:`276`).
- Add ``pass_original`` parameter to ``post_load`` and ``post_dump`` (:issue:`216`).
- Methods decorated with the ``pre_*``, ``post_*``, and ``validates_*`` decorators must be instance methods. Class methods and instance methods are not supported at this time.

2.0.0rc1 (2015-09-13)
+++++++++++++++++++++

Features:

- *Backwards-incompatible*: ``fields.Field._deserialize`` now takes ``attr`` and ``data`` as arguments (:issue:`172`). Thanks :user:`alexmic` and :user:`kevinastone` for the suggestion.
- Allow a ``Field's`` ``attribute`` to be modified during deserialization (:issue:`266`). Thanks :user:`floqqi`.
- Allow partially-valid data to be returned for ``Nested`` fields (:issue:`269`). Thanks :user:`jomag` for the suggestion.
- Add ``Schema.on_bind_field`` hook which allows a ``Schema`` to modify its fields when they are bound.
- Stricter validation of string, boolean, and number fields (:issue:`231`). Thanks :user:`touilleMan` for the suggestion.
- Improve consistency of error messages.

Deprecation/Removals:

- ``Schema.validator``, ``Schema.preprocessor``, and ``Schema.data_handler`` are removed. Use ``validates_schema``, ``pre_load``, and ``post_dump`` instead.
- ``QuerySelect``  and ``QuerySelectList`` are deprecated (:issue:`227`). **These fields will be removed in version 2.1.**
- ``utils.get_callable_name`` is removed.

Bug fixes:

- If a date format string is passed to a ``DateTime`` field, it is always used for deserialization (:issue:`248`). Thanks :user:`bartaelterman` and :user:`praveen-p`.

Support:

- Documentation: Add "Using Context" section to "Extending Schemas" page (:issue:`224`).
- Include tests and docs in release tarballs (:issue:`201`).
- Test against Python 3.5.

2.0.0b5 (2015-08-23)
++++++++++++++++++++

Features:

- If a field corresponds to a callable attribute, it will be called upon serialization. Thanks :user:`alexmorken`.
- Add ``load_only`` and ``dump_only`` class Meta options. Thanks :user:`kelvinhammond`.
- If a ``Nested`` field is required, recursively validate any required fields in the nested schema (:issue:`235`). Thanks :user:`max-orhai`.
- Improve error message if a list of dicts is not passed to a ``Nested`` field for which ``many=True``. Thanks again :user:`max-orhai`.

Bug fixes:

- `make_object` is only called after all validators and postprocessors have finished (:issue:`253`). Thanks :user:`sunsongxp` for reporting.
- If an invalid type is passed to ``Schema`` and ``strict=False``, store a ``_schema`` error in the errors dict rather than raise an exception (:issue:`261`). Thanks :user:`density` for reporting.

Other changes:

- ``make_object`` is only called when input data are completely valid (:issue:`243`). Thanks :user:`kissgyorgy` for reporting.
- Change default error messages for ``URL`` and ``Email`` validators so that they don't include user input (:issue:`255`).
- ``Email`` validator permits email addresses with non-ASCII characters, as per RFC 6530 (:issue:`221`). Thanks :user:`lextoumbourou` for reporting and :user:`mwstobo` for sending the patch.

2.0.0b4 (2015-07-07)
++++++++++++++++++++

Features:

- ``List`` field respects the ``attribute`` argument of the inner field. Thanks :user:`jmcarp`.
- The ``container`` field ``List`` field has access to its parent ``Schema`` via its ``parent`` attribute. Thanks again :user:`jmcarp`.

Deprecation/Removals:

- Legacy validator functions have been removed (:issue:`73`). Use the class-based validators in ``marshmallow.validate`` instead.

Bug fixes:

- ``fields.Nested`` correctly serializes nested ``sets`` (:issue:`233`). Thanks :user:`traut`.

Changes from 2.0.0b3:

- If ``load_from`` is used on deserialization, the value of ``load_from`` is used as the key in the errors dict (:issue:`232`). Thanks :user:`alexmorken`.

2.0.0b3 (2015-06-14)
+++++++++++++++++++++

Features:

- Add ``marshmallow.validates_schema`` decorator for defining schema-level validators (:issue:`116`).
- Add ``marshmallow.validates`` decorator for defining field validators as Schema methods (:issue:`116`). Thanks :user:`philtay`.
- Performance improvements.
- Defining ``__marshallable__`` on complex objects is no longer necessary.
- Add ``fields.Constant``. Thanks :user:`kevinastone`.

Deprecation/Removals:

- Remove ``skip_missing`` class Meta option. By default, missing inputs are excluded from serialized output (:issue:`211`).
- Remove optional ``context`` parameter that gets passed to methods for ``Method`` fields.
- ``Schema.validator`` is deprecated. Use ``marshmallow.validates_schema`` instead.
- ``utils.get_func_name`` is removed. Use ``utils.get_callable_name`` instead.

Bug fixes:

- Fix serializing values from keyed tuple types (regression of :issue:`28`). Thanks :user:`makmanalp` for reporting.

Other changes:

- Remove unnecessary call to ``utils.get_value`` for ``Function`` and ``Method`` fields (:issue:`208`). Thanks :user:`jmcarp`.
- Serializing a collection without passing ``many=True`` will not result in an error. Be very careful to pass the ``many`` argument when necessary.

Support:

- Documentation: Update Flask and Peewee examples. Update Quickstart.

Changes from 2.0.0b2:

- ``Boolean`` field serializes ``None`` to ``None``, for consistency with other fields (:issue:`213`). Thanks :user:`cmanallen` for reporting.
- Bug fix: ``load_only`` fields do not get validated during serialization.
- Implicit passing of original, raw data to Schema validators is removed. Use ``@marshmallow.validates_schema(pass_original=True)`` instead.

2.0.0b2 (2015-05-03)
++++++++++++++++++++

Features:

- Add useful ``__repr__`` methods to validators (:issue:`204`). Thanks :user:`philtay`.
- *Backwards-incompatible*: By default, ``NaN``, ``Infinity``, and ``-Infinity`` are invalid values for ``fields.Decimal``. Pass ``allow_nan=True`` to allow these values. Thanks :user:`philtay`.

Changes from 2.0.0b1:

- Fix serialization of ``None`` for `Time`, `TimeDelta`, and `Date` fields (a regression introduced in 2.0.0a1).

Includes bug fixes from 1.2.6.

2.0.0b1 (2015-04-26)
++++++++++++++++++++

Features:

- Errored fields will not appear in (de)serialized output dictionaries (:issue:`153`, :issue:`202`).
- Instantiate ``OPTIONS_CLASS`` in ``SchemaMeta``. This makes ``Schema.opts`` available in metaclass methods. It also causes validation to occur earlier (upon ``Schema`` class declaration rather than instantiation).
- Add ``SchemaMeta.get_declared_fields`` class method to support adding additional declared fields.

Deprecation/Removals:

- Remove ``allow_null`` parameter of ``fields.Nested`` (:issue:`203`).

Changes from 2.0.0a1:

- Fix serialization of `None` for ``fields.Email``.

2.0.0a1 (2015-04-25)
++++++++++++++++++++

Features:

- *Backwards-incompatible*: When ``many=True``, the errors dictionary returned by ``dump`` and ``load`` will be keyed on the indices of invalid items in the (de)serialized collection (:issue:`75`). Add ``index_errors=False`` on a Schema's ``class Meta`` options to disable this behavior.
- *Backwards-incompatible*: By default, fields will raise a ValidationError if the input is ``None``. The ``allow_none`` parameter can override this behavior.
- *Backwards-incompatible*: A ``Field's`` ``default`` parameter is only used if explicitly set and the field's value is missing in the input to `Schema.dump`. If not set, the key will not be present in the serialized output for missing values . This is the behavior for *all* fields. ``fields.Str`` no longer defaults to ``''``, ``fields.Int`` no longer defaults to ``0``, etc. (:issue:`199`). Thanks :user:`jmcarp` for the feedback.
- In ``strict`` mode, a ``ValidationError`` is raised. Error messages are accessed via the ``ValidationError's`` ``messages`` attribute (:issue:`128`).
- Add ``allow_none`` parameter to ``fields.Field``. If ``False`` (the default), validation fails when the field's value is ``None`` (:issue:`76`, :issue:`111`). If ``allow_none`` is ``True``, ``None`` is considered valid and will deserialize to ``None``.
- Schema-level validators can store error messages for multiple fields (:issue:`118`). Thanks :user:`ksesong` for the suggestion.
- Add ``pre_load``, ``post_load``, ``pre_dump``, and ``post_dump`` Schema method decorators for defining pre- and post- processing routines (:issue:`153`, :issue:`179`). Thanks :user:`davidism`, :user:`taion`, and :user:`jmcarp` for the suggestions and feedback. Thanks :user:`taion` for the implementation.
- Error message for ``required`` validation is configurable. (:issue:`78`). Thanks :user:`svenstaro` for the suggestion. Thanks :user:`0xDCA` for the implementation.
- Add ``load_from`` parameter to fields (:issue:`125`). Thanks :user:`hakjoon`.
- Add ``load_only`` and ``dump_only`` parameters to fields (:issue:`61`, :issue:`87`). Thanks :user:`philtay`.
- Add `missing` parameter to fields (:issue:`115`). Thanks :user:`philtay`.
- Schema validators can take an optional ``raw_data`` argument which contains raw input data, incl. data not specified in the schema (:issue:`127`). Thanks :user:`ryanlowe0`.
- Add ``validate.OneOf`` (:issue:`135`) and ``validate.ContainsOnly`` (:issue:`149`) validators. Thanks :user:`philtay`.
- Error messages for validators can be interpolated with `{input}` and other values (depending on the validator).
- ``fields.TimeDelta`` always serializes to an integer value in order to avoid rounding errors (:issue:`105`). Thanks :user:`philtay`.
- Add ``include`` class Meta option to support field names which are Python keywords (:issue:`139`). Thanks :user:`nickretallack` for the suggestion.
- ``exclude`` parameter is respected when used together with ``only`` parameter (:issue:`165`). Thanks :user:`lustdante` for the catch and patch.
- ``fields.List`` works as expected with generators and sets (:issue:`185`). Thanks :user:`sergey-aganezov-jr`.

Deprecation/Removals:

- ``MarshallingError`` and ``UnmarshallingError`` error are deprecated in favor of a single ``ValidationError`` (:issue:`160`).
- ``context`` argument passed to Method fields is deprecated. Use ``self.context`` instead (:issue:`184`).
- Remove ``ForcedError``.
- Remove support for generator functions that yield validators (:issue:`74`). Plain generators of validators are still supported.
- The ``Select/Enum`` field is deprecated in favor of using `validate.OneOf` validator (:issue:`135`).
- Remove legacy, pre-1.0 API (``Schema.data`` and ``Schema.errors`` properties) (:issue:`73`).
- Remove ``null`` value.

Other changes:

- ``Marshaller``, ``Unmarshaller`` were moved to ``marshmallow.marshalling``. These should be considered private API (:issue:`129`).
- Make ``allow_null=True`` the default for ``Nested`` fields. This will make ``None`` serialize to ``None`` rather than a dictionary with empty values (:issue:`132`). Thanks :user:`nickrellack` for the suggestion.

1.2.6 (2015-05-03)
++++++++++++++++++

Bug fixes:

- Fix validation error message for ``fields.Decimal``.
- Allow error message for ``fields.Boolean`` to be customized with the ``error`` parameter (like other fields).

1.2.5 (2015-04-25)
++++++++++++++++++

Bug fixes:

- Fix validation of invalid types passed to a ``Nested`` field when ``many=True`` (:issue:`188`). Thanks :user:`juanrossi` for reporting.

Support:

- Fix pep8 dev dependency for flake8. Thanks :user:`taion`.

1.2.4 (2015-03-22)
++++++++++++++++++

Bug fixes:

- Fix behavior of ``as_string`` on ``fields.Integer`` (:issue:`173`). Thanks :user:`taion` for the catch and patch.

Other changes:

- Remove dead code from ``fields.Field``. Thanks :user:`taion`.

Support:

- Correction to ``_postprocess`` method in docs. Thanks again :user:`taion`.

1.2.3 (2015-03-15)
++++++++++++++++++

Bug fixes:

- Fix inheritance of ``ordered`` class Meta option (:issue:`162`). Thanks :user:`stephenfin` for reporting.

1.2.2 (2015-02-23)
++++++++++++++++++

Bug fixes:

- Fix behavior of ``skip_missing`` and ``accessor`` options when ``many=True`` (:issue:`137`). Thanks :user:`3rdcycle`.
- Fix bug that could cause an ``AttributeError`` when nesting schemas with schema-level validators (:issue:`144`). Thanks :user:`vovanbo` for reporting.

1.2.1 (2015-01-11)
++++++++++++++++++

Bug fixes:

- A ``Schema's`` ``error_handler``--if defined--will execute if ``Schema.validate`` returns validation errors (:issue:`121`).
- Deserializing `None` returns `None` rather than raising an ``AttributeError`` (:issue:`123`). Thanks :user:`RealSalmon` for the catch and patch.

1.2.0 (2014-12-22)
++++++++++++++++++

Features:

- Add ``QuerySelect`` and ``QuerySelectList`` fields (:issue:`84`).
- Convert validators in ``marshmallow.validate`` into class-based callables to make them easier to use when declaring fields (:issue:`85`).
- Add ``Decimal`` field which is safe to use when dealing with precise numbers (:issue:`86`).

Thanks :user:`philtay` for these contributions.

Bug fixes:

- ``Date`` fields correctly deserializes to a ``datetime.date`` object when ``python-dateutil`` is not installed (:issue:`79`). Thanks :user:`malexer` for the catch and patch.
- Fix bug that raised an ``AttributeError`` when using a class-based validator.
- Fix ``as_string`` behavior of Number fields when serializing to default value.
- Deserializing ``None`` or the empty string with either a ``DateTime``, ``Date``, ``Time`` or ``TimeDelta`` results in the correct unmarshalling errors (:issue:`96`). Thanks :user:`svenstaro` for reporting and helping with this.
- Fix error handling when deserializing invalid UUIDs (:issue:`106`). Thanks :user:`vesauimonen` for the catch and patch.
- ``Schema.loads`` correctly defaults to use the value of ``self.many`` rather than defaulting to ``False`` (:issue:`108`). Thanks :user:`davidism` for the catch and patch.
- Validators, data handlers, and preprocessors are no longer shared between schema subclasses (:issue:`88`). Thanks :user:`amikholap` for reporting.
- Fix error handling when passing a ``dict`` or ``list`` to a ``ValidationError`` (:issue:`110`). Thanks :user:`ksesong` for reporting.

Deprecation:

- The validator functions in the ``validate`` module are deprecated in favor of the class-based validators (:issue:`85`).
- The ``Arbitrary``, ``Price``, and ``Fixed`` fields are deprecated in favor of the ``Decimal`` field (:issue:`86`).

Support:

- Update docs theme.
- Update contributing docs (:issue:`77`).
- Fix namespacing example in "Extending Schema" docs. Thanks :user:`Ch00k`.
- Exclude virtualenv directories from syntax checking (:issue:`99`). Thanks :user:`svenstaro`.


1.1.0 (2014-12-02)
++++++++++++++++++

Features:

- Add ``Schema.validate`` method which validates input data against a schema. Similar to ``Schema.load``, but does not call ``make_object`` and only returns the errors dictionary.
- Add several validation functions to the ``validate`` module. Thanks :user:`philtay`.
- Store field name and instance on exceptions raised in ``strict`` mode.

Bug fixes:

- Fix serializing dictionaries when field names are methods of ``dict`` (e.g. ``"items"``). Thanks :user:`rozenm` for reporting.
- If a Nested field is passed ``many=True``, ``None`` serializes to an empty list. Thanks :user:`nickretallack` for reporting.
- Fix behavior of ``many`` argument passed to ``dump`` and ``load``. Thanks :user:`svenstaro` for reporting and helping with this.
- Fix ``skip_missing`` behavior for ``String`` and ``List`` fields. Thanks :user:`malexer` for reporting.
- Fix compatibility with python-dateutil 2.3.
- More consistent error messages across DateTime, TimeDelta, Date, and Time fields.

Support:

- Update Flask and Peewee examples.

1.0.1 (2014-11-18)
++++++++++++++++++

Hotfix release.

- Ensure that errors dictionary is correctly cleared on each call to Schema.dump and Schema.load.

1.0.0 (2014-11-16)
++++++++++++++++++

Adds new features, speed improvements, better error handling, and updated documentation.

- Add ``skip_missing`` ``class Meta`` option.
- A field's ``default`` may be a callable.
- Allow accessor function to be configured via the ``Schema.accessor`` decorator or the ``__accessor__`` class member.
- ``URL`` and ``Email`` fields are validated upon serialization.
- ``dump`` and ``load`` can receive the ``many`` argument.
- Move a number of utility functions from fields.py to utils.py.
- More useful ``repr`` for ``Field`` classes.
- If a field's default is ``fields.missing`` and its serialized value is ``None``, it will not be included in the final serialized result.
- Schema.dumps no longer coerces its result to a binary string on Python 3.
- *Backwards-incompatible*: Schema output is no longer an ``OrderedDict`` by default. If you want ordered field output, you must explicitly set the ``ordered`` option to ``True``.
- *Backwards-incompatible*: `error` parameter of the `Field` constructor is deprecated. Raise a `ValidationError` instead.
- Expanded test coverage.
- Updated docs.

1.0.0-a (2014-10-19)
++++++++++++++++++++

Major reworking and simplification of the public API, centered around support for deserialization, improved validation, and a less stateful ``Schema`` class.

* Rename ``Serializer`` to ``Schema``.
* Support for deserialization.
* Use the ``Schema.dump`` and ``Schema.load`` methods for serializing and deserializing, respectively.
* *Backwards-incompatible*: Remove ``Serializer.json`` and ``Serializer.to_json``. Use ``Schema.dumps`` instead.
* Reworked fields interface.
* *Backwards-incompatible*: ``Field`` classes implement ``_serialize`` and ``_deserialize`` methods. ``serialize`` and ``deserialize`` comprise the public API for a ``Field``. ``Field.format`` and ``Field.output`` have been removed.
* Add ``exceptions.ForcedError`` which allows errors to be raised during serialization (instead of storing errors in the ``errors`` dict).
* *Backwards-incompatible*: ``DateTime`` field serializes to ISO8601 format by default (instead of RFC822).
* *Backwards-incompatible*: Remove ``Serializer.factory`` method. It is no longer necessary with the ``dump`` method.
* *Backwards-incompatible*: Allow nesting a serializer within itself recursively. Use ``exclude`` or ``only`` to prevent infinite recursion.
* *Backwards-incompatible*: Multiple errors can be stored for a single field. The errors dictionary returned by ``load`` and ``dump`` have lists of error messages keyed by field name.
* Remove ``validated`` decorator. Validation occurs within ``Field`` methods.
* ``Function`` field raises a ``ValueError`` if an uncallable object is passed to its constructor.
* ``Nested`` fields inherit context from their parent.
* Add ``Schema.preprocessor`` and ``Schema.validator`` decorators for registering preprocessing and schema-level validation functions respectively.
* Custom error messages can be specified by raising a ``ValidationError`` within a validation function.
* Extra keyword arguments passed to a Field are stored as metadata.
* Fix ordering of field output.
* Fix behavior of the ``required`` parameter on ``Nested`` fields.
* Fix serializing keyed tuple types (e.g. ``namedtuple``) with ``class Meta`` options.
* Fix default value for ``Fixed`` and ``Price`` fields.
* Fix serialization of binary strings.
* ``Schemas`` can inherit fields from non-``Schema`` base classes (e.g. mixins). Also, fields are inherited according to the MRO (rather than recursing over base classes). Thanks :user:`jmcarp`.
* Add ``Str``, ``Bool``, and ``Int`` field class aliases.

0.7.0 (2014-06-22)
++++++++++++++++++

* Add ``Serializer.error_handler`` decorator that registers a custom error handler.
* Add ``Serializer.data_handler`` decorator that registers data post-processing callbacks.
* *Backwards-incompatible*: ``process_data`` method is deprecated. Use the ``data_handler`` decorator instead.
* Fix bug that raised error when passing ``extra`` data together with ``many=True``. Thanks :user:`buttsicles` for reporting.
* If ``required=True`` validation is violated for a given ``Field``, it will raise an error message that is different from the message specified by the ``error`` argument. Thanks :user:`asteinlein`.
* More generic error message raised when required field is missing.
* ``validated`` decorator should only wrap a ``Field`` class's ``output`` method.

0.6.0 (2014-06-03)
++++++++++++++++++

* Fix bug in serializing keyed tuple types, e.g. ``namedtuple`` and ``KeyedTuple``.
* Nested field can load a serializer by its class name as a string. This makes it easier to implement 2-way nesting.
* Make Serializer.data override-able.

0.5.5 (2014-05-02)
++++++++++++++++++

* Add ``Serializer.factory`` for creating a factory function that returns a Serializer instance.
* ``MarshallingError`` stores its underlying exception as an instance variable. This is useful for inspecting errors.
* ``fields.Select`` is aliased to ``fields.Enum``.
* Add ``fields.__all__`` and ``marshmallow.__all__`` so that the modules can be more easily extended.
* Expose ``Serializer.OPTIONS_CLASS`` as a class variable so that options defaults can be overridden.
* Add ``Serializer.process_data`` hook that allows subclasses to manipulate the final output data.

0.5.4 (2014-04-17)
++++++++++++++++++

* Add ``json_module`` class Meta option.
* Add ``required`` option to fields . Thanks :user:`DeaconDesperado`.
* Tested on Python 3.4 and PyPy.

0.5.3 (2014-03-02)
++++++++++++++++++

* Fix ``Integer`` field default. It is now ``0`` instead of ``0.0``. Thanks :user:`kalasjocke`.
* Add ``context`` param to ``Serializer``. Allows accessing arbitrary objects in ``Function`` and ``Method`` fields.
* ``Function`` and ``Method`` fields raise ``MarshallingError`` if their argument is uncallable.


0.5.2 (2014-02-10)
++++++++++++++++++

* Enable custom field validation via the ``validate`` parameter.
* Add ``utils.from_rfc`` for parsing RFC datestring to Python datetime object.

0.5.1 (2014-02-02)
++++++++++++++++++

* Avoid unnecessary attribute access in ``utils.to_marshallable_type`` for improved performance.
* Fix RFC822 formatting for localized datetimes.

0.5.0 (2013-12-29)
++++++++++++++++++

* Can customize validation error messages by passing the ``error`` parameter to a field.
* *Backwards-incompatible*: Rename ``fields.NumberField`` -> ``fields.Number``.
* Add ``fields.Select``. Thanks :user:`ecarreras`.
* Support nesting a Serializer within itself by passing ``"self"`` into ``fields.Nested`` (only up to depth=1).
* *Backwards-incompatible*: No implicit serializing of collections. Must set ``many=True`` if serializing to a list. This ensures that marshmallow handles singular objects correctly, even if they are iterable.
* If Nested field ``only`` parameter is a field name, only return a single value for the nested object (instead of a dict) or a flat list of values.
* Improved performance and stability.

0.4.1 (2013-12-01)
++++++++++++++++++

* An object's ``__marshallable__`` method, if defined, takes precedence over ``__getitem__``.
* Generator expressions can be passed to a serializer.
* Better support for serializing list-like collections (e.g. ORM querysets).
* Other minor bugfixes.

0.4.0 (2013-11-24)
++++++++++++++++++

* Add ``additional`` `class Meta` option.
* Add ``dateformat`` `class Meta` option.
* Support for serializing UUID, date, time, and timedelta objects.
* Remove ``Serializer.to_data`` method. Just use ``Serialize.data`` property.
* String field defaults to empty string instead of ``None``.
* *Backwards-incompatible*: ``isoformat`` and ``rfcformat`` functions moved to utils.py.
* *Backwards-incompatible*: Validation functions moved to validate.py.
* *Backwards-incompatible*: Remove types.py.
* Reorder parameters to ``DateTime`` field (first parameter is dateformat).
* Ensure that ``to_json`` returns bytestrings.
* Fix bug with including an object property in ``fields`` Meta option.
* Fix bug with passing ``None`` to a serializer.

0.3.1 (2013-11-16)
++++++++++++++++++

* Fix bug with serializing dictionaries.
* Fix error raised when serializing empty list.
* Add ``only`` and ``exclude`` parameters to Serializer constructor.
* Add ``strict`` parameter and option: causes Serializer to raise an error if invalid data are passed in, rather than storing errors.
* Updated Flask + SQLA example in docs.

0.3.0 (2013-11-14)
++++++++++++++++++

* Declaring Serializers just got easier. The *class Meta* paradigm allows you to specify fields more concisely. Can specify ``fields`` and ``exclude`` options.
* Allow date formats to be changed by passing ``format`` parameter to ``DateTime`` field constructor. Can either be ``"rfc"`` (default), ``"iso"``, or a date format string.
* More useful error message when declaring fields as classes (instead of an instance, which is the correct usage).
* Rename MarshallingException -> MarshallingError.
* Rename marshmallow.core -> marshmallow.serializer.

0.2.1 (2013-11-12)
++++++++++++++++++

* Allow prefixing field names.
* Fix storing errors on Nested Serializers.
* Python 2.6 support.

0.2.0 (2013-11-11)
++++++++++++++++++

* Field-level validation.
* Add ``fields.Method``.
* Add ``fields.Function``.
* Allow binding of extra data to a serialized object by passing the ``extra`` param when initializing a ``Serializer``.
* Add ``relative`` paramater to ``fields.Url`` that allows for relative URLs.

0.1.0 (2013-11-10)
++++++++++++++++++

* First release.
