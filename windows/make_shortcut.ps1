# Creates a "CP Controller" shortcut on the Desktop, with the game's icon.
# The shortcut runs play.bat, which updates the game (git pull) and starts it.
$game = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$link = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop 'CP Controller.lnk'))
$link.TargetPath = Join-Path $PSScriptRoot 'play.bat'
$link.WorkingDirectory = $game
$link.IconLocation = (Join-Path $game 'railgame\assets\icon.ico') + ',0'
$link.WindowStyle = 7  # start the console window minimised
$link.Description = 'CP Controller'
$link.Save()
Write-Host "Shortcut 'CP Controller' created on the Desktop."
