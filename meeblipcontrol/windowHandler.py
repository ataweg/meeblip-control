'''
Created on Mar 20, 2012

@author: bitrex@earthlink.net
'''
from PyQt4 import QtGui, QtCore
from optionsDialog import optionsDialog
from pygame import midi
from meeblipPatch import meeblipPatch
import pickle
from functools import partial
import midi as midiwrite
import hashlib

class MainWindowHandler(object):
    '''
    Handles main window actions.
    '''
    def __init__(self, dialDict, buttonDict):
        '''
        Constructor
        '''
        self.dialDict = dialDict
        self.buttonDict = buttonDict
        self.midiSelectedInputDevicesDict = {}
        self.midiSelectedOutputDevice = None
        self.midiOutputChannel = None
        self.midiInputChannel = None
        self.currentPatch = meeblipPatch()
        self.currentFile = None
        self.midiInputMutex = QtCore.QMutex()

    def dialChanged(self, value, mainWindowInstance=None, cc=None):
        self.currentPatch.patchCCDict[cc] = value
        if self.midiSelectedOutputDevice != None:
            try:
                self.midiSelectedOutputDevice.write_short(0xB0 | self.midiOutputChannel - 1, cc, value)
            except midi.MidiException as e:
                QtGui.QMessageBox.warning(mainWindowInstance, "MIDI Error", unicode(e))

        mainWindowInstance.ui.action_Save.setEnabled(True)
        mainWindowInstance.ui.action_New.setEnabled(True)

    def buttonChanged(self, mainWindowInstance, value, cc, button):
        self.currentPatch.patchCCDict[cc] = value
        if self.midiSelectedOutputDevice != None and button.isChecked():
            try:
                self.midiSelectedOutputDevice.write_short(0xB0 | self.midiOutputChannel - 1, cc, value)
            except midi.MidiException as e:
                QtGui.QMessageBox.warning(mainWindowInstance, "MIDI Error", unicode(e))

        mainWindowInstance.ui.action_Save.setEnabled(True)
        mainWindowInstance.ui.action_New.setEnabled(True)

    def menuOptions(self, mainWindowInstance):
        dialog = optionsDialog(self.midiInputChannel, self.midiOutputChannel)
        if dialog.exec_():
            self.midiInputChannel = dialog.midiInputChannel
            self.midiOutputChannel = dialog.midiOutputChannel
            mainWindowInstance.settings.setValue('midiOutputChannel', dialog.midiOutputChannel)
            mainWindowInstance.settings.setValue('midiInputChannel', dialog.midiInputChannel)

    def midiInputSelect(self, mainWindowInstance, device):
        deviceIndex = mainWindowInstance.midiInputDevicesDict[device]
        if not device.isChecked():
            try:
                self.midiSelectedInputDevicesDict.pop(deviceIndex).close()
                device.setChecked(False)
            except midi.MidiException as e:
                QtGui.QMessageBox.warning(mainWindowInstance, "MIDI Error", unicode(e))
            except:
                QtGui.QMessageBox.warning(mainWindowInstance, "MIDI Error", "Device error.")
                mainWindowInstance.midiInputDevicesDict.pop(device)
                mainWindowInstance.ui.midiInputDevicesMenu.removeAction(device)
        else:
            try:
                self.midiSelectedInputDevicesDict[deviceIndex] = midi.Input(deviceIndex)
            except midi.MidiException as e:
                QtGui.QMessageBox.warning(mainWindowInstance, "MIDI Error", unicode(e))
            except:
                QtGui.QMessageBox.warning(mainWindowInstance, "MIDI Error", "Device error.")
                mainWindowInstance.midiInputDevicesDict.pop(device)
                mainWindowInstance.ui.midiInputDevicesMenu.removeAction(device)


        deviceNameList = []
        for deviceIndex in self.midiSelectedInputDevicesDict.keys():
            deviceNameList.append(hashlib.md5(midi.get_device_info(deviceIndex)[1]).hexdigest())
        mainWindowInstance.settings.setValue('midiInputDevices', deviceNameList)

    def midiOutputSelect(self, mainWindowInstance, device):
        deviceIndex = mainWindowInstance.midiOutputDevicesDict[device]

        for outputDevice in mainWindowInstance.midiOutputDevicesDict.keys():
            if outputDevice != device:
                outputDevice.setChecked(False)
            else:
                if outputDevice.isChecked():
                            try:
                                self.midiSelectedOutputDevice = midi.Output(deviceIndex)
                                if not self.midiSelectedOutputDevice:
                                    raise Exception
                                mainWindowInstance.settings.setValue('midiOutputDevice', hashlib.md5(midi.get_device_info(deviceIndex)[1]).hexdigest())
                            except midi.MidiException as e:
                                QtGui.QMessageBox.warning(mainWindowInstance, "MIDI Error", unicode(e))
                            except:
                                QtGui.QMessageBox.warning(mainWindowInstance, "MIDI Error", "Device error.")
                                mainWindowInstance.midiOutputDevicesDict.pop(device)
                                mainWindowInstance.ui.midiOutputDevicesMenu.removeAction(device)
                else:
                    try:
                        self.midiSelectedOutputDevice.close()
                    except midi.MidiException as e:
                        QtGui.QMessageBox.warning(mainWindowInstance, "MIDI Error", unicode(e))
                    except:
                        QtGui.QMessageBox.warning(mainWindowInstance, "MIDI Error", "Device error.")
                        mainWindowInstance.midiOutputDevicesDict.pop(device)
                        mainWindowInstance.ui.midiOutputDevicesMenu.removeAction(device)

                    self.midiSelectedOutputDevice = None
                    mainWindowInstance.settings.setValue('midiOutputDevice', '')

    def contextMenu(self, position, mainWindowInstance=None, widgetName=None):
        contextMenu = QtGui.QMenu()
        clearAction = None
        learnAction = contextMenu.addAction('MIDI Learn')
        if widgetName in self.currentPatch.patchMIDIMapDict.values():
            clearAction = contextMenu.addAction('MIDI Clear')
        action = contextMenu.exec_(getattr(mainWindowInstance.ui, widgetName).mapToGlobal(position))
        if action == learnAction:
            self.midiLearn(mainWindowInstance, widgetName)
        if action == clearAction:
            wigetCCs = [k for k, v in self.currentPatch.patchMIDIMapDict.iteritems() if v==widgetName]
            for cc in wigetCCs:
                self.currentPatch.patchMIDIMapDict[cc] = None
            mainWindowInstance.ui.action_Save.setEnabled(True)

    def midiLearn(self, mainWindowInstance, widgetName):


        class _midiLearnWait(QtCore.QThread):

            dataReceived = QtCore.pyqtSignal(int)
            midiException = QtCore.pyqtSignal(str)

            def __init__(self, midiInputDevicesDict, midiInputChannel, midiInputMutex, parent=None):
                super(_midiLearnWait, self).__init__(parent)
                self.midiSelectedInputDevicesDict = midiInputDevicesDict
                self.midiInputChannel = midiInputChannel
                self.midiInputMutex = midiInputMutex
                self.threadAlive = True

            def run(self):
                self.midiInputMutex.lock()
                while self.threadAlive:
                    try:
                        for inputDevice in self.midiSelectedInputDevicesDict.values():
                            if inputDevice.poll():
                                data = inputDevice.read(1)
                                channel = (data[0][0][0] & 0xF) + 1
                                if channel == self.midiInputChannel:
                                    if data[0][0][0] & 0xF0 == 0xB0:  #if a CC message arrives
                                        cc = data[0][0][1]
                                        self.dataReceived.emit(cc)
                                        self.threadAlive = False
                                        break
                    except midi.MidiException as e:
                            self.midiException.emit(unicode(e))
                            break
                self.midiInputMutex.unlock()
                self.msleep(10) #don't hog the processor in the polling loop!

        def _dataReceivedCallback(cc, message=None):
            message.accept()
            self.currentPatch.patchMIDIMapDict[cc] = widgetName
            mainWindowInstance.ui.action_Save.setEnabled(True)

        if self.midiSelectedInputDevicesDict:
            midiLearnMessage = QtGui.QMessageBox(1, "MIDI Learn", "Please move a controller.",
                                                             QtGui.QMessageBox.Cancel)
            midiLearnThread = _midiLearnWait(self.midiSelectedInputDevicesDict, self.midiInputChannel, self.midiInputMutex)
            midiLearnThread.dataReceived.connect(partial(_dataReceivedCallback, message=midiLearnMessage))
            midiLearnThread.midiException.connect(lambda e: QtGui.QMessageBox.warning(mainWindowInstance,
                                                                  "MIDI Error", e))
            midiLearnThread.start()
            reply = midiLearnMessage.exec_()
            if reply == QtGui.QMessageBox.Cancel:
                midiLearnThread.threadAlive = False
                while not midiLearnThread.isFinished():
                    pass
        else:
            QtGui.QMessageBox.warning(mainWindowInstance, "MIDI Error", "No MIDI inputs selected.")

    def saveAs(self, mainWindowInstance, filename=None):
        if not filename:
            filename = QtGui.QFileDialog.getSaveFileName(filter="*.mee")
            self.currentFile = filename
            self.currentPatch.name = filename.split("/")[-1].split(".")[0]
        if filename:
            try:
                with open(filename, "wb") as f:
                    try:
                        pickle.dump(self.currentPatch, f)
                        mainWindowInstance.ui.action_Save.setEnabled(False)
                        mainWindowInstance.ui.action_New.setEnabled(True)
                        mainWindowInstance.setWindowTitle(self.currentPatch.name)
                    except IOError as (errno, strerror):
                        QtGui.QMessageBox.warning(mainWindowInstance, "File write error: %s" % errno,
                                          "Error writing file %s:\n %s" % (unicode(filename), unicode(strerror)))
                    except:
                        QtGui.QMessageBox.warning(mainWindowInstance, "File write error", "Unknown error writing to file.")

            except IOError as (errno, strerror):
                QtGui.QMessageBox.warning(mainWindowInstance, "File save error: %s" % errno,
                                          "Error saving file %s:\n %s" % (unicode(filename), unicode(unicode(strerror))))
            except:
                QtGui.QMessageBox.warning(mainWindowInstance, "File save error", "Unknown error saving file %s." % unicode(filename))

    def save(self, mainWindowInstance):
        if not self.currentFile:
            self.saveAs(mainWindowInstance)
        else:
            self.saveAs(mainWindowInstance, filename=self.currentFile)

    def load(self, mainWindowInstance):
        filename = QtGui.QFileDialog.getOpenFileName(filter="*.mee")
        try:
            if filename:
                with open(filename, "rb") as f:
                    try:
                        self.currentPatch = pickle.load(f)
                        self.restorePatchSettings(mainWindowInstance, self.currentPatch)
                        self.currentFile = filename
                    except IOError as (errno, strerror):
                        QtGui.QMessageBox.warning(mainWindowInstance, "File read error: %s" % errno,
                                      "Error reading from file %s:\n %s" % (unicode(filename), (unicode(strerror))))
                    except:
                        QtGui.QMessageBox.warning(mainWindowInstance, "File read error", "Unknown error reading from file %s." % unicode(filename))

        except IOError as (errno, strerror):
            QtGui.QMessageBox.warning(mainWindowInstance, "File open error: %s" % errno,
                                      "Error opening file %s:\n %s" % (unicode(filename), unicode(strerror)))
        except:
            QtGui.QMessageBox.warning(mainWindowInstance, "File open error", "Unknown error opening file %s." % unicode(filename))

    def new(self, mainWindowInstance):
        if mainWindowInstance.ui.action_Save.isEnabled():
            reply = QtGui.QMessageBox.question(mainWindowInstance, "Create new patch", "Current patch is not saved.  Do you wish to continue?",
                                               QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.No:
                return
        for dial in self.dialDict:
            dialWidget = getattr(mainWindowInstance.ui, dial)
            dialWidget.setValue(0)
        for button, value in self.buttonDict.iteritems():
            if value[1] == mainWindowInstance.offValue:
                buttonWidget = getattr(mainWindowInstance.ui, button)
                buttonWidget.setChecked(True)

        self.currentFile = None
        self.currentPatch = meeblipPatch()
        mainWindowInstance.ui.action_Save.setEnabled(False)
        mainWindowInstance.setWindowTitle("New Patch")
        mainWindowInstance.ui.action_New.setEnabled(False)

    def restorePatchSettings(self, mainWindowInstance, meeblipPatch):
        for cc, value in meeblipPatch.patchCCDict.iteritems():
#           if cc in range(48, 56) + range(58, 62):
            if cc in range(14, 30) + range(48, 56) + range(58, 62):
                dialWidget = getattr(mainWindowInstance.ui, [k for k, v in self.dialDict.iteritems() if v == cc][0])
                dialWidget.setValue(value)
                self.dialChanged(value, mainWindowInstance, cc)
#           elif cc in xrange(65, 80):
            elif cc in xrange(65, 96):
                onButtonWidget = getattr(mainWindowInstance.ui, [k for k, v in self.buttonDict.iteritems() if v[0] == cc and
                                                                v[1] == mainWindowInstance.onValue][0])
                offButtonWidget = getattr(mainWindowInstance.ui, [k for k, v in self.buttonDict.iteritems() if v[0] == cc and
                                                                v[1] == mainWindowInstance.offValue][0])
                if value < mainWindowInstance.onValue and onButtonWidget.isChecked():
                    offButtonWidget.toggle()
                elif value >= mainWindowInstance.onValue and offButtonWidget.isChecked():
                    onButtonWidget.toggle()

        mainWindowInstance.setWindowTitle(self.currentPatch.name)
        mainWindowInstance.ui.action_Save.setEnabled(False)
        mainWindowInstance.ui.action_New.setEnabled(True)

    def midiExport(self, mainWindowInstance):
        filename = QtGui.QFileDialog.getSaveFileName(filter="*.mid")
        try:
            if filename:
                with open(filename, "wb") as f:
                        try:
                            outputPattern = midiwrite.Pattern()
                            outputTrack = midiwrite.Track()
                            eventList = []
                            trackName = "MeeBlip Patch"
                            trackNameEvent = midiwrite.TrackNameEvent(name=trackName)
                            eventList.append(trackNameEvent)

#                           for index in (k for k in xrange(48, 80) if k not in range(56, 58) + range(62, 65)):
                            for index in (k for k in xrange(14, 96) if k not in range(30, 48) + range(56, 58) + range(62, 65)):
                                ccEvent = midiwrite.ControlChangeEvent(channel=1)
                                ccEvent.set_control(index)
                                ccEvent.set_value(self.currentPatch.patchCCDict[index])
                                eventList.append(ccEvent)
                            for event in eventList:
                                outputTrack.append(event)
                            outputPattern.append(outputTrack)

                            midiwrite.write_midifile(f, outputPattern)

                        except IOError as (errno, strerror):
                            QtGui.QMessageBox.warning(mainWindowInstance, "File write error: %s" % errno,
                                              "Error writing file %s:\n %s" % (unicode(filename), unicode(strerror)))
                        except:
                            QtGui.QMessageBox.warning(mainWindowInstance, "File write error", "Unknown error writing to file.")

        except IOError as (errno, strerror):
            QtGui.QMessageBox.warning(mainWindowInstance, "File save error: %s" % errno,
                                      "Error saving file %s:\n %s" % (unicode(filename), unicode(unicode(strerror))))
        except:
            QtGui.QMessageBox.warning(mainWindowInstance, "File save error", "Unknown error saving file %s." % unicode(filename))

    def midiImport(self, mainWindowInstance):
        if mainWindowInstance.ui.action_Save.isEnabled():
            reply = QtGui.QMessageBox.question(mainWindowInstance, "Import MIDI patch", "Current patch is not saved.  Do you wish to continue?",
                                           QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.No:
                return

        filename = QtGui.QFileDialog.getOpenFileName(filter="*.mid")
        try:
            if filename:
                with open(filename, "rb") as f:
                    try:
                        pattern = midiwrite.read_midifile(f)
                        midiImportPatch = meeblipPatch()
#                       ccList = [k for k in xrange(48, 80) if k not in range(56, 58) + range(62, 65)]
                        ccList = [k for k in xrange(14, 96) if k not in range(30, 48) + range(56, 58) + range(62, 65)]
                        for event in pattern[0]:
                            if isinstance(event, midiwrite.ControlChangeEvent):
                                cc = event.get_control()
                                if cc in ccList:
                                    midiImportPatch.patchCCDict[cc] = event.get_value()
                                    ccList.remove(cc)
                        if not ccList:
                            self.currentPatch = midiImportPatch
                            self.currentPatch.name = filename.split("/")[-1].split(".")[0]
                            self.restorePatchSettings(mainWindowInstance, self.currentPatch)
                        else:
                            raise Warning, "Patch data not found."

                    except IOError as (errno, strerror):
                        QtGui.QMessageBox.warning(mainWindowInstance, "File read error: %s" % errno,
                                      "Error reading from file %s:\n %s" % (unicode(filename), (unicode(strerror))))
                    except (TypeError, Warning) as e:
                        QtGui.QMessageBox.warning(mainWindowInstance, "File read error",
                                      "Error parsing MIDI data from file %s:\n %s" % (unicode(filename), (unicode(e))))
                    except:
                        QtGui.QMessageBox.warning(mainWindowInstance, "File read error", "Unknown error reading from file %s." % unicode(filename))

        except IOError as (errno, strerror):
            QtGui.QMessageBox.warning(mainWindowInstance, "File open error: %s" % errno,
                                      "Error opening file %s:\n %s" % (unicode(filename), unicode(strerror)))
        except:
            QtGui.QMessageBox.warning(mainWindowInstance, "File open error", "Unknown error opening file %s." % unicode(filename))
