import collections
import mwclient
import re
import os


def main():
	site = mwclient.Site('wiki.archiveteam.org', path = '/')

	page = site.Pages['URLTeam/Dead']

	entries = collections.deque(page.text().split('\n'))

	# Identify blocks of URLs and sort them
	entries.append(None) # Dummy entry at the end to trigger a last sorting if necessary
	output = []
	currentBlock = []
	urlCount = 0
	while entries:
		line = entries.popleft()
		if not line or not line.startswith('* '):
			# Either a line that isn't a list item or the dummy entry at the end
			if currentBlock:
				currentBlock.sort(key = str.lower)
				output.extend(currentBlock)
				currentBlock = []
			if line is not None: # Ignore the dummy entry
				output.append(line)
		else:
			# It's a list item and not the dummy entry.
			currentBlock.append(line)

	outputStr = '\n'.join(output)

	# Update if necessary
	if page.text() != outputStr:
		site.login(os.environ['ATWIKIBOT_USERNAME'], os.environ['ATWIKIBOT_PASSWORD']) # Only log in when necessary
		page.save(outputStr)


main()
