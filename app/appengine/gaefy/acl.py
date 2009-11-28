# -*- coding: utf-8 -*-
"""
    gaefy.acl
    ~~~~~~~~~

    Simple Access Control List system.

    This is used to store permissions for anything that requires some
    level of restriction, like datastore models or handlers. Access permissions
    can be grouped in roles for convenience, so that a new user can be assigned
    to a role directly instead of having all his permissions defined manually.
    Individual access permissions can then override or extend the role
    permissions.

    For example, create a 'admin' role with full access and assign users to it:

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
    assert acl.has_access(topic='AnythingElse', name='put') is True

    The ACL object should be created once after a user is detected, so that
    it becomes available for the app to do all necessary permissions checkings.

    Based on concept from Solar's Access and Role classes: http://solarphp.com.

    :copyright: Paul M. Jones <pmjones@solarphp.com>
    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import uuid
from hashlib import md5
from google.appengine.ext import db
from google.appengine.api import memcache


class AclRules(list):
    """Wraps rule_topic, rule_name and rule_flag for AclBase entities. Each
    item must be a tuple (topic, name, flag).
    """


class AclBase(db.Model):
    # Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    # Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    # Area to which this role is related.
    area = db.StringProperty(required=True)
    # Role name or user identifier.
    name = db.StringProperty(required=True)
    # Lists of rules. Each rule is a tuple (topic, name, flag), stored as three
    # list properties. These properties should not be set one by one. Instead,
    # use the property `rules` and set a tuple (topic, name, flag) - this way
    # they are kept in sync. On put() the tuples are expanded into these list
    # properties.
    rule_topic = db.StringListProperty()
    rule_name = db.StringListProperty()
    rule_flag = db.ListProperty(bool)

    def __init__(self, *args, **kwargs):
        rules = kwargs.pop('rules', None)
        area = kwargs.get('area', None)
        name = kwargs.get('name', None)
        if not area or not name:
            raise ValueError('Properties area and name are required')

        kwargs['key_name'] = self.create_key_name(area, name)
        super(AclBase, self).__init__(*args, **kwargs)

        if rules is None:
            rules = zip(self.rule_topic, self.rule_name, self.rule_flag)

        self._rules = AclRules(rules)

    def get_rules(self):
        return self._rules

    def set_rules(self, rules):
        self._rules = AclRules(rules)

    # Convenience property to keep rule_topic, rule_name and rule_flag in sync.
    rules = property(get_rules, set_rules)

    @classmethod
    def create_key_name(cls, area, name):
        """Returns this entity's key name, also used as memcache key."""
        return '%s:%s' % (str(area), str(name))

    @classmethod
    def get_by_area_and_name(cls, area, name):
        """Returns a role entity with a given role name in a given area."""
        return cls.get_by_key_name(cls.create_key_name(area, name))

    def expand_rules(self):
        """Unzips the rules property into the model properties."""
        if self._rules:
            topics, names, flags = zip(*self._rules)
            self.rule_topic = list(topics)
            self.rule_name = list(names)
            self.rule_flag = list(flags)

    def put(self):
        """Saves the entity and cleans the cache."""
        self.expand_rules()
        cache_key = self.create_key_name(self.area, self.name)
        memcache.delete(cache_key, namespace=self.__class__.__name__)
        super(AclBase, self).put()

    def delete(self):
        """Deletes the entity and cleans the cache."""
        cache_key = self.create_key_name(self.area, self.name)
        memcache.delete(cache_key, namespace=self.__class__.__name__)
        super(AclBase, self).delete()

    def rule_exists(self, topic, name, flag):
        """Checks if a given rule exists in this role. Used to build forms
        for saved roles, when you need to know if a rule is included or not."""
        return rule_exists(self, topic, name, flag)


class AclRole(AclBase):
    """Stores rules for a given role."""
    @classmethod
    def get_rules(cls, area, name):
        """Returns the rules for a given role name in a given area."""
        key = cls.create_key_name(area, name)
        namespace = cls.__name__
        res = memcache.get(key, namespace=namespace)

        if not res:
            entity = cls.get_by_key_name(key)
            if not entity:
                return []

            res = entity.rules
            memcache.set(key, res, namespace=namespace)

        return res

    def put(self):
        """Saves the entity and create a new cache lock."""
        AclRoleLock.create_lock()
        super(AclRole, self).put()


