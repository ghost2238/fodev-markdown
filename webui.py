#!/usr/bin/python3
from flask import Flask, render_template, redirect, request
from data import Data, Page
import config

app = Flask(__name__)

def base_redirect(url):
    return redirect(config.base_href+url, code=302)

@app.route("/<project_name>")
@app.route("/<project_name>/<page_route>")
@app.route("/<project_name>/<page_route>/<doc_route>")
def display_page(project_name, page_route='', doc_route=''):    
    Data.load()

    project = Data.get_project(project_name)
    if project is None:
        return show_projects_page()

    if project.has_pages() is False:
        return show_projects_page()

    # Try to get page by route if it is defined
    # otherwise get the first page.
    page = None
    if page_route is '':
        page = project.get_pages()[0]
    else:
        page = project.get_page(page_route)

    if page == None:
        return show_projects_page()
        
    # If the page has no documents, try to fetch first page with documents
    # If not, redirect to project page.
    if page.has_documents() is False:
        for p in project.get_pages():
            if p.has_documents():
                page = p
        if page == None:
            return show_projects_page()

    doc = None
    if doc_route is '':
        doc = page.documents[0]
    else:
        doc = page.get_document(doc_route)

    if doc == None:
        return show_projects_page()

    return render_template('index.html', base_href=config.base_href, 
        selected_page=page, page=page, doc_route=doc.route, docs=page.documents, html_content=doc.to_html(), project=project)

def show_projects_page():
    return render_template('select.html', base_href=config.base_href, projects=Data.get_projects())

@app.route("/")
def show_index():
    Data.load()
    return show_projects_page()

@app.errorhandler(404)
def page_not_found(e):
    return base_redirect('')

def show_error(error):
    return render_template('error.html', error=error)