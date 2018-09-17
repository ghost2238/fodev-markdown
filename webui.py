#!/usr/bin/python3
from flask import Flask, render_template, redirect
from mdx_gfm import GithubFlavoredMarkdownExtension
import requests
import markdown
import config
import json
import re

app = Flask(__name__)

@app.route("/<project_name>")
@app.route("/<project_name>/<file>")
def show_table(project_name, file=''):
    
    if project_name not in config.projects:
        return render_template('index.html')
    
    project = config.projects[project_name]
    if file is '':
            file = project.menu_items[0].filename
    
    sanitized_file = file.replace('..','')
    if project.github_repo == None:
        
        with open(config.md_path+project.route_name+'/'+sanitized_file, 'r', ) as fp:
            content = ''.join(fp.readlines())
    else:
        url = 'https://raw.githubusercontent.com/'+project.github_repo+'/master/'+sanitized_file
        r = requests.get(url)
        content = r.text

    html = markdown.markdown(content, extensions=[GithubFlavoredMarkdownExtension()])
    return render_template('index.html', base_href=config.base_href, file=sanitized_file, html_content=html, project=project)

@app.route("/")
def show_index():
    return render_template('select.html', base_href=config.base_href, projects=config.projects.values())