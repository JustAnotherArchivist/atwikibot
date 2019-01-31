import mwclient
import os


def main():
	site = mwclient.Site('archiveteam.org', path = '/')

	# Retrieve full "In The Media" page
	mediaPage = site.Pages['In The Media']

	# Parse contents and extract first 10 entries
	entries = []
	for line in mediaPage.text().split('\n'):
		if not line:
			continue
		if line[0] == ';':
			entries.append([line])
		elif line[0] == ':':
			entries[-1].append(line)
	topEntries = entries[:10]

	# Construct contents of "Main Page/In The Media"
	contents = []
	contents.append('<!-- !!! Do not edit this page. It is updated automatically by a bot. !!! -->')
	contents.append('')
	for entry in topEntries:
		contents.append(';*{}'.format(entry[0][1:]))
		contents.extend(entry[1:])
	contents.append('')
	contents.append(';[[In The Media|More...]]')
	contentsStr = '\n'.join(contents)

	# Update if necessary
	mainPage = site.Pages['Main Page/In The Media']
	if mainPage.text() != contentsStr:
		site.login(os.environ['ATWIKIBOT_USERNAME'], os.environ['ATWIKIBOT_PASSWORD']) # Only log in when necessary
		mainPage.save(contentsStr)


main()
