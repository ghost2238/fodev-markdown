import json
import logging
import os
import os.path
import glob
import pickle
import re
import config

from src.html_utils import (html_extract_text_element, html_parse_header,
                            linkify_text, markdown_to_html)

logging.basicConfig(filename=config.base_path+'program.log',level=logging.DEBUG)

# TODO: Use block extension instead?
def doc_parse_title(content):
    if content is None:
        return None
    for line in content.splitlines():
        if not line.startswith('#'):
            continue
        # It's a h2, ##
        if line[1] == '#':
            continue

        # Let's assume rest of the line is just the title...
        return html_extract_text_element(markdown_to_html(line))

    return None


def file_path(filename):
    if config.content_path.endswith('/'):
        return config.content_path+filename
    return config.content_path+'/'+filename

def read_file_safe(filename):
    path = file_path(filename)
    try:
        with open(path, 'r', ) as fp:
            return ''.join(fp.readlines())
    except IOError as ex:
        print("Unable to open file " + path)
        print(ex)


class Data():

    # Parsed content.json
    parsed_content = None
    cache_index = None

    @staticmethod
    def get_content():
        if Data.parsed_content is None:
            print('Loading ' + file_path('content.json'))
            content = read_file_safe('content.json')
            content = json.loads(content)
            Data.parsed_content = content
        return Data.parsed_content

    @staticmethod
    def get_cache_index():
        if Data.cache_index is None:
            Data.cache_index = Data.unpickle_cache('cache.idx')
        if Data.cache_index is None:
            Data.cache_index = dict()
        #print(Data.cache_index)
        return Data.cache_index

    @staticmethod
    def get_projects():
        projects =[]
        content = Data.get_content()
        try:
            for project_name in content:
                route = content[project_name]['route_name']
                projects.append(Data.get_project(route))
        except IOError as ex:
            logging.error('Unable to get projects.')
            logging.error(ex)
        return projects

    @staticmethod
    def unpickle_cache(file):
        path = config.base_path+'/cache/'+file
        try:
            file = open(path,'rb')
            loaded = pickle.load(file)
            return loaded
        except IOError:
            logging.error('Unable to unpickle cached file ' + path)
        return None
    
    @staticmethod
    def pickle_cache(file, obj):
        path = config.base_path+'/cache/'+file
        try:
            file = open(path,'wb')
            pickle.dump(obj, file)
        except IOError:
            logging.error('Unable to save cache file ' + path)
        return None

    @staticmethod
    def mtime_total(path):
        if len(config.base_path) < 6:
            raise ValueError('base_path looks invalid.')
        
        mtime_total = 0
        #print('globbing: ' + path+'/**/*')
        for obj in glob.iglob(path+'/**/*.md', recursive=True):
            #print('f')
            #print(obj)
            mtime = os.path.getmtime(obj)
            #print('mtime of ' + obj + ' is ' + str(mtime))
            mtime_total+=mtime
        return mtime_total

    # Load from cache if it's there, otherwise just read as normal.
    @staticmethod
    def get_project(name):
        print('loading ' + name)
        name = name.replace('..', '')
        # Load cache index
        cache_index = Data.get_cache_index()
        stale_cache = False
        has_cache = False
        v2 = Data.mtime_total(config.content_path+'/'+name)
        
        if name in cache_index:
            has_cache = True
            v1 = cache_index[name]
            if v1 != v2:
                stale_cache = True
                # print('cache is stale')

        project = None
        if has_cache and not stale_cache:
            project = Data.unpickle_cache(name)
            #if project != None:
                # print(name + ' loaded from cache')
        if project != None:
            return project
        
        # Parse project from file
        content = Data.get_content()
        for found_name in content:
            route_name = content[found_name]['route_name']
            if route_name == name:
                project = Project(name, content[found_name])
        if project is None:
            return None

        # load all stuff so we can cache it.
        for p in project.pages:
            for d in p.documents:
                d.to_html()
        # print(name + ' loaded from disk')

        # Save to cache
        # print('saving cache to disk')
        Data.cache_index[name] = v2
        Data.pickle_cache(name, project)
        Data.pickle_cache('cache.idx', Data.cache_index)
        return project

class Subtitle():
    def __init__(self, title, tag):
        self.title = title
        self.tag = tag
    
    def url(self):
        return '#'+linkify_text(self.title)

    def css_class(self):
        c = ['subtitle']
        if self.tag == 'h3':
            c.append('sub-h3')
        if self.tag == 'h4':
            c.append('sub-h4')
        return ' '.join(c)

