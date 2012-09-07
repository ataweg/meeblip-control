:set CLS=cls &
set CLS=

: make sure you have installed/unzip python-midi and pyinstaller-2.0 in the working directoy

:set PYTHON=C:\Program Files\Python26
set PYTHON=C:\Programme\Python26
set SOURCE_DIR=..\source
set BUILD_DIR=.\build
set BUILD_MIDI_DIR=.\python-midi

: ---------------------------------------------------------------------------
: setup/install midi module

cd /d %BUILD_MIDI_DIR%
%CLS%  "%PYTHON%\python.exe" setup.py install

: ---------------------------------------------------------------------------
cd /d %BUILD_DIR%

: translate GUI to python
%CLS% call "%PYTHON%\Lib\site-packages\PyQt4\pyuic4.bat" %SOURCE_DIR%\GUI\Ui_avrsynth_mainWindow.ui -o %SOURCE_DIR%\Ui_avrsynth_mainWindow.py

: run meeblipcontrol
%CLS% "%PYTHON%\python.exe" %SOURCE_DIR%\meeblipControl.py

: build an exe-file
%CLS% "%PYTHON%\python.exe" ..\pyinstaller-2.0\pyinstaller.py --onefile --noconsole --noconfirm --buildpath=.\release  %SOURCE_DIR%\meeblipControl.py

dist\meeblipControl.exe

cd ..
