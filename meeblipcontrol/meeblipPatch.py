'''
Created on Mar 29, 2012

@author: bitrex@earthlink.net
'''

class meeblipPatch(object):
    '''
    Class stores meeblip patch information
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.name = None
        self.patchCCDict = {}
        self.patchMIDIMapDict = {}
#       for index in (k for k in xrange(48, 80) if k not in range(56, 58) + range(62, 65)):
        for index in (k for k in xrange(14, 96) if k not in range(30, 48) + range(56, 58) + range(62, 65)):
            self.patchCCDict[index] = 0

    def randomize(self):
        pass