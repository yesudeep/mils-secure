# -*- coding: utf-8 -*-
"""
    gaefy.db.unique_model
    ~~~~~~~~~~~~~~~~~~~~~

    A Model mixin that validates unique properties.

    One limitation is that the entity with unique properties *must have* a
    key_name. Example:

        class MyModel(UniqueModelMixin, db.Model):
            # Define a list of unique contraints for this model. In this case,
            # property 'name' is unique, but the uniqueness can also be set to
            # a group of properties, as in:
            #
            #     _uniques = [('name', 'surname')]
            #
            # Also, several unique constraints can be set for a single model:
            #
            #     _uniques = [('name', 'surname'), ('email',)]
            _uniques = [('name',)]

            name = db.StringProperty(required=True)
            surname = db.StringProperty(required=True)
            email = db.EmailProperty(required=True)

        entity = MyModel(key_name='something', name='foo')
        entity.put()

        # This will raise an exception: 'name' must be unique.
        entity = MyModel(key_name='another_key', name='foo')
        entity.put()

    Based on http://uniquemodel.googlecode.com/, by Benjamin Burns, released
    under the MIT license. A bit more efficient and error prone, as the entity
    is not saved before the validation occurs, and UniqueProperty entities are
    only saved/deleted if an entity is new or their unique properties were
    changed.

    Authors:
        Benjamin Burns, Ocean Research & Conservation Association
            <http://www.teamorca.com>
        Rodrigo Moraes <http://www.tipfy.org>
"""
from hashlib import md5
from google.appengine.ext import db

class UniqueModelMixin(object):
    """A mixin class that overrides db.Model's put() and delete() to ensure
    uniqueness for tuples of properties.
    """
    # A list of property tuples that have unique values.
    # The uniqueness can be set for a single or multiple properties, as in:
    #
    #     _uniques = [('name', 'surname')]
    #
    # Also, several unique constraints can be set for a single model:
    #
    #     _uniques = [('name', 'surname'), ('email',)]
    _uniques = []

    def put(self):
        _validate_uniques(self, self._uniques)
        return super(UniqueModelMixin, self).put()

    def delete(self):
        _delete_uniques(self)
        return super(UniqueModelMixin, self).delete()


class UniqueConstraintViolatedError(Exception):
    """Raised on put() if a uniqueness constraint defined by a tuple of
    properties is violated.
    """


class ExplicitKeyNameError(Exception):
    """Raised if a key_name is explicitly defined in __init__ for classes in
    this module that disallow this.
    """


class UniquePropertyKind(db.Model):
    """Entities of this kind are roots for entity groups of UniqueProperty.
    No property is defined because only the key_name is used.
    """


class UniqueProperty(db.Model):
    """Stores tuples of unique properties for a given UniquePropertyKind."""
    # Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    # Unique property names as a string.
    props = db.StringProperty(required=True)
    # Hash of the property values in the tuple, concatenated.
    values = db.StringProperty(required=True)
    # Instance of Model on which this tuple of properties is unique.
    reference = db.ReferenceProperty(required=True,
        collection_name='unique_properties')

    def __init__(self, parent=None, key_name=None, *args, **kwargs):
        if key_name is not None:
            raise ExplicitKeyNameError, 'key_name must be set implicitly.'

        key_name = '%s:%s' % (kwargs['props'], kwargs['values'])
        super(UniqueProperty, self).__init__(parent=parent, key_name=key_name,
            *args, **kwargs)


def _validate_uniques(entity, unique_tuples):
    """Validates that a set of properties in this entity are unique."""
    # A dictionary of 'tuple_as_string':UniqueProperty for the entity.
    entity_uniques = {}
    if entity.is_saved():
        for unique in entity.unique_properties:
            entity_uniques[unique.props] = unique

    to_save = []
    to_delete = []
    for unique_tuple in unique_tuples:
        # Convert the properties tuple to a string.
        props = ','.join(unique_tuple)

        # Build a hash for the values.
        string = ''
        for prop in unique_tuple:
            string += str(getattr(entity, prop))

        values = md5(string).hexdigest()

        unique = False
        if props in entity_uniques:
            # Check if UniqueProperty values were changed.
            if entity_uniques[props].values == values:
                # Values are the same. Keep UniqueProperty.
                unique = True
            else:
                # Values were changed. Delete UniqueProperty.
                to_delete.append(entity_uniques[props])

        if not unique:
            # Add these values to datastore.
            to_save.append((props, values))

    if to_save:
        # Get the root entity for the UniqueProperty tuples.
        kind = UniquePropertyKind.get_or_insert(entity.__class__.kind())

        # Build the UniqueProperty's to be saved.
        to_save = [UniqueProperty(props=props, values=values, reference=entity,
            parent=kind) for props, values in to_save]

        keys_to_save = [entity.key() for entity in to_save]
        db.run_in_transaction(_save_uniques, keys_to_save, to_save, to_delete)


def _save_uniques(keys_to_save, to_save, to_delete):
    """Used to save and delete UniqueProperty's transactionally."""
    # First, remove entities that were changed.
    if to_delete:
        db.delete(to_delete)

    # Check if the unique properties are already saved.
    entities = UniqueProperty.get(keys_to_save)
    for entity in entities:
        if entity is not None:
            # Values already exist.
            raise UniqueConstraintViolatedError

    db.put(to_save)


def _delete_uniques(entity):
    """Deletes the UniqueProperty's for an entity."""
    for unique in entity.unique_properties:
        db.delete(unique)


def delete_unique(model, properties):
    kind = UniquePropertyKind.get_or_insert(model.kind())

    props = ','.join([prop for prop, value in properties])
    values = ''.join([value for prop, value in properties])
    values = md5(values).hexdigest()
    key_name = '%s:%s' % (props, values)

    entity = UniqueProperty.get_by_key_name(key_name, parent=kind)
    if entity:
        entity.delete()
        return True
    return False
