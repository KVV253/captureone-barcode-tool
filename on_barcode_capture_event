on CO_BarcodeScanned()
	tell application "Capture One"
		set currentDoc to current document
		set folderPath to captures of currentDoc
		set barcodeValue to barcode of currentDoc
		set img_name to capture name of currentDoc
		set img_counter to capture counter of currentDoc
	end tell
	
	set nextCaptureName to img_name & (img_counter + 1)
	set folderPathText to POSIX path of folderPath
	set dataToSend to folderPathText & "," & barcodeValue & "," & nextCaptureName
	set quotedData to quoted form of dataToSend
	
	set userLibraryPOSIX to POSIX path of (path to library folder from user domain)
	set daemonPath to userLibraryPOSIX & "Scripts/Capture One Scripts/Background Scripts/BarcodeDaemon"
	
	-- check if the daemon is running
	set isRunning to (do shell script "pgrep -f " & quoted form of daemonPath & " >/dev/null && echo true || echo false") as boolean
	if not isRunning then
		display dialog "Barcode Generator is not running. Launching..." buttons {"OK"} default button 1 giving up after 2
		do shell script quoted form of daemonPath & " &> /dev/null &"
		
		-- check the socket
		set socketPath to "/tmp/barcode_daemon_socket"
		set retries to 20
		set socketFound to false
		
		repeat with i from 1 to retries
			set retrLeft to (retries - i + 1)
			set messageText to "Waiting for Barcode Generator to start...
		Attempts left ~" & retrLeft & "."
			
			if (do shell script "test -S " & socketPath & " && echo ok || echo no") is "ok" then
				set socketFound to true
				display dialog "Barcode Generator successfully started." buttons {"OK"} default button 1 giving up after 1
				exit repeat
			else
				display dialog messageText buttons {"Cancel"} default button "Cancel" giving up after 6
			end if
		end repeat
		
		if not socketFound then
			display dialog "Socket " & socketPath & " was not found after 20 attempts. Barcode Generator is not responding." buttons {"OK"} default button 1
			return
		end if
		
	end if
	
	-- check if socket exists
	set socketPath to "/tmp/barcode_daemon_socket"
	if (do shell script "test -S " & quoted form of socketPath & " && echo ok || echo no") is not "ok" then
		display dialog "Socket " & socketPath & " not found. Barcode Generator is not responding." buttons {"OK"} default button 1
		return
	end if
	
	-- send data to socket
	try
		do shell script "echo " & quotedData & " | nc -U /tmp/barcode_daemon_socket"
	on error errMsg
		display dialog "Send error: " & errMsg buttons {"OK"} default button 1
		return
	end try
	
	-- update capture counter
	tell application "Capture One"
		try
			set c to capture counter of currentDoc
			if c is not missing value then set capture counter of currentDoc to c + 1
		end try
	end tell
end CO_BarcodeScanned
