from datetime import datetime


class DatabaseObject:

    database_manager = None
    local_exclusions = []

    id = None

    def __init__(self, database_manager):
        self.database_manager = database_manager

    def __iter__(self):
        exclusions = self.local_exclusions + [
            'database_manager',
            'local_exclusions',
        ]
        for property, value in vars(self).items():
            if property not in exclusions:
                yield(property, value)

    def from_dict(self, database_manager, data):
        exclusions = self.local_exclusions + [
            'database_manager',
            'local_exclusions',
            'ctime',
            'mtime'
        ]
        self.database_manager = database_manager
        for key, value in data.items():
            if key not in exclusions:
                setattr(self, key, value)
        if 'ctime' in data:
            self.ctime = DatabaseObject.get_datetime_from_string(
                data['ctime']
            )
        if 'mtime' in data:
            self.mtime = DatabaseObject.get_datetime_from_string(
                data['mtime']
            )

    def to_dict(self):
        exclusions = self.local_exclusions + [
            'database_manager',
            'local_exclusions',
            'ctime',
            'mtime'
        ]
        data = {}
        for property, value in vars(self).iteritems():
            if property not in exclusions:
                    data[property] = value

        if 'ctime' in data and isinstance(data['ctime'], datetime):
            self.ctime = DatabaseObject.get_datetime_from_string(
                data['ctime']
            )
        if 'mtime' in data and isinstance(data['mtime'], datetime):
            self.mtime = DatabaseObject.get_datetime_from_string(
                data['mtime']
            )

        return data

    def insert_if_not_exists(self):
        self.id = self.database_manager.insert_if_not_exists(self)
        return self.id

    def save(self):
        self.id = self.database_manager.save(self)
        return self.id

    def insert(self):
        self.id = self.database_manager.insert(self)
        return self.id

    def update(self):
        result = self.database_manager.update(self)
        return result

    @staticmethod
    def get_boolean_from_string(input):
        result = False
        if input == True:
            result = input
        elif isinstance(str, int):
            result = input == 1
        elif isinstance(input, str):
            lower_input = input.lower()
            affirmative_values = ["true", "yes", "1"]
            result = lower_input in affirmative_values
        else:
            result = False
        return result

    def get_datetime_from_string(str):
        return datetime.strptime(str, '%Y-%m-%d %H:%M:%S')

    def get_string_from_datetime(dt_object):
        return dt_object.strftime('%Y-%m-%d %H:%M:%S')
