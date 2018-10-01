from html.parser import HTMLParser
from src.html_common import is_heading_tag

# DON'T USE THIS, it's just experiment with building tree via stack instead of the usual recursive style.
# Some better alternatives: https://github.com/vinta/awesome-python#html-manipulation
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

# Stackbased conversion to nodetree with help of python's built-in HTMLParser
class ParseToTree(HTMLParser):
    stack = None
    # frame
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