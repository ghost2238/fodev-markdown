from mdx_gfm import GithubFlavoredMarkdownExtension
import config
import re
import markdown
import os
from data_io import Store, Github

def doc_parse_title(content):
    for line in content.splitlines():
        if not line.startswith('#'):
            continue
        # It's a h2, ##
        if line[1] == '#':
            continue

        # Let's assume rest of the line is just the title... TODO: strip formatting
        return str.strip(line[1:])
    return None

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
    def get_project(route):
        projects = Data.get_projects()
        for project in projects:
            if project.route_name == route:
                return project
        return None

class Subtitle():
    def __init__(self, title):
        self.title = title
    # TODO: Strip lots of more characters...
    def url(self):
        return '#'+self.title.replace(' ', '')

class Document():
    def __init__(self, title, route, project_dir, page_dir, url):
        self.content = None
        self.title = title
        self.page_dir = page_dir
        self.project_dir = project_dir
        self.route = route
        self.url = url
        self.parse_url(self.url)
        self.load_content()
        self.subtitles = []
        self.parse_subtitles()

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

    @staticmethod
    def subtitle_url(subtitle):
        return subtitle.replace(' ', '')

    def parse_subtitles(self):
        if self.content is None:
            return

        for line in self.content.splitlines():
            try:
                idx = line.index('##')
            except:
                continue
            # It's a h3, that's also ok, for now.
            offset = 2
            if line[idx+2] == '#':
                offset = 3

            # Let's assume rest of the line is just the title... TODO: strip formatting
            self.subtitles.append(Subtitle(str.strip(line[idx+offset:])))
        #print(self.subtitles)

    def path_to_file(self):
        return self.project_dir + '/' + self.page_dir + '/' + self.file

    def load_content(self):
        if self.protocol == 'file':
            self.content = Store.read_markdown(self.path_to_file())
        #if self.protocol == 'github':
        #    self.content = Github.get_raw(self.repo, self.file)

    def postprocess(self, html):

        # Yay... 
        # TODO: use a proper HTML parser to strip tags of all formatting.
        print(html)
        #match = 'asd'
        #while match != None:
        for match in re.findall("\<h2\>(.+?)\<\/h2\>", html):
            id = match.replace(' ', '')
            html = html.replace('<h2>'+ match + '</h2>', '<h2 id="'+id+'">'+match+'</h2>')
        for match in re.findall("\<h3\>(.+?)\<\/h3\>", html):
            id = match.replace(' ', '')
            html = html.replace('<h3>'+ match + '</h3>', '<h3 id="'+id+'">'+match+'</h3>')
        #html = re.sub(r"<h2></h2>", "" re.)

        return html.replace(':heavy_check_mark:', u"\u2714")
    

    def to_html(self):
        if self.content is None:
            self.load_content()
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
                print('returning ' + doc.route)
                #print(doc.content)
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
            for page in self.pages:
                if page.route == page_route:
                    return page

    def read_documents_from_folder(self, path, dir):
        docs = []
        document_files = os.listdir(path+'/'+dir)
        for document_file in document_files:
            md_path = self.route_name+'/'+dir+'/'+document_file
            content = Store.read_markdown(md_path)
            (_, filename) = os.path.split(document_file)

            # Parse the markdown document and look for the first heading ('#')
            # This will be used as the title of the document.
            # If we don't find any top-level heading, the filename will be the title.
            title = filename
            parsed_title = doc_parse_title(content)
            if parsed_title != None:
                title = parsed_title
            
            doc = Document(title, filename, self.route_name, dir, document_file)
            doc.content = content
            docs.append(doc)
        return docs

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
            docs = self.read_documents_from_folder(path, dir)
            # print(docs)            

            matched_page = None
            # All documents found goes to this page.
            if self.automap_all_to != '':
                for page in self.pages:
                    if page.route == dir:
                        matched_page = page
            else:
                # See if we can find a matching page with the same route as dirname
                # to add the documents to
                # TODO: pages with same name in different parts of directory tree.
                for page in self.pages:
                    if page.route == dir:
                        matched_page = page
                #if self.
                # Create new page with name of dir. 
                if matched_page is None:
                    matched_page = Page(dir, dir)
                    self.pages.append(matched_page)

            print(matched_page)
            for d in docs:
                matched_page.documents.append(d)