class AclRoleLock(db.Model):
    """Creates a lock for cached role rules that avoids having to fetch role
    rules for every Acl instance. When a role is inserted or updated, the lock
    value changes. All users must then have the role rules cache reseted,
    and the lock is the key to check if the cache is updated.
    """
    LOCK_NAME = 'the_lock'
    lock = db.StringProperty()

    @classmethod
    def get_rules(cls, area, roles):
        namespace = cls.__name__
        key = '%s:%s' % (str(area), md5(str(roles)).hexdigest())

        res = memcache.get_multi([key, cls.LOCK_NAME], namespace=namespace)
        rules = res.get(key, None)
        lock = res.get(cls.LOCK_NAME, None)

        if not lock:
            the_lock = db.get(db.Key.from_path(cls.kind(), cls.LOCK_NAME))
            if the_lock:
                lock = the_lock.lock
                memcache.set(cls.LOCK_NAME, the_lock.lock, namespace=namespace)
            else:
                lock = cls.create_lock()

        if rules and rules.get('lock', None) == lock:
            return rules.get('rules')

        # Rules not found or lock didn't match. Fetch new rules.
        rules = []
        for role in roles:
            rules.extend(AclRole.get_rules(area, role))

        memcache.set(key, {'rules': rules, 'lock': lock}, namespace=namespace)
        return rules

    @classmethod
    def create_lock(cls):
        the_lock = cls(key_name=cls.LOCK_NAME, lock=uuid.uuid4().hex)
        the_lock.put()
        memcache.set(cls.LOCK_NAME, the_lock.lock, namespace=cls.__name__)
        return the_lock.lock


class AclUser(AclBase):
    """Stores access roles and rules for a given user."""
    # List of AclRole names.
    roles = db.StringListProperty()

    @classmethod
    def get_acl(cls, area, user):
        roles, rules = cls.get_roles_and_rules(area, user)
        if roles:
            role_rules = AclRoleLock.get_rules(area, roles)
            rules.extend(role_rules)

        return roles, rules

    @classmethod
    def get_roles_and_rules(cls, area, user):
        """Returns a tuple (roles, rules) for a given user in a given area."""
        key = cls.create_key_name(area, user)
        namespace = cls.__name__
        res = memcache.get(key, namespace=namespace)

        if not res:
            entity = cls.get_by_key_name(key)
            if not entity:
                return ([], [])

            res = (entity.roles, entity.rules)
            memcache.set(key, res, namespace=namespace)

        return res


class Acl(object):
    """Loads access rules and roles for a given user in a given area and
    provides a centralized interface to check permissions."""
    def __init__(self, area, user):
        """Loads access privileges and roles for a given user."""
        if area and user:
            self._roles, self._rules = AclUser.get_acl(area, user)
        else:
            self.reset()

    def reset(self):
        """Resets the currently loaded access rules and user roles."""
        self._rules = []
        self._roles = []

    def is_one(self, role):
        """Check to see if a user is in a role."""
        return role in self._roles

    def is_any(self, roles):
        """Check to see if a user is in any of the listed roles."""
        for role in roles:
            if role in self._roles:
                return True
        return False

    def is_all(self, roles):
        """Check to see if a user is in all of the listed roles."""
        for role in roles:
            if role not in self._roles:
                return False
        return True

    def has_any_access(self):
        """Checks if the user has any access or roles."""
        if self._rules or self._roles:
            return True
        return False

    def has_access(self, topic='*', name='*'):
        """Tells whether or not to allow access to a class/action combination.
        """
        for rule_topic, rule_name, rule_flag in self._rules:
            match1 = (rule_topic == topic or rule_topic == '*')
            match2 = (rule_name == name or rule_name == '*')
            if match1 and match2:
                # Class and action matched, so return the flag.
                return rule_flag

        # No matching params, so deny.
        return False


def rule_exists(entity, topic, name, flag):
    """Checks if a given rule exists in an entity. Used to build forms, when
    you need to know if a rule is included or not.

    `entity` can be AclRole or AclUser instance.
    """
    for rule_topic, rule_name, rule_flag in entity.rules:
        if rule_topic == topic and rule_name == name and rule_flag == flag:
            return True

    return False
