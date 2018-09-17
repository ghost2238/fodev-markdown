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
@app.route("/<project_name>/<file>")
def show_table(project_name, file=''):    
    projects = get_projects()

    if project_name not in projects:
        return render_template('select.html', )

    project = projects[project_name]
    print(projects[project_name])
    if file is '':
        file = project['items'][0]['filename']

    sanitized_file = file.replace('..','')
    if 'github_repo' in project:
        with open(config.md_path+project['route_name']+'/'+sanitized_file, 'r', ) as fp:
            content = ''.join(fp.readlines())
    else:
        url = 'https://raw.githubusercontent.com/'+project.github_repo+'/master/'+sanitized_file
        r = requests.get(url)
        content = r.text

    html = markdown.markdown(content, extensions=[GithubFlavoredMarkdownExtension()])
    return render_template('index.html', base_href=config.base_href, file=sanitized_file, html_content=html, project=project)

@app.route("/")
def show_index():
    projects = get_projects()
    return render_template('select.html', base_href=config.base_href, projects=projects)