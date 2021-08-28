import collections
import mwclient
import re
import os


extractionPattern = re.compile('[^:/]+://(?:www\.)?([^/]+)')
countMarkBegin = '<!-- atwikibot:urlCount -->'
countMarkEnd = '<!-- /atwikibot:urlCount -->'


def get_cleaned_domain(line):
	# Extract the domain from the first URL appearing on a line, stripping away a leading "www." if any; returns None if no URL is found
	match = extractionPattern.search(line)
	if match:
		return match.group(1)
	return None


def main():
	site = mwclient.Site('wiki.archiveteam.org', path = '/')

	page = site.Pages['List of websites excluded from the Wayback Machine']

	# Extract domains from lines
	entries = collections.deque((line, get_cleaned_domain(line)) for line in page.text().split('\n'))

	# Identify blocks of URLs and sort them
	entries.append((None, None)) # Dummy entry at the end to trigger a last sorting if necessary
	output = []
	currentBlock = []
	urlCount = 0
	while entries:
		line, domain = entries.popleft()
		if domain is None:
			# Either a line without a URL or the dummy entry at the end
			if currentBlock:
				currentBlock.sort(key = lambda x: x[1])
				output.extend(x[0] for x in currentBlock)
				urlCount += len(currentBlock)
				currentBlock = []
			if line is not None: # Ignore the dummy entry
				output.append(line)
		elif line is not None:
			# line and domain are not None, i.e. this is a line with a URL in it
			currentBlock.append((line, domain))

	outputStr = '\n'.join(output)
	if countMarkBegin in outputStr and countMarkEnd in outputStr:
		countMarkBeginPos = outputStr.index(countMarkBegin)
		countMarkEndPos = outputStr.find(countMarkEnd, countMarkBeginPos) # End mark could be before begin mark
		if countMarkEndPos != -1:
			outputStr = outputStr[:countMarkBeginPos] + countMarkBegin + 'This list currently contains ' + str(urlCount) + ' URL' + ('s' if urlCount != 1 else '') + '.' + countMarkEnd + outputStr[countMarkEndPos + len(countMarkEnd):]

	# Update if necessary
	if page.text() != outputStr:
		site.login(os.environ['ATWIKIBOT_USERNAME'], os.environ['ATWIKIBOT_PASSWORD']) # Only log in when necessary
		page.save(outputStr)


main()
