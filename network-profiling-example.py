from chrome_remote_shell import Shell
import json
from subprocess import Popen, check_output
import time

# run google chrome with (hopefully) all user interaction and automatic network requests disabled
chrome_proc = Popen('google-chrome --remote-debugging-port=9876 --no-default-browser-check --user-data-dir=/tmp/chrome-profiling --no-first-run --disable-background-networking --disable-client-side-phishing-detection --disable-component-update --disable-default-apps --disable-hang-monitor --disable-popup-blocking --disable-prompt-on-repost --disable-sync --disable-web-resources --enable-logging --ignore-certificate-errors --use-mock-keychain --dbus-stub about:blank'.split(' '))

def wait_for_chrome():
	print "Waiting for chrome to be ready ",
	for i in range(100):
		print ".",
		try:
			# create debugging api client instance
			s=Shell(port=9876)
			for i,tab in enumerate(s.tablist):
				if tab['type'] == 'page':
					# connect to the debugging api
					s.connect(i)
					print "connected", tab, i
					return s
		except:
			time.sleep(0.1)
			pass
	raise "No chrome found"
time.sleep(1)
s = wait_for_chrome()
time.sleep(1)

# start receiving Page related events (esp. onLoad event)
s.do("Page.enable")

# start receiving Network profiling events
s.do("Network.enable")

# clear cache
# unneccessary as we have a clean profile
#### s.do("Network.clearBrowserCache")

# navigate to the page we want to profile
s.do("Page.navigate", url="https://www.ugb.de")

method = ""

starttime=99999999
endtime=0

# receive events until the main Page contents are fully loaded
while method != "Page.frameStoppedLoading":
	r = json.loads(s.soc.recv())
	if not 'method' in r: continue
	method = r['method']
	params = r['params']

	# print some information from the profiling event, there is a lot more
	if 'timestamp' in params:
		print str(params['timestamp']) + ': ',
		if params['timestamp'] < starttime: starttime = params['timestamp']
		if params['timestamp'] > endtime: endtime = params['timestamp']
	print method,
	if 'requestId' in params: print '    '+params['requestId'],
	if 'request' in params and 'url' in params['request']: print '    '+params['request']['url'],
	print ""
	if method == 'Network.loadingFailed': print(params)
	# to dump all params, do this:
	# print(params)

print "Page load took "+str(endtime-starttime)+" seconds"

# close websocket connection
s.close()

time.sleep(1)

# tell chrome to close itself
print("calling close_tab")
s.close_tab(0)

# wait a little, kill it if it's still open
time.sleep(1)
print("sending TERM signal")
chrome_proc.send_signal(15)


time.sleep(0.5)
print("sending KILL signal")
chrome_proc.send_signal(9)

# delete temp folder
check_output(['rm', '-r', '/tmp/chrome-profiling'])

