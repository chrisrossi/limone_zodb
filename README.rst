===========
Limone ZODB
===========

`Limone ZODB` is an extension of `Limone`_ which generates content types that
are persistable via ZODB.  Usage is the same as `Limone` except that the
decorators and `make_content_type` function are imported from the `limone_zodb`
package instead of the `limone` package::

    import colander
    import limone_zodb
    import persistent

    class Friend(colander.TupleSchema):
        rank = colander.SchemaNode(colander.Int(),
                                  validator=colander.Range(0, 9999))
        name = colander.SchemaNode(colander.String())

    class Phone(colander.MappingSchema):
        location = colander.SchemaNode(colander.String(),
                                      validator=colander.OneOf(['home', 'work']))
        number = colander.SchemaNode(colander.String())

    class Friends(colander.SequenceSchema):
        friend = Friend()

    class Phones(colander.SequenceSchema):
        phone = Phone()

    @limone_zodb.content_schema
    class Person(colander.MappingSchema):
        name = colander.SchemaNode(colander.String())
        age = colander.SchemaNode(colander.Int(),
                                 validator=colander.Range(0, 200))
        friends = Friends()
        phones = Phones()

    jake = Person(name='Jake', age=21)
    assert isinstance(jake, persistent.Persistent)

.. _`Limone`: http://pypi.python.org/pypi/limone


Rationale
---------

Naively, one might presume that using `persistent.Persistent` as a base class
for the content type would be sufficient. What can happen, though, is you can
find that certain changes to a content object fail to persist. For example,
without using `limone_zodb` we might have just done something more like::

    import limone
    import persistent

    @limone.content_type(Person)
    class PersistentPerson(persistent.Persistent):
        pass

    jake = PersistentPerson(name='Jake', age=21)

Than, later, in another transaction::

    jake.age = 22  # This will persist just fine

While this will work fine if you only change direct attributes of the content
object, if you change deep attributes, like `friends` or `phones` in the
example above, those won't necessarily persist automatically.  This is not due
to anything particular to `Limone`.  This behavior can be observed with any
object containing nested data structures.  Let's take a look at this example
which doesn't use `Limone`::

    import persistent

    class C(persistent.Persistent):
        def __init__(self):
            self.foo = 'Hello'
            self.bars = ['tiki', 'biker']

    o = C()

Assuming we have stored the instance `o` in the ZODB and retrieved it another
transaction, we could try to modify it.  If we change the value of `o.foo` and
commit our transactoin, a new copy of `o` will be written to the ZODB and our
change will have been saved::

    import transaction

    o.foo = 'Howdy'  # This change will persist
    transaction.commit()

If, on the other hand, we add a new value to `o.bars`, then this change alone
will not be sufficient to cause a new value of `o` to be written to the ZODB
and the change will not be persisted when the transaction is committed::

    o.bars.append('lesbian')  # Change does not persist
    transaction.commit()

The reason for this lies in how `persistent.Persistent` object work.
`persistent.Persistent` overrides the `__setattr__` method of `object` so that
when an attribute is set on a persistent object, that object is advertised to
the transaction as having been changed, and a new copy is written when the
transaction is committed.  `bars`, though, is just a regular old Python list
that doesn't know anything about persistence.  Mutating that list does not
advertise the change to the transaction, so the ZODB doesn't know that there is
anything new to be written to the database.

For this exact same reason, changes to a `Limone` content object that only
involve a nested data structure, will fail to advertise to the transaction
that a change has occurred.  If these are the only changes to an object, that
object's new state will not be written to the database when the transaction is
committed.

`Limone ZODB` gets around this problem by passing a metaclass into the normal
`Limone` content type generation process which makes sure that making any
change to a `Limone ZODB` content object, at any level of the content
structure, will cause the change to be persisted automatically, without any
hoops to be jumped through by the developer.
