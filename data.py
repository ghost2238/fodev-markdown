#!/usr/bin/python3
class Project:
    def __init__(self, display_name=None, route_name=None, github_repo = None):
        self.route_name = route_name
        self.display_name = display_name
        if display_name is None:
            self.display_name = route_name
        self.github_repo = github_repo
        self.menu_items = []

class MenuItem:
    def __init__(self, title, filename):
        self.title = title
        self.filename = filename