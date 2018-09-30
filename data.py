from mdx_gfm import GithubFlavoredMarkdownExtension
import config
import re
import markdown
import os
import logging
from data_io import Store, Github

logging.basicConfig(filename='program.log',level=logging.DEBUG)

def doc_parse_title(content):
    if content is None:
        return None
    for line in content.splitlines():
        if not line.startswith('#'):
            continue
        # It's a h2, ##
        if line[1] == '#':
            continue

        # Let's assume rest of the line is just the title... TODO: strip formatting
        return str.strip(line[1:])
    return None

def linkify_text(text):
    text = text.replace(' ','-').replace('(','').replace(')','')
    text = text.lower()
    return text

class Data():
    @staticmethod
    def load():
        Store.init(config.content_path)

    @staticmethod
    def get_projects():
        projects =[]
        try:
            json = Store.read_json('content.json')
            for project_name in json:
                projects.append(Project(project_name, json[project_name]))
        except IOError as ex:
            logging.error('Unable to open ' + Store.absolute_path('content.json'))
            logging.error(ex)
        return projects

    @staticmethod
    def get_project(route):
        projects = Data.get_projects()
        for project in projects:
            if project.route_name == route:
                return project
        return None

class Subtitle():
    def __init__(self, title, tag):
        self.title = title
        self.tag = tag
    # TODO: Strip lots of more characters...
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
        #if url.find('://') != -1:
            #spl = url.split('://')
            #if spl[0] == 'github':
            #    self.protocol = 'github'
            #    last_slash = spl[1].rfind('/')
            #    self.repo = spl[1][:last_slash] 
            #    self.file = spl[1][last_slash:]
        if self.protocol == 'file':
            self.file = url

    def parse_subtitles(self):
        if self.content is None:
            return

        for line in self.content.splitlines():
            try:
                idx = line.index('##')
            except:
                continue
            
            offset = 2
            tag = 'h2'
            if line[idx+2] == '#':
                offset = 3
                tag = 'h3'
            if line[idx+3] == '#':
                offset = 4
                tag = 'h4'

            # Let's assume rest of the line is just the title... TODO: strip formatting
            self.subtitles.append(Subtitle(str.strip(line[idx+offset:]), tag))

    def path_to_file(self):
        return self.project_dir + '/' + self.page_dir + '/' + self.file

    def has_subtitles(self):
        return len(self.subtitles) > 0

    def load_content(self):
        if self.protocol == 'file':
            self.content = Store.read_markdown(self.path_to_file())
        #if self.protocol == 'github':
        #    self.content = Github.get_raw(self.repo, self.file)

    # For links
    def header_make_id(self, tag, html):
        for match in re.findall("\<"+tag+"\>(.+?)\<\/"+tag+"\>", html):
            id = linkify_text(match)
            html = html.replace('<'+tag+'>'+ match + '</'+tag+'>', '<'+tag+' id="'+id+'">'+match+'</'+tag+'>')
        return html

    def postprocess(self, html):

        # Yay... 
        # TODO: use a proper HTML parser to strip tags of all formatting.
        #print(html)
        #match = 'asd'
        #while match != None:
        html = self.header_make_id('h2', html)
        html = self.header_make_id('h3', html)
        html = self.header_make_id('h4', html)
        return html.replace(':heavy_check_mark:', u"\u2714")
    

    def to_html(self):
        if self.content is None:
            self.load_content()
        if self.content is None:
            logging.error('Unable to retrieve any markdown content for ' + self.path_to_file())
            return ''

        html = markdown.markdown(self.content, extensions=[GithubFlavoredMarkdownExtension()])
        return self.postprocess(html)

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

    def __init__(self, name, json):
        self.name = name
        self.assert_key('display_name', json)
        self.assert_key('route_name', json)
        self.display_name = json['display_name']
        self.route_name = json['route_name']
        self.pages = []
        for page in json['pages']:
            self.pages.append(Page.from_json(page, self.route_name, json['pages'][page]))
        if 'automap_all_to' in json:
            self.automap_all_to = json['automap_all_to']

        if ('use_automapping' in json) and json['use_automapping']:
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
        path = Store.file_path(self.route_name+'/')
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