Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Kill the app
On Error Resume Next
WshShell.Run "taskkill /F /IM ComputerLockdown.exe", 0, True
On Error GoTo 0

' Remove registry policies
On Error Resume Next
WshShell.RegDelete "HKCU\Software\Policies\Microsoft\Windows\System\DisableCMD"
WshShell.RegDelete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System\DisableTaskMgr"
WshShell.RegDelete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System\DisableRegistryTools"
WshShell.RegDelete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\NoControlPanel"
WshShell.RegDelete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\NoSettings"
On Error GoTo 0

' Delete config folder
configDir = WshShell.ExpandEnvironmentStrings("%PROGRAMDATA%") & "\ComputerLockdown"
If fso.FolderExists(configDir) Then
    fso.DeleteFolder configDir, True
End If

' Delete lock file
lockFile = WshShell.ExpandEnvironmentStrings("%TEMP%") & "\computer_lockdown.lock"
If fso.FileExists(lockFile) Then
    fso.DeleteFile lockFile, True
End If

MsgBox "DONE! Everything is reset." & vbCrLf & vbCrLf & "CMD, Task Manager, and Registry are unblocked." & vbCrLf & "You can run ComputerLockdown.exe fresh now.", vbInformation, "Computer Lockdown Reset"
