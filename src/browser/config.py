SECURITY_ARGS = [
	'--disable-web-security',
	'--disable-site-isolation-trials',
	'--disable-features=IsolateOrigins,site-per-process',
]

BROWSER_ARGS = [
    '--disable-sandbox',
	'--enable-blink-features=IdleDetection',
	'--disable-blink-features=AutomationControlled',
	'--disable-infobars',
	'--disable-background-timer-throttling',
	'--disable-popup-blocking',
	'--disable-backgrounding-occluded-windows',
	'--disable-renderer-backgrounding',
	'--disable-window-activation',
	'--disable-focus-on-load',
	'--no-first-run',
	'--no-default-browser-check',
	'--no-startup-window',
	'--window-position=0,0',
    '--remote-debugging-port=9222'
]

IGNORE_DEFAULT_ARGS = ['--enable-automation']