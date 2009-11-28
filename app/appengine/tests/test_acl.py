# -*- coding: utf-8 -*-
from google.appengine.ext import db
from google.appengine.ext.db import BadValueError

from nose.tools import raises
from gaefy.acl import AclBase, AclRole, AclUser, Acl


def setup_module():
    """Ensures that datastore is empty."""
    for model in [AclBase, AclRole, AclUser]:
        entities = model.all().get()
        assert entities is None or len(entities) == 0


def teardown_module():
    """Removes all test records."""
    for model in [AclBase, AclRole, AclUser]:
        entities = model.all().fetch(100)
        if entities:
            # Delete one by one to also clear memcache.
            for entity in entities:
                entity.delete()


def test_set_rules():
    rules = [
        ('topic_1', 'name_1', True),
        ('topic_1', 'name_2', True),
        ('topic_2', 'name_1', False),
    ]

    # Set rules and save the record.
    base = AclBase(area='test', name='test')
    base.rules = rules
    base.put()

    # Fetch the record again, and compare.
    base = AclBase.get_by_area_and_name('test', 'test')
    assert base.rules == rules

def test_append_rules():
    rules = [
        ('topic_1', 'name_1', True),
        ('topic_1', 'name_2', True),
        ('topic_2', 'name_1', False),
    ]

    # Set rules and save the record.
    base = AclBase(area='test', name='test', rules=rules)
    base.put()

    # Fetch the record again, and compare.
    base = AclBase.get_by_area_and_name('test', 'test')
    extra_rule = ('topic_3', 'name_3', True)
    rules.append(extra_rule)
    base.rules.append(extra_rule)
    base.put()

    base = AclBase.get_by_area_and_name('test', 'test')
    assert base.rules == rules

def test_set_rules2():
    rules = [
        ('topic_1', 'name_1', True),
        ('topic_1', 'name_2', True),
        ('topic_2', 'name_1', False),
    ]

    # Set rules and save the record.
    base = AclBase(area='test', name='test', rules=rules)
    base.put()

    # Fetch the record again, and compare.
    base = AclBase.get_by_area_and_name('test', 'test')
    assert base.rules == rules

@raises(BadValueError)
def test_set_invalid_rules():
    rules = [
        ('topic_1', 'name_1', True),
        ('topic_1', 'name_2', True),
        ('topic_2', 'name_1', 'invalid'),
    ]

    # Set rules and save the record.
    base = AclBase(area='test', name='test')
    base.rules = rules
    base.put()

@raises(ValueError)
def test_set_invalid_rules_2():
    rules = [
        ('topic_1', 'name_1', True),
        ('topic_1', 'name_2', True),
        ('topic_2', 'name_1'),
    ]

    # Set rules and save the record.
    base = AclBase(area='test', name='test')
    base.rules = rules
    base.put()

def test_set_empty_rules():
    rules = []
    # Set rules and save the record.
    base = AclBase(area='test', name='test')
    base.rules = rules
    base.put()

def test_example():
    # Create a new 'admin' role.
    # Each rule is a tuple ('topic', 'name', 'flag'), where flag is as boolean
    # to allow or disallow access. Wildcard '*' can be used to match all
    # topics and/or names.
    rules = [('*', '*', True)]
    acl_role = AclRole(area='my_area', name='admin', rules=rules)
    acl_role.put()

    # Assign users 'user_1' and 'user_2' to the 'admin' role.
    acl_user = AclUser(area='my_area', name='user_1', roles=['admin'])
    acl_user.put()
    acl_user = AclUser(area='my_area', name='user_2', roles=['admin'])
    acl_user.put()

    # Restrict 'user_2' from accessing a specific rule, so now access is
    # granted to everything except this rule.
    acl_user = AclUser.get_by_area_and_name('my_area', 'user_2')
    acl_user.rules.append(('UserAdmin', 'put', False))
    acl_user.put()

    # Check 'user_2' permission.
    acl = Acl(area='my_area', user='user_2')
    assert acl.has_access(topic='UserAdmin', name='put') is False
    assert acl.has_access(topic='UserAdmin', name='get') is True
    assert acl.has_access(topic='AnythingElse', name='put') is True
