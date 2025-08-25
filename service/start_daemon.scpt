set userLibraryPOSIX to POSIX path of (path to library folder from user domain)
set daemonPath to userLibraryPOSIX & "Scripts/Capture One Scripts/Background Scripts/BarcodeDaemon"

-- check if the daemon is running
set isRunning to (do shell script "pgrep -f " & quoted form of daemonPath & " >/dev/null && echo true || echo false") as boolean
if not isRunning then
	display dialog "Barcode Generator is not running. Launching..." buttons {"OK"} default button 1
	do shell script quoted form of daemonPath & " &> /dev/null &"
	delay
	
	-- check socket
	set socketPath to "/tmp/barcode_daemon_socket"
	set retries to 10
	set socketFound to false
	
	repeat with i from 1 to retries
		set retrLeft to (retries - i + 1)
		set messageText to "Waiting for BarcodeDaemon to start...
	Attempts left ~" & retrLeft & "."
		
		if (do shell script "test -S " & socketPath & " && echo ok || echo no") is "ok" then
			set socketFound to true
			display dialog "Barcode Generator successfully started." buttons {"OK"} default button 1
			exit repeat
		else
			delay 6
		end if
	end repeat
	
	if not socketFound then
		display dialog "Socket " & socketPath & " not found after 10 attempts. BarcodeDaemon is not responding." buttons {"OK"} default button 1
		return
	end if
	
else
	display dialog "Barcode Generator is already running." buttons {"OK"} default button 1
end if
