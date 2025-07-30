# Generate a windows executable 
1. Deploy wineubuntu2404 development container.
2. Pull update python script into container
3. Run: wine /usr/lib/pythonwindows/Scripts/pyinstaller.exe kumg.py --onefile --distpath ./scripts/
