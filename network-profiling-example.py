from chrome_remote_shell import Shell
import json
from subprocess import Popen

# run google chrome with (hopefully) all user interaction and automatic network requests disabled
chrome_proc = Popen('google-chrome --remote-debugging-port=9876 --no-default-browser-check --user-data-dir=/tmp/chrome-profiling --no-first-run --disable-background-networking --disable-client-side-phishing-detection --disable-component-update --disable-default-apps --disable-hang-monitor --disable-popup-blocking --disable-prompt-on-repost --disable-sync --disable-web-resources --enable-logging --ignore-certificate-errors --use-mock-keychain --dbus-stub', shell=True)

# create debugging api client instance
s=Shell(port=9876)

# connect to the debugging api
s.connect(0)

# start receiving Page related events (esp. onLoad event)
s.soc.send(json.dumps({"id":0, "method":"Page.enable"}))

# start receiving Network profiling events
s.soc.send(json.dumps({"id":0, "method":"Network.enable"}))

# clear cache
# unneccessary as we have a clean profile
#### s.soc.send(json.dumps({"id":0, "method":"Network.clearBrowserCache"}))

# navigate to the page we want to profile
s.soc.send(json.dumps({"id":0, "method":"Page.navigate", "params":{"url":"https://www.ugb.de"}}))

method = ""

# receive events until the main Page contents are fully loaded
while method != "Page.frameStoppedLoading":
	r = json.loads(s.soc.recv())
	if not 'method' in r: continue
	method = r['method']
	params = r['params']

	# print some information from the profiling event, there is a lot more
	if 'timestamp' in params:
		print str(params['timestamp']) + ': ',
	print method,
	if 'requestId' in params: print '    '+params['requestId'],
	if 'request' in params and 'url' in params['request']: print '    '+params['request']['url'],
	print ""

	# to dump all params, do this:
	# print(params)


# close websocket connection
s.close()

# tell chrome to close itself
s.close_tab(0)

# wait a little, kill it if it's still open
time.sleep(0.1)
chrome_proc.send_signal(9)

# delete temp folder
check_output(['rm', '-r', '/tmp/chrome-profiling'])

