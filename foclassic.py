#!/usr/bin/python3
from flask import Flask, render_template, redirect, request
from src.data import Data
from src.routing import Routing
import config
import logging

logging.basicConfig(filename=config.base_path+'program.log',level=logging.DEBUG)

app = Flask(__name__)

def base_redirect(url):
    return redirect(config.base_href+url, code=302)

def bootstrap():
    Routing.init(config.base_path, '/')

# Why are we even using flask... 
# TODO: use WSGI directly instead...
@app.route("/<page_route>/<doc_route>")
def display_page(page_route='', doc_route=''): 
    bootstrap()
    return Routing.resolve_route('foclassic', page_route, doc_route)

@app.route('/<page_route>')
def display_page2(page_route=''):
    bootstrap()
    return Routing.resolve_route('foclassic', page_route, '')

@app.route("/")
def show_index():
    bootstrap()
    return Routing.resolve_route('foclassic', '', '')

@app.errorhandler(404)
def page_not_found(e):
    return base_redirect('')

def show_error(error):
    return render_template('error.html', error=error)