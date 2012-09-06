'''
Created on Mar 20, 2012

@author: Matt
'''
import sys
import hashlib
from PyQt4 import QtGui, QtCore
from Ui_avrsynth_mainWindow import Ui_MainWindow
from windowHandler import MainWindowHandler
from functools import partial
from pygame import midi

class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.midiOutputDevicesDict = {}
        self.midiInputDevicesDict = {}
        self.onValue = 64
        self.offValue = 0
        #control change values
        self.dialDict = {
                         'pwmDepth_Dial':       14,   # PWMDEPTH        = MIDICC + $0E ; Knob 1 14    ; (=LFO2LEVEL)
                         'midiKnob2_Dial':      15,   # MIDI_KNOB_2     = MIDICC + $0F ; Knob 2 15
                         'midiKnob3_Dial':      16,   # MIDI_KNOB_3     = MIDICC + $10 ; Knob 3 16
                         'midiKnob4_Dial':      17,   # MIDI_KNOB_4     = MIDICC + $11 ; Knob 4 17
                         'lfo2Freq_Dial':       18,   # LFO2FREQ        = MIDICC + $12 ; Knob 5 18    ; currently not used
                         'fmDepth_Dial':        19,   # FMDEPTH         = MIDICC + $13 ; Knob 6 19    ; currently not used
                         'mixerBalance_Dial':   20,   # MIXER_BALANCE   = MIDICC + $14 ; Knob 7 20
                         'masterVolume_Dial':   21,   # MASTER_VOLUME   = MIDICC + $15 ; Knob 8 21

                         'attackTime_Slider':   22,   # ATTACKTIME      = MIDICC + $16 ; _Slider 1 22 ; DCA envelope
                         'decaytTme_Slider':    23,   # DECAYTIME       = MIDICC + $17 ; _Slider 2 23
                         'sustainLevel_Slider': 24,   # SUSTAINLEVEL    = MIDICC + $18 ; _Slider 3 24
                         'releaseTime_Slider':  25,   # RELEASETIME     = MIDICC + $19 ; _Slider 4 25
                         'attackTime2_Slider':  26,   # ATTACKTIME2     = MIDICC + $1A ; _Slider 5 26 ; DCF envelope
                         'decayTime2_Slider':   27,   # DECAYTIME2      = MIDICC + $1B ; _Slider 6 27
                         'sustainLevel2_Slider':28,   # SUSTAINLEVEL2   = MIDICC + $1C ; _Slider 7 28
                         'releaseTime2_Slider': 29,   # RELEASETIME2    = MIDICC + $1D ; _Slider 8 29

#                        'sw1':                 44,   # SW1             = MIDICC + $2C ; Reserved
#                        'sw2':                 45,   # SW2             = MIDICC + $2D ; Reserved
#                        'sw3':                 46,   # SW3             = MIDICC + $2E ; Reserved
#                        'sw4':                 47,   # SW4             = MIDICC + $2F ; Reserved

                         'resonanceDial':       48,   # RESONANCE       = MIDICC + $30
                         'cutoffDial':          49,   # CUTOFF          = MIDICC + $31
                         'lfoRateDial':         50,   # LFOFREQ         = MIDICC + $32
                         'lfoDepthDial':        51,   # PANEL_LFOLEVEL  = MIDICC + $33
                         'envAmountDial':       52,   # VCFENVMOD       = MIDICC + $34
                         'glideAmountDial':     53,   # PORTAMENTO      = MIDICC + $35
                         'oscPWMDial':          54,   # PULSE_KNOB      = MIDICC + $36 ; (=LFO2FREQ)
                         'oscDetuneDial':       55,   # OSC_DETUNE      = MIDICC + $37

                                                      # X               = MIDICC + $38 ; Undefined
                                                      # X               = MIDICC + $39 ; Undefined
                         'filterDecaySlider':   58,   # KNOB_DCF_DECAY  = MIDICC + $3A
                         'filterAttackSlider':  59,   # KNOB_DCF_ATTACK = MIDICC + $3B
                         'ampDecaySlider':      60,   # KNOB_AMP_DECAY  = MIDICC + $3C
                         'ampAttackSlider':     61}   # KNOB_AMP_ATTACK = MIDICC + $3D
                                                      # X               = MIDICC + $3E ; Undefined
                                                      # X               = MIDICC + $3F ; Undefined

        self.buttonDict = {                                                                                     # S_KNOB_SHIFT      = MIDICC + $40
                           'oscFMOn':           [65, self.onValue], 'oscFMOff':          [65, self.offValue],   # S_OSC_FM          = MIDICC + $41
                           'lfoRandomOn':       [66, self.onValue], 'lfoRandomOff':      [66, self.offValue],   # S_LFO_RANDOM      = MIDICC + $42
                           'lfoSquareOn':       [67, self.onValue], 'lfoTriangleOn':     [67, self.offValue],   # S_LFO_WAVE        = MIDICC + $43
                           'lpOn':              [68, self.offValue],'hpOn':              [68, self.onValue],    # S_FILTER_MODE     = MIDICC + $44
                           'distortionOn':      [69, self.onValue], 'distortionOff':     [69, self.offValue],   # S_DISTORTION      = MIDICC + $45
                           'lfoOn':             [70, self.onValue], 'lfoOff':            [70, self.offValue],   # S_LFO_ENABLE      = MIDICC + $46
                           'lfoOscOn':          [71, self.onValue], 'lfoFilterOn':       [71, self.offValue],   # S_LFO_DEST        = MIDICC + $47

                           'antiAliasOn':       [72, self.onValue], 'antiAliasOff':      [72, self.offValue],   # S_ANTI_ALIAS      = MIDICC + $48
                           'oscBOctaveOn':      [73, self.onValue], 'oscBOctaveOff':     [73, self.offValue],   # S_OSCB_OCT        = MIDICC + $49
                           'oscBOn':            [74, self.onValue], 'oscBOff':           [74, self.offValue],   # S_OSCB_ENABLE     = MIDICC + $4A
                           'oscBWaveSquare':    [75, self.onValue], 'oscBWaveTri':       [75, self.offValue],   # S_OSCB_WAVE       = MIDICC + $4B
                           'envSustainOn':      [76, self.onValue], 'envSustainOff':     [76, self.offValue],   # S_SUSTAIN         = MIDICC + $4C
                           'oscANoiseOn':       [77, self.onValue], 'oscANoiseOff':      [77, self.offValue],   # S_OSCA_NOISE      = MIDICC + $4D
                           'pwmSweepOn':        [78, self.onValue], 'pwmSweepOff':       [78, self.offValue],   # S_PWM_SWEEP       = MIDICC + $4E
                           'oscAPWMOn':         [79, self.onValue], 'oscASawOn':         [79, self.offValue],   # S_OSCA_WAVE       = MIDICC + $4F

                           'switch30On':        [80, self.onValue], 'switch30Off':       [80, self.offValue],   # S_MIX_RING        = MIDICC + $50
                           'switch31On':        [81, self.onValue], 'switch31Off':       [81, self.offValue],   # S_USER_3_1        = MIDICC + $51
                           'switch32On':        [82, self.onValue], 'switch32Off':       [82, self.offValue],   # S_USER_3_2        = MIDICC + $52
                           'switch33On':        [83, self.onValue], 'switch33Off':       [83, self.offValue],   # S_TRANSPOSE       = MIDICC + $53
                           'switch34On':        [84, self.onValue], 'switch34Off':       [84, self.offValue],   # S_DCA_MODE        = MIDICC + $54
                           'switch35On':        [85, self.onValue], 'switch35Off':       [85, self.offValue],   # S_MODWHEEL_ENABLE = MIDICC + $55
                           'switch36On':        [86, self.onValue], 'switch36Off':       [86, self.offValue],   # S_LFO_KBD_SYNC    = MIDICC + $56
                           'switch37On':        [87, self.onValue], 'switch37Off':       [87, self.offValue],   # S_DCF_KBD_TRACK   = MIDICC + $57

                           'switch40On':        [88, self.onValue], 'switch40Off':       [88, self.offValue],   # S_USER_4_0        = MIDICC + $58
                           'switch41On':        [89, self.onValue], 'switch41Off':       [89, self.offValue],   # S_USER_4_1        = MIDICC + $59
                           'switch42On':        [90, self.onValue], 'switch42Off':       [90, self.offValue],   # S_USER_4_2        = MIDICC + $5A
                           'switch43On':        [91, self.onValue], 'switch43Off':       [91, self.offValue],   # S_USER_4_3        = MIDICC + $5B
                           'switch44On':        [92, self.onValue], 'switch44Off':       [92, self.offValue],   # S_USER_4_4        = MIDICC + $5C
                           'switch45On':        [93, self.onValue], 'switch45Off':       [93, self.offValue],   # S_USER_4_5        = MIDICC + $5D
                           'switch46On':        [94, self.onValue], 'switch46Off':       [94, self.offValue],   # S_LFO2_WAVE       = MIDICC + $5E
                           'switch47On':        [95, self.onValue], 'switch47Off':       [95, self.offValue]}   # S_LFO2_RANDOM     = MIDICC + $5F

        self.buttonBoxDict = {
                              'oscAWaveBox':    'oscAWaveGroup',
                              'oscANoiseBox':   'oscANoiseGroup',
                              'oscBEnableBox':  'oscBEnableGroup',
                              'oscBWaveBox':    'oscBWaveGroup',
                              'oscBOctaveBox':  'oscBOctaveGroup',
                              'oscFMBox':       'oscFMGroup',
                              'lfoEnableBox':   'lfoEnableGroup',
                              'lfoDestBox':     'lfoDestGroup',
                              'lfoWaveBox':     'lfoWaveGroup',
                              'lfoRandomBox':   'lfoRandomGroup',
                              'filterModeBox':  'filterModeGroup',
                              'distortionBox':  'distortionGroup',
                              'antiAliasBox':   'antiAliasGroup',
                              'envSustainBox':  'envSustainGroup',
                              'pwmSweepBox':    'pwmSweepGroup',
                              'oscAWaveBox':    'oscAWaveGroup'}

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.windowHandler = MainWindowHandler(self.dialDict, self.buttonDict)
        self.settings = QtCore.QSettings('MeeblipControl', 'MeeblipControl')
        #connect signals and slots
        for dial, cc, in self.dialDict.iteritems():
            currentDial = getattr(self.ui, dial)
            currentDial.setRange(0,127)
            dialChanged = partial(self.windowHandler.dialChanged, mainWindowInstance=self, cc=cc)
            currentDial.valueChanged.connect(dialChanged)
            currentDial.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            currentDial.customContextMenuRequested.connect(partial(self.windowHandler.contextMenu, mainWindowInstance=self, widgetName=dial))
        for button, buttonList in self.buttonDict.iteritems():
            currentButton = getattr(self.ui, button)
            buttonFunc = partial(self.windowHandler.buttonChanged, mainWindowInstance=self, value=buttonList[1], cc=buttonList[0], button=currentButton)
            currentButton.toggled.connect(buttonFunc)
        for buttonGroupBox in self.buttonBoxDict.keys():
            currentGroup = getattr(self.ui, buttonGroupBox)
            currentGroup.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            currentGroup.customContextMenuRequested.connect(partial(self.windowHandler.contextMenu, mainWindowInstance=self,
                                                                    widgetName=buttonGroupBox))

        class _MidiInput(QtCore.QThread):
            dataReceivedSignal = QtCore.pyqtSignal(int, int)
            midiExceptionSignal = QtCore.pyqtSignal(str)

            def __init__(self, mainWindow, mainWindowHandler, parent=None):
                super(_MidiInput, self).__init__(parent)
                self.mainWindow = mainWindow
                self.mainWindowHandler = mainWindowHandler

            def run(self):
                while True:
                    if self.mainWindowHandler.midiSelectedInputDevicesDict:
                        try:
                            self.mainWindowHandler.midiInputMutex.lock()
                            for inputDevice in self.mainWindowHandler.midiSelectedInputDevicesDict.values():
                                        if inputDevice.poll():
                                            data = inputDevice.read(1)
                                            channel = (data[0][0][0] & 0xF) + 1
                                            if channel == self.mainWindowHandler.midiInputChannel:
                                                status = data[0][0][0] & 0xF0
                                                cc = data[0][0][1]
                                                #if a CC message arrives and is mapped
                                                if status == 0xB0 and cc in self.mainWindowHandler.currentPatch.patchMIDIMapDict:
                                                    value = data[0][0][2]
                                                    self.dataReceivedSignal.emit(cc, value)
                                                else:
                                                    if self.mainWindowHandler.midiSelectedOutputDevice:
                                                        self.mainWindowHandler.midiSelectedOutputDevice.write(data)
                        except midi.MidiException as e:
                            self.midiExceptionSignal.emit(unicode(e))
                        finally:
                            self.mainWindowHandler.midiInputMutex.unlock()
                    self.usleep(200) #don't hog the processor in the polling loop!
        #initialize MIDI, start listening for incoming MIDI data
        midi.init()
        self.getMIDIDevices()
        self.midiInputThread = _MidiInput(self, self.windowHandler)
        self.midiInputThread.dataReceivedSignal.connect(self.midiInputCallback)
        self.midiInputThread.midiExceptionSignal.connect(lambda e: QtGui.QMessageBox.warning(self, "MIDI Error", unicode(e)))
        self.midiInputThread.start()
        self.ui.action_Save.setEnabled(False)
        self.restoreSettings(self.windowHandler)
        self.windowHandler.new(self)

    def midiInputCallback(self, cc, value):
        widgetName = self.windowHandler.currentPatch.patchMIDIMapDict[cc]
        if widgetName in self.dialDict:
            getattr(self.ui, widgetName).setValue(value)
            self.windowHandler.dialChanged(value, self, self.dialDict[widgetName])
        elif widgetName in self.buttonBoxDict:
            buttonGroup = getattr(self.ui, self.buttonBoxDict[widgetName])
            checkedButton = buttonGroup.checkedButton()
            checkedButtonName = str(checkedButton.objectName())
            if value >= self.onValue and self.buttonDict[checkedButtonName][1] == self.offValue:
                for button in buttonGroup.buttons():
                    if button != checkedButton:
                        button.toggle()
            elif value < self.onValue and self.buttonDict[checkedButtonName][1] == self.onValue:
                for button in buttonGroup.buttons():
                    if button != checkedButton:
                        button.toggle()

    def getMIDIDevices(self):
        midiOutputDevices = []
        midiInputDevices = []
        for index in xrange(0, midi.get_count()):
            device = midi.get_device_info(index)
            deviceName = device[1]
            if device[3] == 1 and device[4] == 0: #if the device is an output and not opened
                setattr(self, deviceName, QtGui.QAction(QtGui.QIcon(''), deviceName, self))
                deviceWidget = getattr(self, deviceName)
                deviceWidget.setCheckable(True)
                midiOutputDevices.append(deviceWidget)
                self.midiOutputDevicesDict[deviceWidget] = index
            elif device[2] == 1 and device[4] == 0: #if devices is an input and not opened
                deviceName = device[1]
                setattr(self, deviceName, QtGui.QAction(QtGui.QIcon(''), deviceName, self))
                deviceWidget = getattr(self, deviceName)
                deviceWidget.setCheckable(True)
                midiInputDevices.append(deviceWidget)
                self.midiInputDevicesDict[deviceWidget] = index

        if midiOutputDevices:
            self.ui.midiOutputDevicesMenu = self.ui.menubar.addMenu("&Midi Output Device")
            self.ui.midiOutputDevicesMenu.addActions(midiOutputDevices)
        if midiInputDevices:
            self.ui.midiInputDevicesMenu = self.ui.menubar.addMenu("&Midi Input Devices")
            self.ui.midiInputDevicesMenu.addActions(midiInputDevices)

        for device in midiOutputDevices:
            outputFunction = partial(self.windowHandler.midiOutputSelect, mainWindowInstance=self, device=device)
            device.triggered.connect(outputFunction)

        for device in midiInputDevices:
            inputFunction = partial(self.windowHandler.midiInputSelect, mainWindowInstance=self, device=device)
            device.triggered.connect(inputFunction)

    def restoreSettings(self, mainWindowHandler):
        mainWindowHandler.midiInputChannel = self.settings.value('midiInputChannel').toInt()[0]
        if not mainWindowHandler.midiInputChannel:
            self.midiInputChannel = 1
        self.midiOutputChannel = self.settings.value('midiOutputChannel').toInt()[0]
        if not mainWindowHandler.midiOutputChannel:
            mainWindowHandler.midiOutputChannel = 1

        registryInputDeviceList = []
        for inputDeviceHash in self.settings.value('midiInputDevices', []).toList():
            inputDeviceHash = str(inputDeviceHash.toString())
            for deviceWidget, index in self.midiInputDevicesDict.iteritems():
                deviceName = midi.get_device_info(index)[1]
                deviceHash = hashlib.md5(deviceName).hexdigest()
                if deviceHash == inputDeviceHash:
                    deviceWidget.setChecked(True)
                    self.windowHandler.midiInputSelect(self, deviceWidget)
                    registryInputDeviceList.append(deviceHash)
        self.settings.setValue('midiInputDevices', registryInputDeviceList)
        #update the registry so unplugged devices aren't
        #reselected when plugged back in at some later time
        outputDeviceHash = str(self.settings.value('midiOutputDevice').toString())
        registryOutputDevice = None
        for deviceWidget, index in self.midiOutputDevicesDict.iteritems():
                deviceName = midi.get_device_info(index)[1]
                deviceHash = hashlib.md5(deviceName).hexdigest()
                if deviceHash == outputDeviceHash:
                    deviceWidget.setChecked(True)
                    self.windowHandler.midiOutputSelect(self, deviceWidget)
                    registryOutputDevice = deviceHash
        self.settings.setValue('midiOutputDevice', registryOutputDevice)

    @QtCore.pyqtSignature("")
    def on_action_MIDI_Channel_triggered(self):
        self.windowHandler.menuOptions(self)

    @QtCore.pyqtSignature("")
    def on_action_Save_as_triggered(self):
        self.windowHandler.saveAs(self)

    @QtCore.pyqtSignature("")
    def on_action_Load_triggered(self):
        self.windowHandler.load(self)

    @QtCore.pyqtSignature("")
    def on_action_Save_triggered(self):
        self.windowHandler.save(self)

    @QtCore.pyqtSignature("")
    def on_action_New_triggered(self):
        self.windowHandler.new(self)

    @QtCore.pyqtSignature("")
    def on_action_Export_patch_as_MIDI_triggered(self):
        self.windowHandler.midiExport(self)

    @QtCore.pyqtSignature("")
    def on_action_Import_MIDI_patch_triggered(self):
        self.windowHandler.midiImport(self)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myapp = MainWindow()
    myapp.show()
    sys.exit(app.exec_())