from mdx_gfm import GithubFlavoredMarkdownExtension
import config
import re
import markdown
import os
import logging
from data_io import Store, Github
from html.parser import HTMLParser

logging.basicConfig(filename=config.base_path+'program.log',level=logging.DEBUG)

def is_heading_tag(tag):
    return tag == 'h1' or tag == 'h2' or tag == 'h3' or tag == 'h4' or tag == 'h5' or tag == 'h6'

# TODO: Move HTML and markdown stuff...
# TODO: Remove text as a constructor parameter
class HTMLNode:
    def __init__(self, tag, attrs, text):
        self.tag = tag
        self.attrs = attrs # list (attr, value)
        self.text = text
        self.children = []

    def add_child(self, node):
        node.parent = self
        self.children.append(node)

    def get_text(self):
        text = ''
        for ch in self.children:
            if ch.tag == '' and ch.text != '':
                text += ch.text
            else:
                text += ch.get_text()
        return text

    # Take a HTML node and call function for each node recursively.
    def walk(self, func):
        func(self)

class Vars():
    def __init__(self):
        self.tag = ''
        self.attrs = list()
        self.text = ''
        self.nodes = []

# Stackbased conversion to nodetree with help of python's built-in html parser
class ParseToTree(HTMLParser):
    stack = None
    # stack frame
    vars = None

    def __init__(self):
        HTMLParser.__init__(self)
        self.vars = Vars()
        #self.vars.tag = 'body'
        self.stack = []

    def print_stack(self, msg):
        print('>'*len(self.stack) +' '+msg)

    def stack_push(self):
        # self.print_stack('pushing stack')
        self.stack.append(self.vars)
        self.vars = Vars()

    def stack_pop(self):
        # self.print_stack('popping stack')
        #self.stack_idx-=1
        self.vars = self.stack.pop()

    def handle_starttag(self, tag, attrs):
        # self.print_stack('found <' + tag +'>')
        print('"<'+tag+'>"')
        if tag == 'br':
            print('return')
            return
        self.stack_push()
        self.vars.nodes = []
        self.vars.tag = tag
        self.vars.attrs = attrs

    def handle_data(self, data):
        # Text element
        self.vars.nodes.append(HTMLNode('',(),data))

    # TODO: Fix br handling
    def handle_endtag(self, tag):
        print('"</'+tag+'>"')
        if tag == 'br':
            self.vars.nodes.append(HTMLNode('br',(),''))
            return
            #self.vars.nodes.append(HTMLNode('br',(),''))
        #    return
        # self.print_stack('found </' + tag + '>')
        node = HTMLNode(self.vars.tag, self.vars.attrs, '')
        for child in self.vars.nodes:
            # self.print_stack('adding ' + child.tag)
            node.add_child(child)
        self.stack_pop()
        self.vars.nodes.append(node)

    def get_result(self):
        node = HTMLNode(self.vars.tag, self.vars.attrs, '')
        for child in self.vars.nodes:
            node.children.append(child)
        return node

# Walks a tree and writes html to a buffer. 
class HTMLWriter():
    def __init__(self):
        self.buffer = ''
        self.depth = 0

    def walk(self, node):
        #print(len(node.children))
        #self.depth+=1
        if node.tag == '' and node.text != '':
            self.buffer += node.text
            return
        attr_strs = []
        if node.tag != '':
            self.buffer += '<'+node.tag
            if len(node.attrs) > 0:
                self.buffer += ' '
            for a in node.attrs:
                attr_strs.append(a[0]+'="'+a[1]+'"')
            self.buffer += ' '.join(attr_strs)
            self.buffer +='>'
            if node.tag == 'ul':
                self.buffer += '\n'
        for c in node.children:
            self.walk(c)
        self.buffer +='</'+node.tag+'>'
        if node.tag == 'code' or node.tag == 'em':
            self.buffer += ''
        elif node.tag == 'pre':
            self.buffer += '\n\n'
        else:
            self.buffer += '\n'

            
        #if self.depth>3:
        #    self.buffer +='\n'
        #self.depth-=1

def add_id_to_headings(node):
    if is_heading_tag(node.tag) and node.tag != 'h1':
        id = linkify_text(node.get_text())
        node.attrs.append(('id', id))
    for n in node.children:
        add_id_to_headings(n)


def html_tree_to_string(node):
    writer = HTMLWriter()
    writer.walk(node)
    return writer.buffer

def html_to_tree(html):
    parser = ParseToTree()
    print(html)
    parser.feed(html)
    return parser.get_result()

# Parse text and tag info from some html, used to extract titles and subtitles
class HeadingsParser(HTMLParser):
    def __init__(self):
        self.inside_heading = False
        self.inside_tag = ''
        self.text = ''
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if is_heading_tag(tag):
            self.inside_heading = True
            self.inside_tag = tag

    def handle_endtag(self, tag):
        if is_heading_tag(tag):
            self.inside_heading = False

    def handle_data(self, data):
        if self.inside_heading:
            self.text += data


def markdown_to_html(content):
    return markdown.markdown(content, extensions=[GithubFlavoredMarkdownExtension()])

def html_parse_header(html):
    parser = HeadingsParser()
    parser.feed(html)
    result = {'tag': parser.inside_tag, 'text': parser.text }
    return result

def html_extract_text_element(html):
    parser = HeadingsParser()
    parser.feed(html)
    print('extracted: ' + parser.text)
    return parser.text

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
        return html_extract_text_element(markdown_to_html(line))

    return None

# TODO: Strip lots of more characters...
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
            self.content = Store.read_markdown(self.path_to_file())
        #if self.protocol == 'github':
        #    self.content = Github.get_raw(self.repo, self.file)

    def postprocess(self, html):
        node = html_to_tree(html)
        node.walk(add_id_to_headings)
        html = html_tree_to_string(node)
        return html.replace(':heavy_check_mark:', u"\u2714")
    

    def to_html(self):
        if self.content is None:
            self.load_content()
        if self.content is None:
            logging.error('Unable to retrieve any markdown content for ' + self.path_to_file())
            return ''
        #print(self.content)

        html = markdown_to_html(self.content)
        #print(html)
        processed = self.postprocess(html)
        print(processed)
        return processed

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