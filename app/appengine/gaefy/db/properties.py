# -*- coding: utf-8 -*-
"""
    gaefy.db.properties
    ~~~~~~~~~~~~~~~~~~~

    Extra properties for App Engine Models.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import csv, pickle, simplejson
from cStringIO import StringIO

from google.appengine.ext import db
from google.appengine.api import datastore_errors

class SerialProperty(db.Property):
    """Overrides make_value_from_form() provided in GAE, which casts the
    property value to a string. This is not desired for some properties, and
    enables the use of CsvProperty in MultiValueField's.
    """
    def make_value_from_form(self, value):
        return value

    def get_value_for_form(self, instance):
        return getattr(instance, self.name)


class CsvProperty(SerialProperty):
    """A special property that accepts a list or tuple as value, and stores the
    data in CSV format using the db.Text data_type. Each item in the list must
    be a iterable representing fields in a CSV row. The value is converted back
    to a list of tuples when read.
    """
    data_type = db.Text

    def __init__(self, csv_params={}, field_count=None, default=None, **kwargs):
        """Constructs CsvProperty.

        Args:
          csv_params: CSV formatting parameters. See:
            http://docs.python.org/library/csv.html#csv-fmt-params
          field_count: If set, enforces all items to have this number of fields.
        """
        self._require_parameter(kwargs, 'indexed', False)
        kwargs['indexed'] = True
        if default is None:
            default = []
        self.field_count = field_count
        self.csv_params = csv_params
        super(CsvProperty, self).__init__(default=default, **kwargs)

    def get_value_for_datastore(self, model_instance):
        """Converts the list to CSV."""
        value = super(CsvProperty, self).get_value_for_datastore(model_instance)

        if value is not None:
            csvfile = StringIO()
            writer = csv.writer(csvfile, **self.csv_params)
            writer.writerows(value)
            value = csvfile.getvalue().strip()
            csvfile.close()
            return db.Text(value)

    def make_value_from_datastore(self, value):
        """Converts the CSV data back to a list."""
        values = []

        if value is not None:
            reader = csv.reader(StringIO(str(value)), **self.csv_params)
            for item in reader:
                values.append(item)

        return values

    def validate(self, value):
        """Validates the property on __set__."""
        value = super(CsvProperty, self).validate(value)
        if value is not None:
            if not isinstance(value, (list, tuple)):
                raise db.BadValueError('Property %s must be a list or tuple.' %
                    (self.name))

            value = self.validate_list_contents(value)

        return value

    def validate_list_contents(self, value):
        """Validates that all rows are of the correct type and have a
        required number of fields.

        Returns:
          The validated list.

        Raises:
          BadValueError if the list has items that are not list or tuple
          instances or doesn't have the required length.
        """
        for item in value:
            if not isinstance(item, (list, tuple)):
                raise db.BadValueError(
                    'Items in the %s list must be a list or tuple.' %
                    (self.name))

            if self.field_count and len(item) != self.field_count:
                raise db.BadValueError(
                    'Items in the %s list must have a length of %d.' %
                    (self.name, self.length))

        return value

    def empty(self, value):
        return value is None


class EnumProperty(SerialProperty):
    """Maps a list of strings to be saved as int. The property is set or get
    using the string value, but it is stored using its index in the 'choices'
    list.
    """
    data_type = int

    def __init__(self, choices=None, **kwargs):
        if not isinstance(choices, list):
            raise TypeError('Choices must be a list.')
        super(EnumProperty, self).__init__(choices=choices, **kwargs)

    def get_value_for_datastore(self, model_instance):
        value = super(EnumProperty, self).get_value_for_datastore(
            model_instance)
        if value is not None:
            return int(self.choices.index(value))

    def make_value_from_datastore(self, value):
        if value is not None:
            return self.choices[int(value)]

    def empty(self, value):
        return value is None


class JsonProperty(SerialProperty):
    """Stores a dictionary automatically encoding to JSON on set and decoding
    on get.
    """
    data_type = db.Text

    def __init__(self, *args, **kwds):
        self._require_parameter(kwds, 'indexed', False)
        kwds['indexed'] = True
        super(JsonProperty, self).__init__(*args, **kwds)

    def get_value_for_datastore(self, model_instance):
        """Encodes the value to JSON."""
        value = super(JsonProperty, self).get_value_for_datastore(
            model_instance)
        if value is not None:
            return db.Text(simplejson.dumps(value))

    def make_value_from_datastore(self, value):
        """Decodes the value from JSON."""
        if value is not None:
            return simplejson.loads(value)

    def validate(self, value):
        if value is not None and not isinstance(value, (dict, list, tuple)):
            raise db.BadValueError('Property %s must be a dict, list or '
                'tuple.' % self.name)

        value = super(JsonProperty, self).validate(value)
        return value


class PickledProperty(SerialProperty):
    """Stores a native Python object, pickling automatically on set and
    unpickling on get.
    """
    data_type = db.Blob

    def __init__(self, require_type=None, **kwargs):
        """Constructs PickledProperty.

        Args:
          require_type: requires the property value to be of this type.
        """
        self._require_parameter(kwargs, 'indexed', False)
        kwargs['indexed'] = True
        self.require_type = require_type
        super(PickledProperty, self).__init__(**kwargs)

    def get_value_for_datastore(self, model_instance):
        value = super(PickledProperty, self).get_value_for_datastore(
            model_instance)
        if value is not None:
            return db.Blob(pickle.dumps(value))

    def make_value_from_datastore(self, value):
        if value is not None:
            return pickle.loads(value)

    def validate(self, value):
        value = super(PickledProperty, self).validate(value)
        if value is not None and self.require_type and \
            not isinstance(value, self.require_type):
                raise datastore_errors.BadValueError(
                    'Property %s must be of type "%s".' % (self.name,
                        self.require_type))

        return value


class SlugProperty(db.StringProperty):
    """Undocumented"""
    def __init__(self, to_slug=None, slug_function=None, **kwargs):
        self.to_slug = to_slug
        self.slug_function = slug_function
        super(SlugProperty, self).__init__(**kwargs)

    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self

        value = getattr(model_instance, self._attr_name())

        if value is not None:
            value = self.slug_function(value)

        if not value and self.to_slug:
            value = self.slug_function(getattr(model_instance, self.to_slug))

        if value:
            return value

        return self.default
