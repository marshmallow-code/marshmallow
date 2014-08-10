.. _deserialization:
.. module:: marshmallow

Deserialization
===============

**In construction**

The Basics
----------


.. code-block:: python

    from marshmallow import Serializer, fields

    class AccountSerializer(Serializer):
        account_type = fields.Enum(['checking', 'savings'])
        name = fields.String()
        balance = fields.Fixed(2)
        date_created = fields.DateTime()

    account_data = {
        'name': 'For a rainy day',
        'balance': '42',
        'date_created': '2014-08-10T06:58:55.276725',
    }
    deserialized = AccountSerializer().deserialize(account_data)
    # {
    #     'name': 'For a rainy day',
    #     'balance': '42.00',
    #     'date_created': datetime.datetime(2014, 8, 10, 6, 58, 55, 276725)
    # }


.. code-block:: python

    import datetime as dt

    class Account(object):
        def __init__(self, name, account_type='checking', balance=0.0, date_created=None):
            self.name = name
            self.account_type = account_type
            self.balance = balance
            self.date_created = date_created or dt.datetime.utcnow()

        def __repr__(self):
            return '<Account({self.name}, balance={self.balance})>'.format(self=self)

    # Same as above, but this time we define ``make_object``
    class AccountSerializer2(Serializer):
        account_type = fields.Enum(['checking', 'savings'])
        name = fields.String()
        balance = fields.Fixed(2)
        date_created = fields.DateTime()

        def make_object(self, data):
            return Account(**data)

    account_data = {
        'name': 'For a rainy day',
        'balance': '42',
        'date_created': '2014-08-10T06:58:55.276725',
    }
    deserialized = AccountSerializer2().deserialize(account_data)
    # <Account(For a rainy day, balance=42.00)>

A :exc:`DeserializationError <marshmallow.exceptions.DeserializationError>` is raised if invalid data are passed.

.. code-block:: python

    invalid_account = {
        'account_type': 'notvalid',
    }
    AccountSerializer().deserialize(invalid_account)
    # DeserializationError: 'notvalid' is not a valid choice for this field.
