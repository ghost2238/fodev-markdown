#!/usr/bin/python3
from flask import Flask, render_template, redirect
from mdx_gfm import GithubFlavoredMarkdownExtension
import requests
import markdown
import config
import json
import re

app = Flask(__name__)

def get_projects():
    with open(config.base_path+'/content.json') as file:
        content = json.load(file)
    return content

@app.route("/<project_name>")
@app.route("/<project_name>/<page_route>")
@app.route("/<project_name>/<page_route>/<doc_route>")
def show_table(project_name, page_route='', doc_route=''):    
    projects = get_projects()

    if project_name not in projects:
        return render_template('select.html', )

    project = projects[project_name]
    if page_route is '':
        page = project['pages'][0]
    else:
        page = project['pages'][page_route]
    
    docs = page['docs']
    if doc_route is '':
        # Take first document on page.
        doc = docs[0]
        doc_route = doc['route']
    else:
        for x in range(0,len(docs)):
            if doc_route == docs[x]['route']:
                doc = docs[x]

    url = doc['url']
    url = url.replace('..','')
    github_repo = ''
    protocol = 'file'
    if url.find('://') != -1:
        spl = url.split('://')
        if spl[0] == 'github':
            protocol = 'github'
            last_slash = spl[1].rfind('/')
            github_repo = spl[1][:last_slash] 
            url = spl[1][last_slash:]

    if protocol == 'file':
        with open(config.md_path+project['route_name']+'/'+url, 'r', ) as fp:
            content = ''.join(fp.readlines())
    else:
        request_url = 'https://raw.githubusercontent.com/'+github_repo+'/master/'+url
        r = requests.get(request_url)
        content = r.text

    html = markdown.markdown(content, extensions=[GithubFlavoredMarkdownExtension()])
    return render_template('index.html', base_href=config.base_href, 
        selected_page=page, page_route=page_route, doc_route=doc_route, docs=docs, url=url, html_content=html, project=project)

@app.route("/")
def show_index():
    projects = get_projects()
    return render_template('select.html', base_href=config.base_href, projects=projects)