class Document():
    def __init__(self, title, route, project_dir, page_dir, url):
        self.content = None
        self.output_html = None
        self.title = title
        self.page_dir = page_dir
        self.project_dir = project_dir
        self.route = route # also filename
        self.url = url
        self.parse_url(self.url)
        self.load_content()
        self.subtitles = []
        self.parse_subtitles()
        self.parse_title()

    # Parse the markdown document and look for the first heading ('#')
    # This will be used as the title of the document.
    # If we don't find any top-level heading, the filename will be the title.
    def parse_title(self):
        parsed_title = doc_parse_title(self.content)
        if parsed_title != None:
            self.title = parsed_title

    def parse_url(self, url):
        self.protocol = 'file'
        if self.protocol == 'file':
            self.file = url

    def parse_subtitles(self):
        if self.content is None:
            return

        for line in self.content.splitlines():
            try:
                _ = line.index('##')
            except:
                continue
            
            result = html_parse_header(markdown_to_html(line))

            # Let's assume rest of the line is just the title... TODO: strip formatting
            self.subtitles.append(Subtitle(result['text'], result['tag']))

    def path_to_file(self):
        return self.project_dir + '/' + self.page_dir + '/' + self.file

    def has_subtitles(self):
        return len(self.subtitles) > 0

    def load_content(self):
        if self.protocol == 'file':
            self.content = read_file_safe(self.path_to_file())
        #if self.protocol == 'github':
        #    self.content = Github.get_raw(self.repo, self.file)

    def postprocess(self, html):
        # TODO: Create an extension to replace github emotes to unicode symbols.
        return html.replace(':heavy_check_mark:', u"\u2714")
    
    def to_html(self):
        if self.output_html != None:
            print('output already generated')
            return self.output_html

        if self.content is None:
            self.load_content()
        if self.content is None:
            logging.error('Unable to retrieve any markdown content for ' + self.path_to_file())
            return ''
        #print(self.content)

        html = markdown_to_html(self.content)
        #print(html)
        html = self.postprocess(html)
        self.output_html = html
        # print(processed)
        return html

class Page():
    def __init__(self, name, route):
        self.name = name
        self.route = route
        self.documents = []
    
    @staticmethod
    def from_json(route, project_route, json):
        page = Page(json['name'], route)
        page.documents = []
        if 'docs' in json:
            docs = json['docs']
            for x in range(0,len(docs)):
                j = docs[x]
                page.documents.append(Document(j['title'], j['route'], project_route, route, j['url']))
        return page

    def get_document(self, route_name):
        if route_name is '':
                return self.documents[0]
        for doc in self.documents:
            if doc.route == route_name:
                logging.debug('Matched document for ' + doc.route)
                return doc

    def get_documents(self):
        return self.documents

    def has_documents(self):
        return len(self.documents)>0


# Represents a project from content.json
class Project():
    display_name = ''
    route_name = ''
    use_automapping = False
    automap_all_to = ''
    github_repo = ''

    def __init__(self, name, json):
        self.name = name
        #self.assert_key('display_name', json)
        #self.assert_key('route_name', json)
        self.display_name = json['display_name']
        self.route_name = json['route_name']
        self.pages = []
        for page in json['pages']:
            self.pages.append(Page.from_json(page, self.route_name, json['pages'][page]))
        if 'automap_all_to' in json:
            self.automap_all_to = json['automap_all_to']
        if 'github_repo' in json:
            self.github_repo = json['github_repo']
        if ('use_automapping' in json) and json['use_automapping']:
            self.automap()
        

    #def assert_key(self, key, json):
    #    assert (key in json, key + ' is required for project ' + self.name)

    def has_tools(self):
        return self.github_repo != ''

    def has_pages(self):
        return len(self.pages) > 0

    def get_pages(self):
        return self.pages

    def get_page_with_docs(self):
        for p in self.pages:
            if p.has_documents():
                return p
        return None

    def get_page(self, page_route):
        if page_route is '':
            return self.pages[0]
        else:
            return self.get_page_by_route(page_route)

    def get_page_by_route(self, page_route):
        for page in self.pages:
            if page.route == page_route:
                return page

    def read_documents_from_folder(self, path, dir):
        docs = []
        document_files = os.listdir(path+'/'+dir)
        for document_file in document_files:
            (_, filename) = os.path.split(document_file)
            doc = Document(filename, filename, self.route_name, dir, document_file)
            docs.append(doc)
        return docs

    # Build content from automapped directory
    def automap(self):
        path = file_path(self.route_name+'/')
        if not os.path.exists(path):
            logging.error(path + ' don\'t exist, unable to automap.')
            return
        dir_contents = os.listdir(path)
        for obj in dir_contents:
            if not os.path.isdir(path+'/'+obj):
                # If we automap to a page, root objects can go there.
                if self.automap_all_to != '':
                    mapped_page = self.get_page_by_route(self.automap_all_to)
                    doc = Document(obj, obj, self.route_name, '', obj)
                    mapped_page.documents.append(doc)
                continue

            # Get all documents in the folder
            docs = self.read_documents_from_folder(path, obj)
            # print(docs)            

            matched_page = None
            # All documents found goes to this page.
            if self.automap_all_to != '':
                for page in self.pages:
                    if page.route == obj:
                        matched_page = page
            else:
                # See if we can find a matching page with the same route as dirname
                # to add the documents to
                # TODO: pages with same name in different parts of directory tree.
                for page in self.pages:
                    if page.route == obj:
                        matched_page = page

                # Create new page with name of dir. 
                if matched_page is None:
                    matched_page = Page(obj, obj)
                    self.pages.append(matched_page)

            for d in docs:
                matched_page.documents.append(d)
