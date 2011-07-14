import unittest2


class TestLimoneZODB(unittest2.TestCase):

    def setUp(self):
        import colander

        class Friend(colander.TupleSchema):
            rank = colander.SchemaNode(colander.Int(),
                                      validator=colander.Range(0, 9999))
            name = colander.SchemaNode(colander.String())

        class Phone(colander.MappingSchema):
            location = colander.SchemaNode(
                colander.String(),
                validator=colander.OneOf(['home', 'work']))
            number = colander.SchemaNode(colander.String())

        class Friends(colander.SequenceSchema):
            friend = Friend()

        class Phones(colander.SequenceSchema):
            phone = Phone()

        class Person(colander.MappingSchema):
            name = colander.SchemaNode(colander.String())
            age = colander.SchemaNode(colander.Int(),
                                     validator=colander.Range(0, 200))
            friends = Friends()
            phones = Phones()

        self.schema = Person

    def assert_object_is_persistent(self, obj):
        import persistent
        from persistent.list import PersistentList
        self.assertIsInstance(obj, persistent.Persistent)
        self.assertIsInstance(obj.phones._data, PersistentList)
        self.assertIsInstance(
            obj.phones[0], persistent.Persistent)

    def test_content_type(self):
        import limone_zodb

        @limone_zodb.content_type(self.schema)
        class TestType(object):
            foo = 'bar'

        obj = TestType(name='Jake', age=43, phones=[
            {'location': 'home', 'number': '555-1212'},
            {'location': 'work', 'number': '555-2121'}])
        self.assertEqual(obj.foo, 'bar')
        self.assert_object_is_persistent(obj)

    def test_content_type_already_persistent(self):
        import limone_zodb
        import persistent

        @limone_zodb.content_type(self.schema)
        class TestType(persistent.Persistent):
            foo = 'bar'

        obj = TestType(name='Jake', age=43, phones=[
            {'location': 'home', 'number': '555-1212'},
            {'location': 'work', 'number': '555-2121'}])
        self.assertEqual(obj.foo, 'bar')
        self.assert_object_is_persistent(obj)

    def test_content_schema(self):
        import limone_zodb
        TestType = limone_zodb.content_schema(self.schema)
        self.assert_object_is_persistent(
            TestType(name='Jake', age=43, phones=[
                {'location': 'home', 'number': '555-1212'},
                {'location': 'work', 'number': '555-2121'}]))

    def test_make_content_type(self):
        import limone_zodb
        TestType = limone_zodb.make_content_type(self.schema, 'TestType')
        self.assert_object_is_persistent(
            TestType(name='Jake', age=43, phones=[
                {'location': 'home', 'number': '555-1212'},
                {'location': 'work', 'number': '555-2121'}]))


class FunctionalTest(unittest2.TestCase):

    def setUp(self):
        import colander
        import limone
        import limone_zodb

        class Friend(colander.TupleSchema):
            rank = colander.SchemaNode(colander.Int(),
                                      validator=colander.Range(0, 9999))
            name = colander.SchemaNode(colander.String())

        class Phone(colander.MappingSchema):
            location = colander.SchemaNode(
                colander.String(),
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

        self.registry = registry = limone.Registry()
        registry.register_content_type(Person)
        registry.hook_import()

        self.content_type = Person

        import os
        import tempfile
        self.tmp = tmp = tempfile.mkdtemp('.tests-limone_zodb')
        self.dbfile = dbfile = os.path.join(tmp, 'data.fs')
        self.open_zodb()

    def open_zodb(self):
        from ZODB.DB import DB
        from ZODB.FileStorage import FileStorage
        self.db = DB(FileStorage(self.dbfile))
        self.conn = self.db.open()
        self.root = self.conn.root()

    def close_zodb(self):
        self.conn.close()
        self.db.close()

    def reopen_zodb(self):
        self.close_zodb()
        self.open_zodb()

    def tearDown(self):
        import shutil
        self.close_zodb()
        self.registry.unhook_import()
        shutil.rmtree(self.tmp)

    def test_shallow_changes_persist(self):
        import transaction
        jake = self.content_type(name='Jake', age=43)
        self.root['jake'] = jake
        transaction.commit()
        self.reopen_zodb()
        self.assertEqual(self.root['jake'].age, 43)
        self.root['jake'].age = 33
        transaction.commit()
        self.reopen_zodb()
        self.assertEqual(self.root['jake'].age, 33)

    def test_sequence_changes_persist(self):
        import transaction
        jake = self.content_type(
            name='Jake', age=43, phones=[
                {'location': 'home', 'number': '555-1212'}])
        self.root['jake'] = jake
        transaction.commit()
        self.reopen_zodb()
        self.assertEqual(self.root['jake'].phones[0].location, 'home')
        self.assertEqual(self.root['jake'].phones[0].number, '555-1212')
        self.root['jake'].phones[0] = {'location': 'work', 'number': '555-2121'}
        transaction.commit()
        self.reopen_zodb()
        self.assertEqual(self.root['jake'].phones[0].location, 'work')
        self.assertEqual(self.root['jake'].phones[0].number, '555-2121')

    def test_mapping_changes_persist(self):
        import transaction
        jake = self.content_type(
            name='Jake', age=43, phones=[
                {'location': 'home', 'number': '555-1212'}])
        self.root['jake'] = jake
        transaction.commit()
        self.reopen_zodb()
        self.root['jake'].phones[0].location = 'work'
        self.root['jake'].phones[0].number = '555-2121'
        transaction.commit()
        self.reopen_zodb()
        self.assertEqual(self.root['jake'].phones[0].location, 'work')
        self.assertEqual(self.root['jake'].phones[0].number, '555-2121')

