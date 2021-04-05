# -*- coding: utf-8 -*-
"""Slight extension of standard wave-module.Wave_read
"""

import wave
import struct
import math
import numpy as np


##
# The class extending standard Python wave.Wave_read class.<br><br>
#
# It provides aditional methods:
# <ul>
# <li> the intensity and intensity per sample computing (both between samples and times)
# <li> the energy and energy per sample computing (both between samples and times)
# <li> the index-like access to samples (e.g. wav[1] or wav[1:10])
# <li> the length operator (len(wav))
# </ul>
#
class WavRead(wave.Wave_read):

    ##
    # Constructor.
    #
    # @param filename the name of file from which the wav is read (string)
    # @param self
    #
    def __init__(self, filename):
        try:
            wave.Wave_read.__init__(self, filename)
            self.__fname = filename
        except IOError, (errno, strerror):
            raise Exception, 'File "' + filename + '" cannot be read ...'


    ##
    # Computes the intensity between given sample indexes.
    #
    # @param  samp1 the index of sample from which to compute (int)
    # @param  samp2 the index of sample to which to compute (int)
    # @param  self
    # @return the value of intensity
    #
    def count_intensity_samps(self, samp1, samp2):
        intensity = 0
        # Compute the energy
        for sample in self[samp1 : samp2] :
            intensity += abs(sample)
        # Return the energy
        return intensity

    ##
    # Computes the energy between given sample indexes.
    #
    # @param  samp1 the index of sample from which to compute (int)
    # @param  samp2 the index of sample to which to compute (int)
    # @param  self
    # @return the value of energy
    #
    def count_energy_samps(self, samp1, samp2):
        energy = 0
        # Compute the energy
        for sample in self[samp1 : samp2] :
            energy += (sample * sample)
        # Return the energy
        return energy

    ##
    # Computes the intensity per sample between given sample indexes.
    #
    # @param  samp1 the index of sample from which to compute (int)
    # @param  samp2 the index of sample to which to compute (int)
    # @param  self
    # @return the value of intensity per sample
    #
    def count_intensityps_samps(self, samp1, samp2):
        return (self.count_intensity_samps(samp1, samp2) / (samp2 - samp1)) if samp2 > samp1 else 0

    ##
    # Computes the energy per sample between given sample indexes.
    #
    # @param  samp1 the index of sample from which to compute (int)
    # @param  samp2 the index of sample to which to compute (int)
    # @param  self
    # @return the value of energy per sample
    #
    def count_energyps_samps(self, samp1, samp2):
        return (self.count_energy_samps(samp1, samp2) / (samp2 - samp1)) if samp2 > samp1 else 0

    ##
    # Computes the intensity between given time instants.
    #
    # @param  time1 the time from which to compute (float)
    # @param  time2 the time to which to compute (float)
    # @param  self
    # @return the value of intensity
    #
    def count_intensity_times(self, time1, time2):
        return self.count_intensity_samps(int(self.getframerate() * time1), int(self.getframerate() * time2))

    ##
    # Computes the intensity per sample between given time instants.
    #
    # @param  time1 the time from which to compute (float)
    # @param  time2 the time to which to compute (float)
    # @param  self
    # @return the value of intensity per samples
    #
    def count_intensityps_times(self, time1, time2):
        return self.count_intensityps_samps(int(self.getframerate() * time1), int(self.getframerate() * time2))

    ##
    # Computes the energy between given time instants.
    #
    # @param  time1 the time from which to compute (float)
    # @param  time2 the time to which to compute (float)
    # @param  self
    # @return the value of intensity
    #
    def count_energy_times(self, time1, time2):
        return self.count_energy_samps(int(self.getframerate() * time1), int(self.getframerate() * time2))

    ##
    # Computes the energy per sample between given time instants.
    #
    # @param  time1 the time from which to compute (float)
    # @param  time2 the time to which to compute (float)
    # @param  self
    # @return the value of intensity per samples
    #
    def count_energyps_times(self, time1, time2):
        return self.count_energyps_samps(int(self.getframerate() * time1), int(self.getframerate() * time2))

    ##
    # Computes the root mean square (RMS) energy between given sample indeces.
    #
    # @param  samp1 the index of sample from which to compute (int)
    # @param  samp2 the index of sample to which to compute (int)
    # @return the value of RMS energy (float)
    #
    def count_energyrms_samps(self, samp1, samp2):
        return math.sqrt(self.count_energy_samps(samp1, samp2)/float(samp2-samp1))

    ##
    # Computes the root mean square (RMS) energy between given time instants.
    #
    # @param  time1 the time from which to compute (float)
    # @param  time2 the time to which to compute (float)
    # @return the value of RMS energy (float)
    #
    def count_energyrms_times(self, time1, time2):
        return self.count_energyrms_samps(int(self.getframerate() * time1), int(self.getframerate() * time2))

    ##
    # Returns list of indeces of elements after which a zero crossing occurs between given start and end positions.
    #
    # @param  beg position from which to compute (int denotes sample index, float denotes time)
    # @param  end position to which to compute (int denotes sample index, float denotes time)
    # @return list of indeces of elements after which a zero crossing occurs between given start and end positions
    #
    def zerocross(self, beg, end):
        # Express positions in samples
        if isinstance(beg, float):
            beg = int(self.getframerate() * beg)
        if isinstance(end, float):
            end = int(self.getframerate() * end)

        # Make signum in the input segment
        seg = np.sign(self[beg:end])
        # Replace zeros with -1 to correctly interpret zeros in the input segment
        seg[seg==0] = -1

        # Return list of indeces of elements after which a zero crossing occurs
        return list(np.where(np.diff(seg))[0])

    ##
    # Computes zero crossing rate between the given positions.
    #
    # @param  beg position from which to compute (int denotes sample index, float denotes time)
    # @param  end position to which to compute (int denotes sample index, float denotes time)
    # @param  pertime time (in sec) to express the rate: 0 means the length of the input segment; -1 means 'per sample'
    # @return the value of zero crossing rate
    #
    def count_zerocrossrate(self, beg, end, pertime=0):
        # Total number of zerocrossings
        n = len(self.zerocross(beg, end))
        if pertime == 0:        # (absolute) ZCR in the input segment
            rate = n
        else:
            # Express positions in samples
            if isinstance(beg, float):
                beg = int(self.getframerate() * beg)
            if isinstance(end, float):
                end = int(self.getframerate() * end)

            if pertime == -1:     # ZCR per sample
                rate = n / float(end - beg)
            else:                 # ZCR per the given time interval
                rate = n / float(end - beg) * (self.getframerate()*pertime)
        return rate

    ##
    # The method enabling index-like access into the array of samples (as int).
    # Note, that the method can be slow due to decoding of samples from the internal format
    # of the parent class.
    #
    # @param  index the index of the required sample, or the array of samples (int, int:int)
    # @param  self
    # @return the value of the sample, or array of samples (int)
    #
    def __getitem__(self, index):
        # If the index is number (integer expected), one sample is required
        if isinstance(index, int) :
           beg = index
           num = 1
        # If the index is slice, array of samples is required
        elif isinstance(index, slice) :
           beg = index.start
           num = index.stop - beg
           # If the num is larger than number of samples, adjust it ...
           if beg + num > self.getnframes() :
              num = self.getnframes() - beg
        # Otherwise error
        else :
           raise RuntimeError, "Invalid index value: %s" % str(index)

        # Read the sample(s) from the required position
        self.setpos(beg)
        frames = self.readframes(num)
        # Set the sample(s)
        samps  = struct.unpack(str(num) + 'h', frames)

        # Return the samples
        if   num >  1 : return samps
        elif num == 1 : return samps[0]
        else          : return []

    ##
    # The method getting the number of samples in the class
    #
    # @param self
    #
    def __len__(self):
        return int(self.getnframes())

    ##
    # The method printing user-readable information about the wav object
    #
    def __repr__(self):
        return "[Wave file. %d samples, %d sample freq., read form: %s]" % (self.getnframes(), self.getframerate(), self.__fname)

