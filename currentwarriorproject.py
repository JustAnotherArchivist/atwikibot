import mwclient
import os
import requests


# Retrieve current project
def get_current_default_project():
	response = requests.get('https://warriorhq.archiveteam.org/projects.json')
	projects = response.json()
	defaultName = projects['auto_project']
	for p in projects['projects']:
		if p['name'] == defaultName:
			return p
	return None


def default_project_to_wiki_text(project):
	return '{{CurrentWarrior|' + project['name'] + '|' + project['title'] + '}}'


# Update the wiki page if necessary
def maybe_edit_wiki(pageText):
	site = mwclient.Site('wiki.archiveteam.org', path = '/')
	page = site.Pages['CurrentWarriorProject']
	if page.text() != pageText:
		site.login(os.environ['ATWIKIBOT_USERNAME'], os.environ['ATWIKIBOT_PASSWORD']) # Only log in when necessary
		page.save(pageText)


maybe_edit_wiki(default_project_to_wiki_text(get_current_default_project()))
