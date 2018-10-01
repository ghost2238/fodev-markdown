from src.html_parser import HTMLWriter, ParseToTree, HeadingsParser
from src.html_common import is_heading_tag
from mdx_gfm import GithubFlavoredMarkdownExtension
from markdown.extensions.headerid import HeaderIdExtension
import markdown

# TODO: Strip lots of more characters...
def linkify_text(text):
    text = text.replace(' ','-').replace('(','').replace(')','')
    text = text.lower()
    return text

def html_tree_to_string(node):
    writer = HTMLWriter()
    writer.walk(node)
    return writer.buffer

def html_to_tree(html):
    parser = ParseToTree()
    parser.feed(html)
    return parser.get_result()

class IdHeadingsExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md, md_globals):
        md.treeprocessors.add('idheadings', AddIdToHeadings, '_end')

# Actually not used at the moment, because of HeaderIdExtension
class AddIdToHeadings(markdown.treeprocessors.Treeprocessor):
    def get_text(self, node):
        text = node.text
        if text == None:
            text = ''
        for ch in node.getchildren():
            ret = self.get_text(ch)
            if ret != None:
                text += ret
        return text

    def run(self, node):
        if is_heading_tag(node.tag) and node.tag != 'h1':
            id = linkify_text(self.get_text(node))
            node.set('id', id)
        for ch in node.getchildren():
            self.run(ch)
        
def markdown_to_html(content):
    return markdown.markdown(content, extensions=[GithubFlavoredMarkdownExtension(), HeaderIdExtension()])

def html_parse_header(html):
    parser = HeadingsParser()
    parser.feed(html)
    result = {'tag': parser.inside_tag, 'text': parser.text }
    return result

def html_extract_text_element(html):
    result = html_parse_header(html)
    return result['text']