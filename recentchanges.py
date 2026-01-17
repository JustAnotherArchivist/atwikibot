from __future__ import annotations  # PEP 585 for Python 3.7 and 3.8
import collections
import logging
import requests
import time
import typing
import urllib.parse


def get_new(newestRc: typing.Optional[tuple[str, int]]) -> tuple[list[dict], tuple[str, int]]:
	'''
	Fetches edits made after newestRc = (newestTimestamp, newestRcId), which shall both refer to the last change already known/processed.
	newestTimestamp is a timestamp in YYYY-MM-DDTHH:MM:SSZ format; newestRcId is the internal ID of the change.
	The return value are the list of changes after newestRcId in chronological order (as returned by MW), and a new (newestTimestamp, newestRcId) tuple.
	If newestRc is None, this returns an empty list of changes and the timestamp and rev ID of the most recent edit (for initialisation of a feed).
	'''

	logging.info(f'Fetching with newestRc = {newestRc!r}')
	if newestRc is None:
		newestTimestamp, newestRcId = None, None
	else:
		newestTimestamp, newestRcId = newestRc
	rcend = f'&rcend={newestTimestamp}' if newestTimestamp else ''
	r = requests.get(f'https://wiki.archiveteam.org/api.php?action=query&list=recentchanges&rcdir=older&format=json&rcprop=user|comment|timestamp|sizes|title|flags|ids|loginfo&continue=&rclimit=500{rcend}',
	                 timeout = 5,
	                )
	r.raise_for_status()
	o = r.json()
	if not o['query']['recentchanges']:
		return [], (newestTimestamp, newestRcId)
	rc = o['query']['recentchanges']
	changes = []
	if newestRcId is not None:
		for c in rc:
			if c['rcid'] <= newestRcId:
				break
			changes.append(c)
	return changes[::-1], (rc[0]['timestamp'], rc[0]['rcid'])


def truncate(s: str, limit: int) -> str:
	'''If s is longer than limit, split on words and return a truncated version no longer than limit.'''
	if len(s) <= limit:
		return s
	words = s.split(' ')
	trunLength = 0
	trun = []
	while words and trunLength + 1 + len(words[0]) < limit - 1:
		word = words.pop(0)
		trunLength += 1 + len(word)
		trun.append(word)
	return f'{" ".join(trun)}…'


def format_change(change: dict) -> typing.Optional[str]:
	'''Formats a change for posting to IRC. Returns None if it's an event that isn't handled and not to be reported to IRC.'''
	lenChange = False
	title = change['title']
	url = None
	if change['type'] == 'new':
		verb = 'created'
		url = f'https://wiki.archiveteam.org/?oldid={change["revid"]}'
		lenChange = True
	elif change['type'] == 'edit':
		verb = 'edited'
		url = f'https://wiki.archiveteam.org/?diff={change["revid"]}&oldid={change["old_revid"]}'
		lenChange = True
	elif change['type'] == 'log' and change['logtype'] == 'delete':
		verb = 'deleted'
		url = ''
	elif change['type'] == 'log' and change['logtype'] == 'upload':
		verb = 'uploaded'
		url = f'https://wiki.archiveteam.org/?title={urllib.parse.quote(change["title"])}'
	elif change['type'] == 'log' and change['logtype'] == 'move':
		verb = 'moved'
		title = f'{change["title"]} to {change["logparams"]["target_title"]}'
		url = f'https://wiki.archiveteam.org/?title={urllib.parse.quote(change["logparams"]["target_title"])}'
	elif change['type'] == 'log' and change['logtype'] == 'rights':
		verb = 'changed the user rights of'
	else:
		return
	comment = f'{truncate(change["comment"], 50)}' if change["comment"] else ''
	lenChange = f'{change["newlen"] - change["oldlen"]:+d}' if lenChange else ''
	joiner = ', ' if comment and lenChange else ''
	lenChangeAndComment = f' ({lenChange}{joiner}{comment})' if lenChange or comment else ''
	url = f': {url}' if url else ''
	return f'{change["user"]} {verb} {title}{lenChangeAndComment}{url}'


def format_bot_changes(username, changes):
	# [-1] is the newest edit, increment its timestamp by one second for the URL
	offset = ''.join(c for c in changes[-1]['timestamp'] if c in '0123456789') or '0'
	offset = str(int(offset) + 1)
	if len(offset) == 14:
		url = f': https://wiki.archiveteam.org/index.php?title=Special:Contributions/{urllib.parse.quote_plus(username)}&offset={offset}&limit={len(changes)}&namespace=2&wpfilters%5B%5D=nsInvert&wpfilters%5B%5D=associated'
	else:
		url = f' but I couldn\'t generate a link for them.'
	return f'{username} made {len(changes)} bot changes{url}'


def main():
	botCounts = collections.Counter()
	botChanges = collections.defaultdict(list)
	# Get initial TS/rcid tuple
	_, newestRc = get_new(None)
	time.sleep(60)
	while True:
		try:
			changes, newestRc = get_new(newestRc)
		except Exception as e:
			logging.error('get_new failed', exc_info = e)
			time.sleep(60)
			continue

		# Filter User and User_talk namespace log entries (but not e.g. rights changes)
		filtered = []
		for change in changes:
			if change['ns'] in (2, 3) and change['type'] != 'log':
				logging.info(f'Skipping user namespace change: {change!r}')
				continue
			filtered.append(change)
		changes = filtered

		botCounts.update(change['user'] for change in changes if change.get('bot', None) is not None)
		for change in changes:
			if change.get('bot', None) is not None and botCounts[change['user']] > 1:
				logging.info(f'Collapsing bot change: {change!r}')
				botChanges[change['user']].append(change)
				continue
			logging.info(f'Regular change: {change!r}')
			formatted = format_change(change)
			if formatted and not any(ord(c) < 32 for c in formatted):
				logging.info(f'Formatted: {formatted!r}')
				print(formatted, flush = True)
			else:
				logging.warning(f'Suppressed change because it was un- or ill-formatted: {change!r}')
		for item in botChanges.items():
			formatted = format_bot_changes(*item)
			logging.info(f'Formatted (bot): {formatted!r}')
			print(formatted, flush = True)
		botCounts.clear()
		botChanges.clear()
		time.sleep(60)


if __name__ == '__main__':
	logging.basicConfig(
		format = '{asctime}.{msecs:03.0f}  {levelname}  {name}  {message}',
		datefmt = '%Y-%m-%d %H:%M:%S',
		style = '{',
		level = logging.INFO,
	)
	main()
