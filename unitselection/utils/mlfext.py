# -*- coding: utf-8 -*-
# Extended MLF support - adds f0 and intensity per sample parameters

import struct, sys, os.path, bisect      # standard modules

sys.path.append('../math_package')
sys.path.append('../dsp_package')

import mlf, pm, wavext  # user modules

## Class for calculating f0 frequency and intensity per sample for segments in MLF structure.
class MlfExt(mlf.Mlf):
    ''' Names of additional keys in MLF structure:

    attr_f0     -- f0 frequency
    attr_intps  -- intensity per sample
    '''
    
    attr_f0         = 'F0'
    attr_intps      = 'INTPS'

    ## Constructor
    #
    # @param fname is name of MLF file that is to be loaded
    def __init__(self, fname=None, from_htk_dir=None, from_esps_dir=None, unsureBound='?', ext=None, encoding='utf8'):
        mlf.Mlf.__init__(self, fname, from_htk_dir, from_esps_dir, unsureBound, ext, encoding)
        self.__ext_pm  = 'pm'
        self.__ext_wav = 'wav'
        

    ## Extends (calculate) standard mlf structure with f0 and intensity per sample.
    #  @param pm_dir is the name of directory that contains pitch-mark files
    #  @param wav_dir is the name of directory that contains wav files
    #  @param shift_type defines whether (and how) the unit boundaries will be shifted onto pitch-marks
    def count_params(self, pm_dir, wav_dir, shift_type = pm.Pm.shift_nearest):
        self._count_f0(pm_dir, shift_type)  # f0 must be counted first because of time boundary correction
        self._count_intps(wav_dir)


    # counts an extends data structure with f0
    def _count_f0(self, pm_dir, shift_type = pm.Pm.shift_nearest):
        
        utts = self.getutts()
        for sentname in sorted(utts.keys()):  # through all utterances

            filename = os.path.join(pm_dir, sentname + '.' + self.__ext_pm)
            print "\rf0: " + filename,
            pm_buffer = pm.Pm(filename,shift_type)

            for seg in utts[sentname]:        # through all words in utterance
                f0_obj = pm_buffer.get_segment(pm.Pm.idx_continue, float(seg[MlfExt.attr_endTime]))
                seg[MlfExt.attr_f0] = str(f0_obj.get_f0())
                if shift_type != pm.Pm.shift_none:
                    seg[MlfExt.attr_begTime] = str(f0_obj.get_time1())
                    seg[MlfExt.attr_endTime] = str(f0_obj.get_time2())


    # counts an extends data structure with intensity per sample
    def _count_intps(self, wav_dir):

        utts = self.getutts()        
        for sentname in sorted(utts.keys()):  # through all utterances

            filename = os.path.join(wav_dir, sentname + '.' + self.__ext_wav)
            print "\rintps: " + filename,

            wave_buffer = wavext.WavExt(filename)
            if wave_buffer.getnchannels() != 1 or wave_buffer.getsampwidth() != 2:
                print 'Unsupported waveformat'

            for seg in utts[sentname]:        # through all units in utterance
                intps = wave_buffer.count_intps(float(seg[MlfExt.attr_begTime]), float(seg[MlfExt.attr_endTime]))
                seg[MlfExt.attr_intps] = str(intps)

            wave_buffer.close()

    ## Sets extension for pitch-mark file
    #  @param extension defines the extension of pitch-mark files
    def set_pm_extension(self, extension):
        self.__ext_pm = extension

    ## Sets extensions for wave file
    #  @param extension defines the extension of wav files
    def set_wav_extension(self, extension):
        self.__ext_wav = extension

    ## Shift segment boundary times to their corresponding positions (eg pitch-marks).
    #  The MLF file is assumed to have been created in a standard HTK way, i.e. boundaries were placed as multiples of a constant framerate.
    #  "Position" files (files containing real positions of each frame in the file) must be available; position of each boundary frame is then shifted to the corresponding position.
    #  @param dir Directory with files, each of them contains positions of each frame.
    #  @param framerate Framerate of the original MLF.
    #  @param fext Extension of the files with positions.
    #  @param self
    #  @note Could be used to shift the boundaries with respect to pitch-synchronous parameterisation scheme.
    def bound2pos(self, dir, framerate=0.010, fext="pos"):
        for uname in self.utt_names():
            # read frame positions
            pos = [line.split()[0] for line in open(os.path.join(dir, uname+"."+fext))]
            # go through all boundaries in MLF and shift them to their corresponding positions
            for seg in self[uname]:
                frm_beg = int(round(seg[self.attr_begTime]/framerate))
                if frm_beg == 0:    # the very first segment in utterance
                    seg[self.attr_begTime] = 0
                else:
                    seg[self.attr_begTime] = pos[frm_beg-1]
                frm_end = int(round(seg[self.attr_endTime]/framerate)) - 1
                seg[self.attr_endTime] = pos[frm_end]


    ## Shift segment boundaries to constant-shift pitch-asynchronous frames.
    #  The MLF file is assumed to be synchronised with some prominent time instants (e.g. pitch-marks).
    #  "Frame description" files (files containing beginnings and lengths of each frame in the file) must be available; position of each boundary frame is then shifted in a constant pitch-asynchronous way compatible with HTK.
    #  @param dir Directory with files, each of them contains beginnings and lengths of each frame (each line has the format: beg len).
    #  @param framerate Framerate of the HTK MLF.
    #  @param fext Extension of the files with frame descriptions.
    #  @param self
    #  @note Could be used to shift the pitch-synchronous boundaries with respect to pitch-asynchronous HTK parameterisation scheme.
    def topabound(self, dir, framerate=0.010, fext="frm"):
        for uname in self.utt_names():
            # read frame positions
            frm = [float(line.split()[0]) for line in open(os.path.join(dir, uname+"."+fext))]
            end_time = 0

            # go through all boundaries in MLF and shift them to their corresponding positions
            for seg in self[uname]:
                if seg[self.attr_begTime] > 0:  # beginning of the 1st segment is unchanged
                    seg[self.attr_begTime] = end_time    # set the beginning time according to the end time of the previous segment
                # prepocte pitch-synchronni pozici na pitch-asynchronni pozici (podle HTK)
                idx = bisect.bisect_right(frm, seg[self.attr_endTime])
                if idx == len(frm): # for safety, to avoid error +1
                    idx =- 1
                # find the nearest frame
                if frm[idx]-seg[self.attr_endTime] > seg[self.attr_endTime]-frm[idx-1]:
                    idx -= 1
                end_time = idx*framerate
                seg[self.attr_endTime] = end_time


    ## Shift segment boundaries to pitch-mark positions.
    #  Boundaries are shifted to the nearest pitch-mark positions with respect to the defined tolerances in V-U or U-V regions)
    #  @note Only voiced pitch-marks are considered. In unvoiced speech, no shift is performed. In transitional speech (V-T or T-V regions), boundaries are shifted to the voiced pitch-marks.
    #  @param dir Directory with pitch-mark files, each of them contains pitch-mark times and types in wavesurfer format, i.e. "time time type" (both times must be the same!).
    #  @param vtol Tolerance region for a voiced pitch-mark (in number of pitch-marks). If a boundary in voiced speech is within the vtol from a transitional pitch-mark (in a number of pitch-marks), the boundary is shifted to the first/last voiced pitch-mark.
    #  @param utol Tolerance region for an unvoiced "pitch-mark" (in sec). If a boundary in unvoiced speech is within the utol from a voiced pitch-mark, the boundary is shifted to the first/last voiced pitch-mark.
    #  @param fext Extension of the pitch-mark files.
    #  @param self
    #  @warning The input pitch-mark files must be in wavesurfer format, i.e. "time time type" (both times must be the same!).
    def topitchmark(self, dir, vtol=0, utol=0, fext="pm"):
        for uname in self.utt_names():
            times = []
            types = []
            # read pitch-marks (only voiced and transitional ones)
            for line in open(os.path.join(dir, uname+"."+fext)):
                (time, time, type) = line.split()   # both times are the same, the 1st one is ignored
                if type == 'U':     # ignore unvoiced pitch-marks
                    continue
                times.append(float(time))
                types.append(type)

            end_time = self[uname][0][self.attr_begTime]    # init: beg. time of the first segment
            
            # go through all boundaries in MLF and shift them to the nearest pitch-mark
            for seg in self[uname]:
                
                # set the beginning time according to the end time of the previous segment
                # (beginning of the 1st segment is unchanged)
                seg[self.attr_begTime] = end_time
                
                end_time = seg[self.attr_endTime]    # save the original end time
                
                # find indexes of the corresponding pitch-marks
                idx = bisect.bisect_right(times, seg[self.attr_endTime])
                
                if idx == 0:    # the very first pitch-mark (must be "T-mark")
                    # the U-V region at the beginning of the file
                    # -> boundary is shifted to the 1st "V-mark" if close enough to the V region
                    if utol and times[idx+1]-seg[self.attr_endTime] < utol:
                        end_time = times[1]
                elif idx == len(times): # the very last pitch-mark (must be "T-mark")
                    # the V-U region at the end of the file
                    # -> boundary is shifted to the last "V-mark" if close enough to the V region
                    if utol and seg[self.attr_endTime]-times[-1] < utol:
                        end_time = times[-2]

                # ---------------------------
                # find the nearest pitch-mark
                # ---------------------------
                
                # the case of unvoiced speech
                elif types[idx] == "T" and types[idx-1] == "T":
                    # shift to the nearest "V-mark" if close enough to the V region, otherwise don't change the time
                    if utol:
                        prev_v = times[types.index("V", idx-2)]
                        next_v = times[types.index("V", idx+1)]
                        if seg[self.attr_endTime]-prev_v < utol:
                            end_time = prev_v
                        elif next_v-seg[self.attr_endTime] < utol:
                            end_time = next_v

                # the case of voiced speech
                elif types[idx] == "V" and types[idx-1] == "V":
                    # shift the nearest from two neighbouring "V-marks"
                    if times[idx]-seg[self.attr_endTime] > seg[self.attr_endTime]-times[idx-1]:
                        idx -= 1
                    end_time = times[idx]
                    # shift to the first/last "V-mark" if close enough to the U region
                    if vtol:
                        if "T" in types[idx-vtol:idx]:
                            #end_time = times[types.index("T", idx-vtol, idx)+1]
                            rev_types = list(types[idx-vtol:idx+1])
                            rev_types.reverse()
                            rev_times = list(times[idx-vtol:idx+1])
                            rev_times.reverse()
                            end_time = rev_times[rev_types.index("T")-1]
                        elif "T" in types[idx+1:idx+vtol+1]:
                            end_time = times[types.index("T", idx+1, idx+vtol+1)-1]

                # voiced-to-unvoiced speech => will be shifted to the last V-mark
                elif types[idx] == "T":
                    end_time = times[idx-1]
                
                # in unvoiced-to-voiced speech => will be shifted to the 1st V-mark
                elif types[idx] == "V":
                    end_time = times[idx]

                seg[self.attr_endTime] = end_time


    ##
    #  Return utterance names with specified number of hand-labeled segments/boundaries.
    #
    #  @param n_handlabs Number of hand-labeled segments (0 = no hand labels, any number
    #         = the required number of hand labels, 'all' = all segments are hand-labeled)
    #  @param mode Comparison mode.
    #  @param sort Sort the utterances.
    #  @return List of utterance names.
    #  @see Mlf.utt_names()
    #
    def utt_names_handlabs(self, n_handlabs=0, mode='>', sort=True):

        unames = []
        
        # Go through all utterances in MLF
        for uname in self.utt_names(sort=sort):
            n_hand = 0
            for seg in self.__utts[uname]:
                if self.attr_modelScore in seg and seg[self.attr_modelScore] == self.attr_handLab:
                    n_hand += 1
            
            if handlabs == 'all' and n_hand == len(self.__utts[uname]):
                unames.append(uname)
            elif mode == '>' and n_hand > n_handlabs:
                unames.append(uname)
            elif mode == '=' and n_hand == n_handlabs:
                unames.append(uname)
            elif mode == '<' and n_hand < n_handlabs:
                unames.append(uname)
            
        return unames

    
    ##
    #  Keep only hand-labeled segments in MLF.
    #
    #  @note       Only hand-labeled segments are kept possibly resulting in a "leaky" MLF!
    #
    def keep_handlabs(self):
        
        for uname in self.utt_names():
            
            trash = []
            n_segs = self.model_len(utts=[uname])
            
            prev = None
            for idx, seg in enumerate(self.getutts()[uname]):
                
                # Check hand labeling:
                #   segment beginning is hand labeled if starting an utterance or its left boundary is hand-labeled
                #   segment end is hand labeled if ending an utterance or its right boundary is hand-labeled
                beg = True if idx == 0         else prev[self.attr_modelScore] == self.attr_handLab
                end = True if idx == n_segs-1  else seg[self.attr_modelScore]  == self.attr_handLab
                
                if not (beg and end):   # Mark segment for deletion
                    trash.append(idx)
                
                prev = seg

            # Delete marked segments
            for item in reversed(trash):
                self.del_segment(uname, item)
            
            # Delete all utterances if it does not contain any segment
            if self.model_len(utts=[uname]) == 0:
                del self[uname]


    ##
    #  Change case of words.
    #
    #  @param typ       'lower' or 'upper'
    #
    def change_case_words(self, typ='lower'):
        
        utts = self.getutts()
        
        for utt in utts:
            for seg in utts[utt]:
                if self.attr_word in seg:
                    
                    if typ.lower() in ('lower', 'low', 'l'):
                        seg[self.attr_word] = seg[self.attr_word].lower()
                    elif typ.lower() in ('upper', 'up', 'u'):
                        seg[self.attr_word] = seg[self.attr_word].upper()

