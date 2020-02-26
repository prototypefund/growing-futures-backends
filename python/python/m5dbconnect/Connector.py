from pymongo import MongoClient
from urllib.parse import quote_plus
from bson.json_util import dumps


class Connector:
    def __init__(self, collection, user, password, host, db):
        self.collection_name = collection
        self.user = user
        self.password = password
        self.host = host
        self.db = db

    def find_one(self, find_json):
        found = self.collection().find_one(find_json)
        if (found):
            return self.remove_id_key(found)
        else:
            return None

    def delete(self, data, uid_key):
        query_string = {uid_key: data[uid_key]}
        return self.collection().delete_one(query_string)

    def save(self, json_data):
        return self.collection().insert_one(json_data).inserted_id

    def get_client(self):
        client = self.open_connection()
        db = client[self.db]
        return db

    def collection(self):
        return self.get_client()[self.get_key()]

    def get_key(self):
        return self.collection_name

    def save_or_update(self, uid_key, json_data):
        query_string = {uid_key: json_data[uid_key]}
        doc = self.create_update_data(json_data)
        new_doc = self.collection().update_one(query_string, doc, upsert=True)
        return (new_doc.matched_count, new_doc.modified_count)

    def create_update_data(self, json_data):
        return {"$set": json_data}

    def data_as_json(self):
        ret_arr = self.data_as_list()
        ret_val = {}
        ret_val[self.get_key()] = ret_arr

        return dumps(ret_val)

    def data_as_list(self):
        ret_arr = []
        for data_point in self.collection().find():
            without_id = self.remove_id_key(data_point)
            ret_arr.append(without_id)
        return ret_arr

    def remove_id_key(self, d):
        return {k: v for k, v in d.items() if k != '_id'}

    def data_as_json_list(self):
        return dumps(self.data_as_list())

    def add_to_all(self, data_dict):
        pass

    def open_connection(self):
        return MongoClient(self.get_old_style_uri())

    def get_new_style_uri(self):
        return "mongodb+srv://%s:%s@%s/test?retryWrites=true" % (quote_plus(self.user), quote_plus(self.password), self.host)

    def get_old_style_uri(self):
        return "mongodb://%s:%s@%s:27017,cluster0-shard-00-01-jbf8e.gcp.mongodb.net:27017,cluster0-shard-00-02-jbf8e.gcp.mongodb.net:27017/test?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true" % (quote_plus(self.user), quote_plus(self.password), self.host)
