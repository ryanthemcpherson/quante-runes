@echo off
echo Running UrgotMatchupHelper with debug output...
echo Current directory: %CD%
echo Files in current directory:
dir
echo.
echo Running application...
UrgotMatchupHelper.exe --debug > debug_output.txt 2>&1
echo.
echo Application output saved to debug_output.txt
echo Press any key to view the output...
pause > nul
type debug_output.txt
echo.
echo Press any key to exit...
pause > nul
