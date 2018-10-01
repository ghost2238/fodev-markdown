from flask import Flask, render_template, redirect, request
from src.data import Data
import logging

# Resolves various routes from files in root, 
# like index.py or routing files for specific projects.
class Routing():
    base_path = None
    base_href = None
    @staticmethod
    def init(base_path, base_href):
        Routing.base_path = base_path
        Routing.base_href = base_href
        logging.basicConfig(filename=Routing.base_path+'program.log',level=logging.DEBUG)

    @staticmethod
    def show_projects_page():
        return render_template('select.html', base_href=Routing.base_href, projects=Data.get_projects())

    @staticmethod
    def resolve_route(project_route, page_route, doc_route):
        project = Data.get_project(project_route)
        if project is None:
            return Routing.show_projects_page()

        if project.has_pages() is False:
            logging.error('Project ' + project.display_name + ' has no pages')
            return Routing.show_projects_page()

        # Try to get page by route if it is defined
        # otherwise get the first page.
        page = project.get_page(page_route)
        if page == None:
            return Routing.show_projects_page()
        
        # If the page has no documents, try to fetch first page with documents
        # If not, redirect to project page.
        if page.has_documents() is False:
            page = project.get_page_with_docs()

        if page == None:
            return Routing.show_projects_page()

        doc = page.get_document(doc_route)
        if doc == None:
            return Routing.show_projects_page()

        return render_template('index.html', base_href=Routing.base_href, 
            selected_page=page, page=page, doc_route=doc.route, docs=page.documents, html_content=doc.to_html(), project=project)