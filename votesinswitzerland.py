import mwclient
import os
import requests


BOT_OPEN_TAG = '<!-- Do not edit the list between this line and /bot; it is edited automatically by a bot. -->'
BOT_CLOSE_TAG = '<!-- /bot -->'


def get_archivebot_votes_in_switzerland_pages(site):
	for page in site.allpages(prefix = 'ArchiveBot/Votes in Switzerland/'):
		if not page.name.endswith('/list'):
			yield page


def generate_page_list(site):
	return '\n'.join('* [[{}]]'.format(page.name) for page in get_archivebot_votes_in_switzerland_pages(site))


def maybe_edit_wiki(site, newList):
	page = site.Pages['Votes in Switzerland']
	oldText = page.text()
	if BOT_OPEN_TAG + '\n' not in oldText or '\n' + BOT_CLOSE_TAG not in oldText:
		print('Error: bot tag not found.')
		return
	prefix, remainder = oldText.split(BOT_OPEN_TAG + '\n', 1)
	oldList, suffix = remainder.split('\n' + BOT_CLOSE_TAG, 1)
	if oldList != newList:
		site.login(os.environ['ATWIKIBOT_USERNAME'], os.environ['ATWIKIBOT_PASSWORD'])
		pageText = prefix + BOT_OPEN_TAG + '\n' + newList + '\n' + BOT_CLOSE_TAG + suffix
		page.save(pageText)


def main():
	site = mwclient.Site('wiki.archiveteam.org', path = '/')
	maybe_edit_wiki(site, generate_page_list(site))


main()
