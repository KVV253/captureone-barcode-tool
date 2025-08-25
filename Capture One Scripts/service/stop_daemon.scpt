-- === PATHS AND SETTINGS ===
set socketPath to "/tmp/barcode_daemon_socket"
set killCommand to "kill process" -- command sent to the daemon over the socket
set userLibraryPOSIX to POSIX path of (path to library folder from user domain)
set daemonPath to userLibraryPOSIX & "Scripts/Capture One Scripts/Background Scripts/BarcodeDaemon"

-- how many times to wait for shutdown after commands (1-second steps)
set gracefulRetries to 10
set hardRetries to 5

set logMsg to ""
set didSocketStop to false
set didTermKill to false
set didKill9 to false

-- === HELPERS ===
on getPidList(cmdPath)
	try
		-- Return a space-separated PID string or an empty string
		return do shell script "/usr/bin/pgrep -f " & quoted form of cmdPath & " | /usr/bin/tr '\\n' ' '"
	on error
		return ""
	end try
end getPidList

on waitGone(cmdPath, retries)
	repeat with i from 1 to retries
		set pidListCheck to my getPidList(cmdPath)
		if pidListCheck is "" then return true
		delay 1
	end repeat
	return false
end waitGone

-- === 1) Graceful stop via socket, if present ===
try
	if (do shell script "test -S " & quoted form of socketPath & " && echo ok || echo no") is "ok" then
		-- send command and wait
		do shell script "/usr/bin/printf %s " & quoted form of (killCommand & "
") & " | /usr/bin/nc -U " & quoted form of socketPath & " -w 2"
		set didSocketStop to true
		set logMsg to logMsg & "Sent socket command. "
		
		-- wait for exit
		if my waitGone(daemonPath, gracefulRetries) then
			display dialog "Barcode generator stopped via socket." buttons {"OK"} default button 1
			return
		else
			set logMsg to logMsg & "Process still running after socket command. "
		end if
	else
		set logMsg to logMsg & "Socket not found. "
	end if
on error errMsg
	set logMsg to logMsg & "Socket error: " & errMsg & " "
end try

-- === 2) Check and stop processes with SIGTERM ===
set pidList to my getPidList(daemonPath)
if pidList is not "" then
	try
		do shell script "/bin/kill " & pidList
		set didTermKill to true
		set logMsg to logMsg & "Sent SIGTERM to PID(s): " & pidList & ". "
	on error errMsg
		set logMsg to logMsg & "SIGTERM kill error: " & errMsg & " "
	end try
	
	-- wait for exit after SIGTERM
	if my waitGone(daemonPath, gracefulRetries) then
		display dialog "Barcode generator stopped (SIGTERM)." buttons {"OK"} default button 1
		return
	end if
else
	-- Nothing is running
	if didSocketStop then
		display dialog "Socket command sent; no active processes detected." buttons {"OK"} default button 1
	else
		display dialog "Barcode generator is not running." buttons {"OK"} default button 1
	end if
	return
end if

-- === 3) Force kill with SIGKILL, if still hanging ===
set pidList2 to my getPidList(daemonPath)
if pidList2 is not "" then
	try
		do shell script "/bin/kill -9 " & pidList2
		set didKill9 to true
		set logMsg to logMsg & "Sent SIGKILL to PID(s): " & pidList2 & ". "
	on error errMsg
		set logMsg to logMsg & "SIGKILL (kill -9) error: " & errMsg & " "
	end try
	
	-- final short wait
	if my waitGone(daemonPath, hardRetries) then
		display dialog "Barcode generator force-stopped (SIGKILL)." buttons {"OK"} default button 1
		return
	else
		display dialog "Failed to stop the process even with SIGKILL.
" & logMsg buttons {"OK"} default button 1
		return
	end if
else
	display dialog "Barcode generator stopped after SIGTERM." buttons {"OK"} default button 1
	return
end if
