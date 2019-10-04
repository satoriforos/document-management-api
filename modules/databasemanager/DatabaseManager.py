import re
import copy
import base64
import pymysql


class DatabaseManager:

    database = None
    in_verbose_mode = True
    in_debug_mode = False

    def __init__(
        self,
        database=None,
        in_verbose_mode=False,
        host=None,
        port=None,
        user=None,
        password=None,
        charset=None,
        db=None
    ):
        if database is not None:
            self.database = database
        self.in_verbose_mode = in_verbose_mode
        self.say("In verbose mode")
        if host is not None and user is not None and password is not None:
            self.connect(
                host,
                user,
                password,
                port=port,
                charset=charset,
                db=db
            )

    def __del__(self):
        if self.database is not None:
            self.database.close()

    def connect(
        self,
        host,
        user,
        password,
        port=3306,
        charset="utf8",
        db=None
    ):
        self.say("Connecting to {}".format(host))
        self.database = pymysql.connect(
            host=host,
            port=port,
            user=user,
            passwd=password,
            db=db,
            charset=charset,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )

    @staticmethod
    def camel_to_underscore(name, separator="_"):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        underscore_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        underscore_name = underscore_name.replace("__", "_")
        return underscore_name

    def dict_factory(self, cursor, row):
        ''' http://stackoverflow.com/a/3300514 '''
        data = {}
        for index, column in enumerate(cursor.description):
            data[column[0]] = row[index]
        return data

    def execute(self, query):
        #if self.database is None:
        #    self.connect()
        cursor = self.database.cursor()
        self.say("Query: {}".format(query))

        if self.in_debug_mode is False:
            query_type = query.split(" ", 1)[0].lower()
            self.database.row_factory = self.dict_factory
            try:
                result = cursor.execute(query)
            except Exception as e:
                print(e)
                print("Ouery: '{}'".format(query))
                return None

            if query_type == "select" or query_type == "show":
                return cursor.fetchall()
            elif query_type == "update" or query_type == "delete":
                self.database.commit()
                return result
            elif query_type == "insert":
                self.database.commit()
                inserted_id = cursor.lastrowid
                return inserted_id
            else:
                self.database.commit()
                return None

    def drop_table(self, obj):
        table_name = DatabaseManager.camel_to_underscore(
            DatabaseManager.get_class_name(obj)
        )
        query = 'DROP TABLE IF EXISTS `{}`'.format(table_name)
        result = self.execute(query)
        return result

    def create_table(self, obj, data_types):
        table_name = DatabaseManager.camel_to_underscore(
            DatabaseManager.get_class_name(obj)
        )
        types = []
        for column, data_type in data_types.items():
            types.append("`{}` {}".format(column, data_type))
        query = "CREATE TABLE IF NOT EXISTS `{}` ({})".format(
            table_name,
            ",".join(types)
        )
        result = self.execute(query)
        return result

    def fetch_all(self, obj, columns="*"):
        table_name = DatabaseManager.camel_to_underscore(
            DatabaseManager.get_class_name(obj)
        )
        query = "SELECT {columns} FROM `{table}`".format(
            columns=columns,
            table=table_name
        )
        result = self.execute(query)
        results = []
        cursor = self.database.cursor()
        if len(result) > 0:
            for row in result:
                o = copy.copy(obj)
                if isinstance(row, dict):
                    for column, value in row.items():
                        setattr(o, column, value)
                elif isinstance(row, tuple) or isinstance(row, list):
                    for idx, col in enumerate(cursor.description):
                        setattr(o, col[0], row[idx])

                results.append(o)

        return results

    def fetch(self, obj, id):
        table_name = DatabaseManager.camel_to_underscore(
            DatabaseManager.get_class_name(obj)
        )
        conditions = [{
            'column': 'id',
            'equivalence': '=',
            'value': id
        }]
        return self.fetch_by(table_name, conditions)

    def fetch_by(
        self,
        obj,
        conditions,
        columns="*",
        num_rows=None,
        start_row=None
    ):
        ''' condition is like ['column': id, 'equivalence': '=', 'value': '1']
        '''
        table_name = DatabaseManager.camel_to_underscore(
            DatabaseManager.get_class_name(obj)
        )
        columns_string = "*"
        if columns is not None:
            if isinstance(columns, list):
                ",".join([
                    "`" + column + "`"
                    for column in columns if not column == "*"
                ])
            else:
                if columns == "*":
                    columns_string = columns
                else:
                    columns_string = "`" + columns + "`"

        condition_strings = []
        for condition in conditions:
            if isinstance(condition['value'], type(None)):
                cleaned_value = 'NULL'
            elif isinstance(condition['value'], bool):
                cleaned_value = str(condition['value']).upper()
            elif isinstance(condition['value'], int) or \
                    isinstance(condition['value'], float):
                cleaned_value = str(condition['value'])
            elif isinstance(condition["value"], bytes):
                cleaned_value = "FROM_BASE64('{}')".format(
                    base64.encodebytes(condition["value"]).decode('utf-8')
                )
            else:
                try:
                    cleaned_value = self.database.escape(condition['value'])
                except Exception:
                    cleaned_value = condition['value'].replace("'", "\'")
                    cleaned_value = cleaned_value.replace('"', '\"')
                    cleaned_value = "'" + cleaned_value + "'"

            condition_string = "`{column}` {equivalence} {value}".format(
                column=condition['column'],
                equivalence=condition['equivalence'],
                value=cleaned_value
            )
            condition_strings.append(condition_string)
        conditions_string = " AND ".join(condition_strings)
        limit_string = ""
        if start_row is not None:
            if num_rows is not None:
                limit_string = " LIMIT {},{}".format(start_row, num_rows)
        else:
            if num_rows is not None:
                limit_string = " LIMIT {}".format(num_rows)

        query = "SELECT {columns} FROM `{table}` WHERE ({conditions}){limit}".format(
            columns=columns_string,
            table=table_name,
            conditions=conditions_string,
            limit=limit_string
        )
        result = self.execute(query)
        cursor = self.database.cursor()
        results = []
        if result is not None and len(result) > 0:
            for row in result:
                o = copy.copy(obj)
                if isinstance(row, dict):
                    for column, value in row.items():
                        setattr(o, column, value)
                elif isinstance(row, tuple) or isinstance(row, list):
                    for idx, col in enumerate(cursor.description):
                        setattr(o, col[0], row[idx])

                results.append(o)
        return results

    def delete(self, obj, conditions):
        table_name = DatabaseManager.camel_to_underscore(
            DatabaseManager.get_class_name(obj)
        )
        condition_strings = []
        for condition in conditions:
            if isinstance(condition['value'], type(None)):
                cleaned_value = 'NULL'
            elif isinstance(condition['value'], bool):
                cleaned_value = str(condition['value']).upper()
            elif isinstance(condition['value'], int) or \
                    isinstance(condition['value'], float):
                cleaned_value = str(condition['value'])
            elif isinstance(condition["value"], bytes):
                cleaned_value = "FROM_BASE64('{}')".format(
                    base64.encodebytes(condition["value"]).decode('utf-8')
                )
            else:
                try:
                    cleaned_value = self.database.escape(condition['value'])
                except Exception:
                    cleaned_value = condition['value'].replace("'", "\'")
                    cleaned_value = cleaned_value.replace('"', '\"')
                    cleaned_value = "'" + cleaned_value + "'"

            condition_string = "`{column}` {equivalence} {value}".format(
                column=condition['column'],
                equivalence=condition['equivalence'],
                value=cleaned_value
            )
            condition_strings.append(condition_string)
        conditions_string = " AND ".join(condition_strings)
        query = "DELETE FROM `{table}` WHERE ({conditions})".format(
            table=table_name,
            conditions=conditions_string)

        self.execute(query)

    def insert_if_not_exists(self, obj):
        data = dict(obj)
        to_insert = False
        if 'id' not in data:
            to_insert = True
        else:
            if data['id'] is None:
                to_insert = True

        if to_insert:
            if 'ctime' in data:
                del(data['ctime'])

            # check if the row exists in the database
            conditions = []
            for key, value in data.items():
                if value is not None:
                    # if isinstance(value, type(None)):
                    #   cleaned_value = 'NULL'
                    #   cleaned_equivalence = ' IS '
                    if isinstance(value, bool):
                        cleaned_value = int(value == 'true')
                        cleaned_equivalence = '='
                    elif isinstance(value, int) or isinstance(value, float):
                        cleaned_value = str(value)
                        cleaned_equivalence = '='
                    elif isinstance(value, bytes):
                        cleaned_value = "FROM_BASE64('{}')".format(
                            base64.encodebytes(value).decode('utf-8')
                        )
                    else:
                        cleaned_value = str(value).encode('utf-8')
                        cleaned_equivalence = '='

                    fetch_condition = {
                        'column': key,
                        'equivalence': cleaned_equivalence,
                        'value': cleaned_value
                    }
                    conditions.append(fetch_condition)

            result = self.fetch_by(obj, conditions, 'id', num_rows=1)
            if result is not None:
                id = None
                if isinstance(result, dict):
                    id = result['id']
                else:
                    id = result.id
                return id
            else:
                return self.insert(obj)

    def save(self, obj):
        data = dict(obj)
        to_insert = False
        if 'id' not in data:
            to_insert = True
        else:
            if data['id'] is None:
                to_insert = True

        if to_insert is False:
            if data['id'] is not None:
                return self.update(obj)
        else:
            if 'ctime' in data:
                del(data['ctime'])

            # check if the row exists in the database
            conditions = []
            for key, value in data.items():
                if value is not None:
                    # if isinstance(value, type(None)):
                    #   cleaned_value = 'NULL'
                    #   cleaned_equivalence = ' IS '
                    if isinstance(value, bool):
                        cleaned_value = int(value == 'true')
                        cleaned_equivalence = '='
                    elif isinstance(value, int) or isinstance(value, float):
                        cleaned_value = str(value)
                        cleaned_equivalence = '='
                    elif isinstance(value, bytes):
                        cleaned_value = "FROM_BASE64('{}')".format(
                            base64.encodebytes(value).decode('utf-8')
                        )
                    else:
                        cleaned_value = str(value).encode('utf-8')
                        cleaned_equivalence = '='

                    fetch_condition = {
                        'column': key,
                        'equivalence': cleaned_equivalence,
                        'value': cleaned_value
                    }
                    conditions.append(fetch_condition)

            result = self.fetch_by(obj, conditions, 'id', num_rows=1)
            if result is not None:
                if isinstance(result, dict):
                    obj.id = result['id']
                else:
                    obj.id = result.id
                self.update(obj)
                return obj.id
            else:
                return self.insert(obj)

    def update(self, obj):
        ''' condition is like ['column': id, 'equivalence': '=', 'value': '1']
        '''
        table_name = DatabaseManager.camel_to_underscore(
            DatabaseManager.get_class_name(obj)
        )
        data = dict(obj)
        condition = {
            'column': 'id',
            'equivalence': '=',
            'value': str(data['id'])
        }
        del(data['id'])
        sets = []
        for column, value in data.items():
            if isinstance(value, type(None)):
                cleaned_value = 'NULL'
            elif isinstance(value, bool):
                cleaned_value = str(value).upper()
            elif isinstance(value, int) or isinstance(value, float):
                cleaned_value = str(value)
            elif isinstance(value, bytes):
                cleaned_value = "FROM_BASE64('{}')".format(
                    base64.encodebytes(value).decode('utf-8')
                )
            else:
                try:
                    cleaned_value = self.database.escape(value.encode("utf8"))
                except Exception:
                    cleaned_value = str(value).replace("'", "\'")
                    cleaned_value = cleaned_value.replace('"', '\"')
                    cleaned_value = "'" + cleaned_value + "'"

            sets.append("`{column}`={value}".format(
                column=column,
                value=cleaned_value
            ))

        set_string = ", ".join(sets)
        try:
            cleaned_value = self.database.escape(condition['value'])
        except Exception:
            cleaned_value = condition['value'].replace("'", "\'")
            cleaned_value = cleaned_value.replace('"', '\"')
            cleaned_value = "'" + cleaned_value + "'"

        query = "UPDATE `{table}` SET {sets}  WHERE `{column}` {equivalence} {value}".format(
            table=table_name,
            sets=set_string,
            column=condition['column'],
            equivalence=condition['equivalence'],
            value=cleaned_value
        )
        self.execute(query)

    def insert(self, obj):
        table_name = DatabaseManager.camel_to_underscore(
            DatabaseManager.get_class_name(obj)
        )
        data = dict(obj)
        if 'id' in data:
            if data['id'] is not None:
                del(data['id'])

        columns = []
        cleaned_values = []
        for column, value in data.items():
            columns.append('`{column}`'.format(column=column))
            if isinstance(value, type(None)):
                cleaned_value = 'NULL'
            elif isinstance(value, bool):
                cleaned_value = str(value).upper()
            elif isinstance(value, int) or isinstance(value, float):
                cleaned_value = str(value)
            elif isinstance(value, bytes):
                cleaned_value = "FROM_BASE64('{}')".format(
                    base64.encodebytes(value).decode('utf-8')
                )
            else:
                try:
                    cleaned_value = self.database.escape(value)
                except Exception:
                    cleaned_value = value.replace("'", "\'")
                    cleaned_value = cleaned_value.replace('"', '\"')
                    cleaned_value = "'" + cleaned_value + "'"

            cleaned_values.append(cleaned_value)
        query = "INSERT INTO `{table}` ({columns}) VALUES ({values})".format(
            table=table_name,
            columns=",".join(columns),
            values=",".join(cleaned_values)
        )
        inserted_id = self.execute(query)
        return inserted_id

    def insert_many(self, objs):
        if len(objs) < 1:
            return

        table_name = DatabaseManager.camel_to_underscore(
            DatabaseManager.get_class_name(objs[0])
        )
        columns = []
        column_names = []
        data = dict(objs[0])
        if 'id' in data:
            if data['id'] is not None:
                del(data['id'])
        for column in data:
            columns.append('`{column}`'.format(column=column))
            column_names.append(column)

        sets = []
        for obj in objs:
            data = dict(obj)
            if 'id' in data:
                if data['id'] is not None:
                    del(data['id'])
            cleaned_values = []
            for column in column_names:
                if column not in data:
                    cleaned_value = "NULL"
                else:
                    value = data[column]
                    if isinstance(value, type(None)):
                        cleaned_value = 'NULL'
                    elif isinstance(value, bool):
                        cleaned_value = str(value).upper()
                    elif isinstance(value, int) or isinstance(value, float):
                        cleaned_value = str(value)
                    elif isinstance(value, bytes):
                        cleaned_value = "FROM_BASE64('{}')".format(
                            base64.encodebytes(value).decode('utf-8')
                        )
                    else:
                        try:
                            cleaned_value = self.database.escape(
                                value.encode('utf-8')
                            )
                        except Exception:
                            cleaned_value = value.encode('utf-8').replace(
                                "'",
                                "\'"
                            )
                            cleaned_value = cleaned_value.replace('"', '\"')
                            cleaned_value = "'" + cleaned_value + "'"

                cleaned_values.append(cleaned_value)
            sets.append(",".join(cleaned_values))

        cleaned_value_sets = "({sets})".format(sets="),(".join(sets))
        query = "INSERT INTO `{table}` ({columns}) VALUES {values}".format(
            table=table_name,
            columns=",".join(columns),
            values=cleaned_value_sets
        )
        self.execute(query)

    @staticmethod
    def get_class_name(obj):
        return obj.__class__.__name__

    def say(self, message):
        if self.in_verbose_mode is True:
            print("[{}] {}".format(self.__class__.__name__, message))
