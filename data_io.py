
import io
import os.path
import json
import requests
# Read from disk or db depending on cache state.
class Store():

    @staticmethod 
    def init(content_path):
        Store.content_path = content_path

    # TODO: Cache to db and fetch from there if file hasn't been modified.
    @staticmethod
    def read(filename):
        path = Store.file_path(filename)
        try:
            with open(path, 'r', ) as fp:
                return ''.join(fp.readlines())
        except IOError as ex:
            print("Unable to open file " + path)
            print(ex)

    @staticmethod
    def read_markdown(filename):
        return Store.read(filename)

    @staticmethod
    def read_json(file):
        print('Loading ' + Store.file_path(file))
        loaded = Store.read(file)
        return json.loads(loaded)

    # Get content path and add trailing slash if needed
    @staticmethod
    def file_path(filename):
        if Store.content_path.endswith('/'):
            return Store.content_path+filename
        return Store.content_path+'/'+filename

    @staticmethod
    def absolute_path(filename):
        return os.path.abspath(Store.content_path+'/'+filename)

class Github():
    @staticmethod
    def get_raw(repo, file):
        request_url = 'https://raw.githubusercontent.com/'+repo+'/master/'+file
        r = requests.get(request_url)
        return r.text