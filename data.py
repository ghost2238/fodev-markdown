from mdx_gfm import GithubFlavoredMarkdownExtension
import config
import re
import markdown
import os
from data_io import Store, Github

class Data():
    @staticmethod
    def load():
        Store.init(config.base_path)

    @staticmethod
    def get_projects():
        projects =[]
        try:
            json = Store.read_json('content.json')
            for project_name in json:
                projects.append(Project(project_name, json[project_name]))
        except IOError as ex:
            print('Unable to open ' + Store.absolute_path('content.json'))
            print(ex)
        return projects

    @staticmethod
    def get_project(name):
        projects = Data.get_projects()
        for project in projects:
            if project.name == name:
                return project
        return None

class Document():
    def __init__(self, title, route, url):
        self.content = None
        self.title = title
        self.route = route
        self.url = url
        self.parse_url(self.url)

    def parse_url(self, url):
        self.protocol = 'file'
        if url.find('://') != -1:
            spl = url.split('://')
            if spl[0] == 'github':
                self.protocol = 'github'
                last_slash = spl[1].rfind('/')
                self.repo = spl[1][:last_slash] 
                self.file = spl[1][last_slash:]
        if self.protocol == 'file':
            self.file = url

    def load_content(self):
        if self.protocol == 'file':
            self.content = Store.read_markdown(self.file)
        if self.protocol == 'github':
            self.content = Github.get_raw(self.repo, self.file)


    def postprocess(self, html):
        return html.replace(':heavy_check_mark:', u"\u2714")

    def to_html(self):
        if self.content is None:
            self.load_content()
        html = markdown.markdown(self.content, extensions=[GithubFlavoredMarkdownExtension()])
        return self.postprocess(html)

class Page():
    def __init__(self, route, json):
        self.route = route
        self.name = json['name']
        self.documents = []
        if 'docs' in json:
            docs = json['docs']
            for x in range(0,len(docs)):
                j = docs[x]
                self.documents.append(Document(j['title'], j['route'], j['url']))
    
    def get_document(self, route_name):
        if route_name is '':
                return self.documents[0]
        for doc in self.documents:
            if doc.route == route_name:
                print('returning ' + doc.route)
                print(doc.content)
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

    def __init__(self, name, json):
        self.name = name
        self.assert_key('display_name', json)
        self.assert_key('route_name', json)
        self.display_name = json['display_name']
        self.route_name = json['route_name']
        self.pages = []
        for page in json['pages']:
            self.pages.append(Page(page, json['pages'][page]))
        if json['use_automapping']:
            self.automap()

    def assert_key(self, key, json):
        assert (key in json, key + ' is required for project ' + self.name)

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
            for page in self.pages:
                if page.route == page_route:
                    return page

    # Build content from automapped directory
    def automap(self):
        path = config.base_path+'/markdown/'+self.route_name+'/'
        if not os.path.exists(path):
            return
        dir_contents = os.listdir(path)
        for dir in dir_contents:
            if not os.path.isdir(path+'/'+dir):
                continue

            # Get all documents in the folder
            docs = []
            document_files = os.listdir(path+'/'+dir)
            print(path+'/'+dir)
            for document_file in document_files:
                md_path = self.route_name+'/'+dir+'/'+document_file
                #print('markdown: ' + md_path)
                content = Store.read_markdown(md_path)
                (_, filename) = os.path.split(document_file)

                # Parse the markdown document and look for the first heading ('#')
                # This will be used as the title of the document.
                # If we don't find any top-level heading, the filename will be the title.
                title = filename
                for line in content.splitlines():
                    if line.startswith('#'):
                        title = str.strip(line[1:])
                        break
                
                doc = Document(title, filename, document_file)
                doc.content = content
                docs.append(doc)

            # See if we can find a matching page
            # to add the documents to
            matched_page = None
            for page in self.pages:
                if page.route == dir:
                    matched_page = page
            #if matched_page is None:
            #    self.pages.append(Page() )
            #else:
            # TODO: Handle if there is no match.
            matched_page.documents = docs