# ----------


##
# The class extending standard Python wave.Wave_write class.<br><br>
#
# It provides aditional methods:
# <ul>
# <li> write wav from the list (or tuple) of int values
# </ul>
#
class WavWrite(wave.Wave_write):

    ##
    # Constructor.
    #
    # @param filename the name of file to which the wav will be written (string)
    # @param self
    #
    def __init__(self, filename):
        try:
            wave.Wave_write.__init__(self, filename)
            self.setsampwidth(struct.calcsize('h'))
        except IOError, (errno, strerror):
            raise Exception, 'File "' + filename + '" cannot be created'

    ##
    # Constructor.
    #
    # @param filename the name of file to which the wav will be written (string)
    # @param sampfreq the sampling frequency (int)
    # @param numchans the number of channels (int, default is 1)
    # @param self
    #
    def __init__(self, filename, sampfreq, numchans = 1):
        try:
            wave.Wave_write.__init__(self, filename)
            wave.Wave_write.setsampwidth(self, struct.calcsize('h'))
            wave.Wave_write.setframerate(self, sampfreq)
            wave.Wave_write.setnchannels(self, numchans)
        except IOError, (errno, strerror):
            raise Exception, 'File "' + filename + '" cannot be created'

    ##
    # Write the samles to the file. Use methods from wave.Wave_write to set the number of
    # cannels, sample frequency etc.
    #
    # @param samps the array (pythons list or typle) of int values containing samples
    # @param self
    #
    def writesamples(self, samps):
        # Convert the samples to buffer
        buf = ''
        for s in samps:
            buf += struct.pack('h', s)
        # Write the buffer to file as wav
        wave.Wave_write.writeframes(self, buf)


    ##
    # Override the method wave.Wave_write.setsampwidth to disable the change of sample width.
    # It is set by default to 'short'.
    #
    # This implementation throws the exception.
    #
    # @param self
    # @param samps not used
    #
    def setsampwidth(self, samps) :
        raise Exception, 'The change of sample width disabled. Set to "short" by default'

# ----------

##
# Shortcut method which writes the array of samples to the file specified.
#
# @param filename  the name of file to write to (string)
# @param samps     the array of samples to write (list or tuple)
# @param sampfreq  the sampling frequency (int)
# @param numchans  the number of channels (int)
# @param self
#
def WriteWav(filename, samps, sampfreq, numchans) :
    w = WavWrite(filename, sampfreq, numchans)
    w.writesamples(samps)
    w.close()

# ----------




##
# The old class replaced by WavRead class. Use the new class instead!
# @obsolete
#
class WavExt(WavRead) :
    ##
    def count_intps(self, time1, time2):
        return self.count_intensityps_times(time1, time2)



