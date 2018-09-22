
import io
import os.path
import json
import requests
# Read from disk or db depending on cache state.
class Store():

    @staticmethod 
    def init(base_path,):
        Store.base_path = base_path

    # TODO: Cache to db and fetch from there if file hasn't been modified.
    @staticmethod
    def read(filename):
        path = Store.base_path+'/'+filename
        with open(path, 'r', ) as fp:
            return ''.join(fp.readlines())

    @staticmethod
    def read_markdown(filename):
        return Store.read('/markdown/'+filename)

    @staticmethod
    def read_json(file):
        return json.loads(Store.read(file))

    @staticmethod
    def absolute_path(filename):
        return os.path.abspath(Store.base_path+'/'+filename)

class Github():
    @staticmethod
    def get_raw(repo, file):
        request_url = 'https://raw.githubusercontent.com/'+repo+'/master/'+file
        r = requests.get(request_url)
        return r.text