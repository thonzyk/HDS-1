# -*- coding: utf-8 -*-
# Core support for manipulating MLF in python

import re, glob, sys, os, os.path, math, copy, codecs

##  Base Class for exceptions in this module.
class Error(Exception):
    pass

##  Class for exceptions raised for MLF errors.
class MlfError(Error):

    ##
    # Constructor
    # @param msg exception message (string).
    # @param self
    def __init__(self, msg):
        self.msg = msg

    ##
    # Return exception message.
    # @param self
    def __str__(self):
        return repr(self.msg)


## Class for manipulating MLF
class Mlf:

    ##
    # Precompiled regular expression for extracting a sentence label from a MLF-style sentence definition.
    __re_fname = re.compile(r'(\*[/\\])+(\S+)\.(\S+)"', re.UNICODE)
    # __re_fname = re.compile(r'(\*/)+(\S+)\.(\S+)"')

    ##
    # Precompiled regular expression for extracting a phone label from a triphone label.
    __re_ctx   = re.compile(r'-(.+)\+', re.UNICODE)

    ##
    # Accuracy for comparing float variables.
    __epsilon = 0.000001    # accuracy

    # mlf-hash key names

    ##
    # Start of segment key.
    attr_begTime    = 'mlfBegTime'

    ##
    # End of segment key.
    attr_endTime    = 'mlfEndTime'

    ##
    # State name key.
    attr_stateName  = 'stateName'

    ##
    # Model name key.
    attr_modelName  = 'modelName'

    ##
    # Word key.
    attr_word       = 'word'

    ##
    # State score key.
    attr_stateScore = 'stateScore'

    ##
    # Model score key.
    attr_modelScore = 'modelScore'

    ##
    # Attribute of unsure boundary location (mainly for manual segmentation purposes) -- correspond to the end time of a segment
    attr_unsureBound = 'unsureBound'

    ##
    # Attribute of hand-labeled boundary (from manual segmentation and/or automatic segmentation corrections) -- correspond to the end time of a segment
    attr_handLab = '!hand!'

    ##
    # Standard input
    io_stdin = 'stdin'

    ##
    # Standard output
    io_stdout = 'stdout'

    ##
    # MLF header.
    header = '#!MLF!#'


    ##
    # Constructor.
    # @param fname Name of MLF file to read, Mlf.io_stdin to read from standard input, or a file-like object from which to read the data. If 'encoding' is set, the object is passed through the codecs to convert the data to unicode.
    # @param fname is name of MLF file, or Mlf.io_stdin, then MLF is read from standard input. If fname is None, the class is constructed only, but if reading from directories is specified, MLF is read from special LAB files in these directories.
    # @param from_htk_dir Directory with HTK LAB files
    # @param from_esps_dir Directory with ESPS LAB files.
    # @param unsureBound Symbol of an unsure boundary (there is no other possibility of marking unsure boundaries in MLF file format -- the unsure symbol at the beginning of a segment label means that we are not sure about the exact end boundary of the segment.
    # @param ext Extension of utterances in MLF file.
    # @param encoding Input MLF encoding.
    # @see Mlf::io_stdin
    # @note When fname is not specified but from_lab_dir or from_esps_dir is, MLF is read accordingly from the dir specified. If fname is given, MLF is read from the given MLF file. However, if fname is Mlf.io_stdin, then MLF is read from standard input.
    #
    def __init__(self, fname=None, from_htk_dir=None, from_esps_dir=None, unsureBound='?', ext=None, encoding='utf8'):
        self.__fname        = None
        self.__file         = None
        self.__utts         = {}
        self.__format       = None
        self.__format_w     = ''
        self.__uttname      = None          # name of utterance under processing
        self.__uttext       = ext           # extension of utterances
        self.__unsureBound  = unsureBound   # symbol of unsure boundary
        self.__encoding     = encoding      # MLF file encoding

        # read MLF
        if not fname:   # no MLF file was specified
            if from_htk_dir:
                self.read_labs(from_htk_dir)    # read from HTK LAB files
            elif from_esps_dir:
                self.import_esps(from_esps_dir) # read from ESPS LAB files
        # read from MLF file (or standard input)
        else :
            self.read_mlf(fname, encoding=encoding)

    ##
    # Destructor.
    #  @param self
    def __del__(self):
        self.close()

    ##
    # Overloading assignment for reading
    # @param uname Utterance name
    # @return List of segments within the given utterance
    def __getitem__(self, uname):
        return self.__utts[uname]

    ##
    # Overloading assignment for seting an item
    # @param uname Utterance name
    # @param segments list of segments
    #
    def __setitem__(self, uname, segments):
        segs = []
        for items in segments:
            if not self.__format:        # check format if not known
                self.__check_format(items)

            if self.__format.startswith('tt'):       # convert HTK time to sec
                items[0] = self.__htk2sec(items[0])
                items[1] = self.__htk2sec(items[1])

            segs.append(self.__array2hash(items))
        self.__utts[uname] = segs

    ##
    #
    # Overloading length operator for number of utterances in MLF.
    #
    # @return Number of utterances in MLF.
    #
    def __len__(self):
        return self.no_utts()
    
    ##
    #
    # Overloading delete item operator.
    #
    def __delitem__(self, uname):
        del self.__utts[uname]


    def __str__(self):
        return "[Hash of %5d utts, read from: %s]" % (self.no_utts(), self.__fname)

    #
    # User visible methods.
    #

    ##
    # Read MLF.
    # @param fname Name of MLF file to read, Mlf.io_stdin to read from (standard input), or a file-like
    #        object from which to read the data. If 'encoding' is set, the object is passed through the
    #        codecs to convert the data to unicode.
    # @param encoding   Input file encoding
    # @see   Mlf:io_stdin
    #
    def read_mlf(self, fname=io_stdin, encoding=None) :
        if self.__file :
            raise MlfError, 'File ' + self.__fname + ' has not been closed.'

        try:
            if fname == self.io_stdin:    # read from standard input
                self.__file = sys.stdin
                self.__fname = self.io_stdin
            # fname is an object from which to read the data
            elif not isinstance(fname, str):
                if encoding:
                    self.__encoding = encoding
                    self.__file = codecs.getreader(self.__encoding)(fname)
                else :
                    self.__file = fname
                self.__fname = 'Unknown source represented by %s' % str(fname)
            else:   # read from file
                if encoding:
                    self.__encoding = encoding
                self.__fname = fname
                self.__file = file(fname, 'rb')      # read from file

            self.__read_header()
            self.__read_utts()
            self.close()
        except IOError:
            raise MlfError, 'Error while reading file ' + fname

    ##
    # Read segments from HTK lab file.
    # @param mask       Mask for reading HTK lab files.
    # @param encoding   Input file encoding.
    # @note If label files exist in the MLF, the extensions of the inputted label files are changed to the existing extension in MLF.
    # @warning Utterances in the imported HTK label files will override the existing utterances with the same name in the MLF!
    #
    def read_labs(self, mask="./*.lab", encoding=None):
        if self.__file :
            raise MlfError, 'File ' + self.__fname + ' has not been closed.'

        ext = os.path.splitext(mask)[1]   # extract extension
        if not ext:
            raise MlfError, "Extension of utterances not specified in the given mask " + mask

        if not self.__uttext:
            self.change_utt_extension(ext)     # when no extension specified in MLF (the case of empty MLF), set extension to store in MLF for HTK lab files according to input mask

        if encoding:
            self.__encoding = encoding

        try:
            orig_format =  self.__format
            self.__format = None     # init format - the same format is expected for all labs in dir

            for fpath in glob.glob(mask):
                fname = os.path.splitext(os.path.basename(fpath))[0]
                
                with codecs.open(fpath, 'rt', encoding=self.__encoding) as f :
                    self.__utts[fname] = []   # init segments => overwrite the existing ones!

                    for line in f: # through all lines in lab
                        # process segments
                        items = line.split()
                        if not self.__format:        # check format if not known
                            self.__check_format(items)
                            if orig_format and self.__format != orig_format:
                                raise MlfError, "Format of the imported label files differs from the existing one: " + self.__format + " vs. " + orig_format
    
                        if self.__format.startswith('tt'):       # convert HTK time to sec
                            items[0] = self.__htk2sec(items[0])
                            items[1] = self.__htk2sec(items[1])
    
                        self.__utts[fname].append(self.__array2hash(items)) # store segment

        except IOError:
            raise MlfError, 'Error while reading file ' + fpath


    ##
    # Import segments from ESPS lab file.
    # @param mask       Mask for reading ESPS label files.
    # @param encoding   Input file encoding.
    # @note If label files exist in the MLF, the extensions of the inputted label files are changed to the existing extension in MLF.
    # @warning Utterances in the imported ESPS label files will override the existing utterances with the same name in the MLF!
    #
    def import_esps(self, mask="./*.lab", encoding=None):
        if self.__file != None:
            raise MlfError, 'File ' + self.__fname + ' has not been closed.'

        if self.__format and self.__format != 'ttm':
            raise MlfError, 'Cannot import ESPS label files when labels in other format ('+self.__format+') than "ttm" exist!'

        self.__format = 'ttm'   # set format strictly to ttm

        ext = os.path.splitext(mask)[1]   # extract extension
        if not ext:
            raise MlfError, "Extension of utterances not specified in the given mask " + mask

        if not self.__uttext:
            self.change_utt_extension(ext)  # when no extension specified in MLF (the case of empty MLF), set extension to store in MLF for HTK lab files according to input mask

        is_valid_esps = False

        if encoding:
            self.__encoding = encoding

        try:
            for fpath in glob.glob(os.path.join(mask)):
                fn = os.path.splitext(os.path.basename(fpath))[0]
                f = codecs.open(fpath, 'rt', encoding=self.__encoding)

                # looking for header (#)
                for line in f:
                    if line.strip().startswith('#'):
                        is_valid_esps = True
                        break

                if not is_valid_esps:
                    raise MlfError, 'ESPS header missing in: '+fpath

                self.__utts[fn] = []    # overwrite the existing segments!
                beg = 0
                for line in f:
                    items = line.split()
                    if len(items) != 3:
                        raise MlfError, fpath+': 3 values expected at ESPS line, but '+str(len(items))+' given!'
                    if self.__isunsure(items[2]):
                        unsure = True
                        items[2] = items[2].replace(self.__unsureBound, "", 1)
                    else:
                        unsure = False
                    self.__utts[fn].append({self.attr_begTime: beg, self.attr_endTime: items[0], self.attr_modelName: items[2], self.attr_unsureBound: unsure})
                    beg = items[0]
        except IOError:
            raise MlfError, 'Error while reading ESPS file: ', fpath

    ##
    # Write to MLF file.
    # @param fname Name of the output MLF, Mlf.io_stdout if output to stdout is wanted, or
    #        an file-like object to which to write the data. If 'encoding' is set, the object
    #        is passed through the codecs to convert them to the given encoding.
    # @param uttext     Extensions of the utterances stored in MLF.
    # @param encoding   Output file encoding (utf8 when not specified).
    #
    def write_mlf(self, fname=io_stdout, uttext=None, encoding="utf8"):
        if self.__file :
            raise MlfError, 'File ' + self.__fname + ' has not been closed.'

        if not self.__uttext and not uttext:
            raise MlfError, 'Extension of utterance names in MLF not specified!'

        if uttext:
            self.__uttext = uttext

        if fname != self.io_stdout:  # write to file
            self.__file     = codecs.open(fname, 'wt', encoding=encoding)
            self.__fname    = fname
        # fname is an object from which to read the data
        elif not isinstance(fname, str):
            self.__file     = fname if not encoding else codecs.getwriter(encoding)(fname)
            self.__fname    = 'Unknown destination represented by %s' % str(fname)
        else:   # write to standard output
            self.__file     = sys.stdout
            self.__fname    = self.io_stdout

        self.__write_header()
        self.__write_utts()
        self.close()


    ##
    # Write to HTK lab files.
    # @param dir        Directory to store the output label files.
    # @param ext        Extension for output label files. If not set, default one stored in MLF is used.
    # @param encoding   Output file encoding (utf8 when not specified).
    #
    def write_labs(self, dir, ext=None, encoding="utf8"):
        if not ext:
            ext = self.__uttext
        try:
            if not os.path.isdir(dir):  os.mkdir(dir)   # create output directory with labs
            for uname in self.__utts.keys():     # through all utterances
                self.__fname = os.path.join(dir,uname+'.'+ext)
                self.__file = codecs.open(self.__fname, 'wt', encoding=encoding)
                for seg in self.__utts[uname]:    # through all segments in utterance
                    self.write_segment(seg)        # write segments
                self.close()
        except IOError:
            raise MlfError, 'Error while writing to file: '+self.__fname


    ##
    # Export in ESPS format to a directory.
    # @param dir        Directory to store the ESPS output label files.
    # @param ext        Extension for output label files. If not set, default one stored in MLF is used.
    # @param encoding   Output file encoding (utf8 when not specified).
    #
    def export_esps(self, dir, ext=None, encoding="utf8"):
        if not self.__format.startswith('tt') or 'm' not in self.__format:
            raise MlfError, 'Cannot export to ESPS format: time boundaries and model name are not present in MLF!'
        if not ext:
            ext = self.__uttext
        try:
            if not os.path.isdir(dir):  os.mkdir(dir)   # create output directory with ESPS labs
            for uname in self.__utts.keys():    # through all utterances
                self.__fname = os.path.join(dir,uname+'.'+ext)
                self.__file = codecs.open(self.__fname, 'wt', encoding=encoding)
                print >> self.__file, '#'               # write ESPS header
                for seg in self.__utts[uname]:          # through all segments in utterance
                    print >> self.__file, '%(end)12.9f 121 %(lab)s' % {'end': seg[self.attr_endTime], 'lab': seg[self.attr_modelName]}
                self.close()
        except IOError:
            raise MlfError, 'Error while writing to file: '+self.__fname

    ##
    # Open MLF file.
    # @param fname Filename
    # @param mode File opening mode (read/write)
    # @see Mlf::close()
    # @param self
    def open(self, fname, mode):
        if self.__file != None:
            raise MlfError, 'File ' + self.__fname + ' has not been closed.'
        try:
            self.__file = codecs.open(fname, mode, encoding=self.__encoding)
            self.__name = fname
            if mode in ['r','rt']:
                self.__read_header()
            elif mode in ['w','wt']:
                self.__write_header()
            else:
                raise MlfError, 'Unsupported mode for opening file: ' + mode
        except IOError:
            raise MlfError, "Error while reading MLF in Mlf::open()"

    ##
    # Converts data stored in asfdata into this class. The correctness of the data is checked, they must represent
    # data read .mlf files (including attribute names). If the source ASF defines some special attributes mapping, it is applied
    # to the attributes in this class.
    #
    #  @param asfdata instance of asf.ASF class holdng the data
    #  @param deep_copy if True, data from asfdata are copied deeply, otherwise only pointers are set (may be dangerous!)
    #  @param self
    def from_asf(self, asfdata, deep_copy = True) :
        format     = ""
        format_w   = ""
        # Attributes in ASF
        asfAttribs = asfdata.get_attrib_names()
        # Attributes required (and optional) in MLF
        reqAttribs = []
        optAttribs = []

        # Change the names of MLF attributes on the basis of mapping defined in ASF
        for asf_attr, mlf_attr in asfdata.get_asf2mlf_attribmap().items() :
            self.add_asf2mlf_attribmap(asf_attr, mlf_attr)

        # Check the attributes and build the format of MLF file
        if self.attr_begTime    in asfAttribs : format   += "t"; reqAttribs.append(self.attr_begTime)
        if self.attr_endTime    in asfAttribs : format   += "t"; reqAttribs.append(self.attr_endTime)
        if self.attr_stateName  in asfAttribs : format   += "s"; reqAttribs.append(self.attr_stateName)
        if self.attr_stateScore in asfAttribs : format   += "l"; reqAttribs.append(self.attr_stateScore)
        if self.attr_modelName  in asfAttribs : format   += "m"; reqAttribs.append(self.attr_modelName)
        if self.attr_modelScore in asfAttribs : format   += "l"; reqAttribs.append(self.attr_modelScore)
        # Words does not have to be in each unit
        if self.attr_word       in asfAttribs : format_w += "w"; optAttribs.append(self.attr_word)

        # Check, if the format is valid! TODO: is it OK?
        if format != 'ttslml' and format != 'ttsm' and format != 'ttml' and format != 'ttm' and format != 'm' :
           raise MlfError, "Invalid MLF format: %s, insufficient attributes in ASF" % format

        # Check if the all the items in ASF are filled by required attributes
        for sentence, items in asfdata.getutts().items() :
            for item in items :
                # Item must have all the required attributes
                if False in [False for a in reqAttribs if not item.has_key(a)] :
                   raise MlfError, "Items in sentence %s in ASF do not have all required attributes" % (sentence)

                # OK, check also optional arguments (and adjust them if necessary)
                # TODO: may be optimized, in this version the value is still checked and replaced ...
                if not item.has_key(self.attr_word) :
                   format_w.replace('w', 'W')

        # Attributes OK, copy the data
        if deep_copy : self.__utts = copy.deepcopy(asfdata.getutts())
        else         : self.__utts =               asfdata.getutts()
        # Set the format
        self.__format   = format
        self.__format_w = format_w

        # Clean other attributes
        self.__file = None
        self.__fname = None

    ##
    # Close MLF file
    # @see Mlf::open()
    # @param self
    def close(self):
        if self.__file and self.__fname not in [self.io_stdin, self.io_stdout] :
            self.__file.close()
            self.__file = None
            self.__fname = None

    ##
    # Get name of the processed MLF file.
    # @return name of the processed MLF file
    # @param self
    def getfname(self):
        return self.__fname

    ##
    # Get utterances structure.
    # @param self
    # @return Returns structure of utterances as a hash with utterance names as keys: { utt1: [seg, seg, ..., seg], utt2: [seg, seg, ..., seg], ...}
    # where uttx is a name of utterance and seg is a hash describing a segment containing the following keys:<br>
    # <ul>
    # <li> Mlf::attr_begTime start time of the segment (if start time was specified in MLF)
    # <li> Mlf::attr_endTime end time of the segment (if end time was specified in MLF)
    # <li> Mlf::attr_stateName state name (if the segment describes a state)
    # <li> Mlf::attr_modelName model name (should always be present in MLF)
    # <li> Mlf::attr_word word (if the segment starts a word)
    # <li> Mlf::attr_stateScore state score (if the segment is a state and score was specified in MLF)
    # <li> Mlf::attr_modelScore model score (if score was specified in MLF)
    # <li> Mlf::attr_unsureBound Indicates whether the <b>end boundary</b> of the segment was unsure (boolean).
    # </ul>
    # Segments are sorted by their appearence in utterances.
    # @note Not all keys must be actually present in segments. For instance, just Mlf::attr_modelName can be present ("plain" MLF format)
    #
    def getutts(self):
        return self.__utts

    ##
    # Return format of MLF file
    # @return format of MLF as a string
    # @param self
    def get_format(self):
        return self.__format + self.__format_w

    ##
    # Remove score from MLF.
    # Both model and state score (likelihood) are removed (if present). The internal format is modified accordingly.
    #
    # @note Removing model OR state score independently could be also beneficial. Not implemented so far.
    #
    def rm_score(self):
        if not "l" in self.__format:
            return
        for utt in self.__utts.keys():
            for seg in self.__utts[utt]:
                if self.attr_modelScore in seg:
                    del seg[self.attr_modelScore]
#                    if self.attr_word in seg:
#                        del seg[self.attr_word]
                if self.attr_stateScore in seg:
                    del seg[self.attr_stateScore]
        self.__format = self.__format.replace("l","")


    ##
    # Add/modify model score to MLF and, possibly also modify state score.
    # Model score is added, or, if already exists, modified to the given value.
    # If state scores were already in MLF, they were set to the same value.
    # Otherwise, state scores are not added. The internal format is modified
    # accordingly.
    #
    # @note As there is no way to check state-level segmentation if state scores
    # are not present, state scores are not added. However, the existing ones
    # are modified.
    #
    def add_score(self, score):
        states = self.__format == "ttslml"
        if not self.__format.endswith("l"): # change the internal format of MLF
            self.__format += "l"
        for utt in self.__utts.keys():
            for seg in self.__utts[utt]:
                seg[self.attr_modelScore] = score   # always add/modify score
                if states:
                    seg[self.attr_stateScore] = score


    ##
    # Remove words from MLF.
    # Words are removed from MLF.
    # @param self
    def rm_words(self):
        if not self.words_included():
            return
        for utt in self.__utts.keys():
            for seg in self.__utts[utt]:
                if self.attr_word in seg:
                    del seg[self.attr_word]
        self.__format_w = ""


    #---------------------------------------------------------------------------
    # Read methods
    #---------------------------------------------------------------------------

    ##
    # Read all utterances in MLF opened in Mlf::read_mlf().
    # Confusing HTK times (100 ns) are converted to sec and stored as floats.
    #
    def __read_utts(self):
        if not self.__file :
            raise MlfError, 'File not open for reading'

        self.__format = None     # init MLF format
        for line in self.__file: # through all lines in MLF
            line = line.decode('string_escape').decode(self.__encoding).strip()     # interpret escape strings and set encoding
            if line.startswith(u'"'):    # start of utterance ?
                re_uttname = self.__re_fname.search(line)   # extract utterance name
                self.__uttname = re_uttname.group(2)
                if self.__uttext and self.__uttext != re_uttname.group(3):
                    raise MlfError, 'Utterance extensions must be the same: '+self.__uttext+' (default) x '+re_uttname.group(3)+' (self.__uttname)'
                self.change_utt_extension(re_uttname.group(3))
                segs = []   # init segments
                continue

            if line.strip() == u'.':     # end of utterance?
                self.__utts[self.__uttname] = segs    # assign segments to an utterance
                continue

            # process segments
            items = line.split()
            if not self.__format:        # check format if not known
                self.__check_format(items)

            if self.__format.startswith(u'tt'):       # convert HTK time to sec
                items[0] = self.__htk2sec(items[0])
                items[1] = self.__htk2sec(items[1])

            segs.append(self.__array2hash(items))


    ##
    # Read single segment from MLF file.
    # @return Segment as a hash with the defined attributes
    #
    def read_segment(self):
        line = self.__file.readline()
        while line.startswith('"') or line.startswith('.') or line.strip() == '':
            if line == "":  # end-of-file
                self.close()
                return None
            if line.startswith('"'):    # line with utterance name
                self.__uttname = self.__re_fname.search(line).group(2)  # get the name
            line = self.__file.readline()

        # read segments in line
        items = line.split()
        if not self.__format:        # check format if not known
            self.__check__format(items)

        if self.__format.startswith('tt'):       # convert HTK time to sec
            items[0] = self.__htk2sec(items[0])
            items[1] = self.__htk2sec(items[1])

        return self.__array2hash(items)

    #---------------------------------------------------------------------------
    # Write methods
    #---------------------------------------------------------------------------

    ##
    # Write name of a utterance to MLF.
    # @param uname utterance name to appear in the output MLF
    #
    def write_name(self, uname):
        if not self.__uttext:
            raise MlfError, 'Extension of the utterances not specified!'

        self.__file.write(u'"*/%s.%s"\n' % (uname, self.__uttext))


    ##
    # Write single segment to MLF
    # @param seg Segment to write.
    # @param self
    def write_segment(self, seg):
        # add symbol of unsure boundary if necessary
        lab = seg[self.attr_modelName]
        if seg.get(self.attr_unsureBound, False) and 'm' in self.__format:
            lab = self.__unsureBound+lab

        if self.__format == 'm':
            self.__file.write(lab)
        elif self.__format == 'ttm':
            self.__file.write(str(self.__sec2htk(seg[self.attr_begTime])) + ' ' + str(self.__sec2htk(seg[self.attr_endTime])) + ' ')
            self.__file.write(lab)
        elif self.__format == 'ttml':
            self.__file.write(str(self.__sec2htk(seg[self.attr_begTime])) + ' ' + str(self.__sec2htk(seg[self.attr_endTime])) + ' ')
            self.__file.write(lab + ' ' + str(seg[self.attr_modelScore]))
        elif self.__format == 'ttslml':
            self.__file.write(str(self.__sec2htk(seg[self.attr_begTime])) + ' ' + str(self.__sec2htk(seg[self.attr_endTime])) + ' ')
            self.__file.write(seg[self.attr_stateName] + ' ' + str(seg[self.attr_stateScore]) + ' ')
            self.__file.write(lab + ' ' + str(seg[self.attr_modelScore]))

        if seg.has_key(self.attr_word):
            self.__file.write(' ' + seg[self.attr_word] + '\n')
        else:
            self.__file.write('\n')

    ##
    # Write symbol of end-of-utterance to MLF.
    # @param self
    def write_endofutt(self):
        self.__file.write('.\n')

    ##
    # Write utterances to MLF opened in Mlf::write_mlf()
    #
    def __write_utts(self):
        if not self.__file :
            raise MlfError, 'No file opened for writing!'

        for name in sorted(self.__utts.keys()) :    # through all utterances
            self.write_name(name)                   # write utterance name
            for seg in self.__utts[name] :          # through all segments in utterance
                self.write_segment(seg)             # write segments
            self.write_endofutt()                   # write end-of-utterance


    ##
    # Change names of utterances.
    # @param table Name conversion table.
    #
    def change_utt_names(self, table):
        for uname in table.keys():
            if table[uname] in self.__utts:     # raise error when utterance with the target name already exists in the MLF
                raise MlfError, 'new utterance name '+table[uname]+ ' already exists in MLF!'
            if uname not in self.__utts:    # skip utterance names not present in the MLF
                continue
            self.__utts[table[uname]] = self.__utts[uname]
            del self.__utts[uname]

    ##
    # Change extension of utterances.
    # @param ext Extension.
    #
    def change_utt_extension(self, ext):
        if not ext:
            raise MlfError, "Extension cannot be empty!"

        if ext.startswith("."):
            ext = ext[1:]
        self.__uttext = ext


    #---------------------------------------------------------------------------
    # Stats methods
    #---------------------------------------------------------------------------

    ##
    # Get number of utterances in MLF
    # @return number of utterances in MLF
    # @param self
    def no_utts(self):
        return len(self.__utts.keys())

    ##
    # Get number of occurences of words in MLF.
    # @return words and their number of occurences as a hash
    # @param self
    def word_occs(self):
        wrds_occs = {}
        if not self.__format_w in ['w','W']:
            raise MlfError, 'Word labels not present in MLF'
        for utt in self.__utts.keys():
            for seg in self.__utts[utt]:
                if seg.has_key(self.attr_word): # word is present
                    if not seg[self.attr_word] in wrds_occs:
                        wrds_occs[seg[self.attr_word]] = 1
                    else:
                        wrds_occs[seg[self.attr_word]] += 1 #orig: wrds_occs[seg[self.attr_word]] + 1
        return wrds_occs

    ##
    # Get number of occurences of models (e.g. triphones or phones) in MLF.
    # @param utts List of utterances to count in. If empty, all utterances are taken.
    # @return models and their number of occurences
    # @param self
    def model_occs(self, utts=[]):
        if not utts:
            utts = self.__utts.keys()
        model_occs = {}
        if self.__format.find('m') == -1:
            raise MlfError, 'Model labels not present in MLF'
        for utt in utts:
            for seg in self.__utts[utt]:
                if self.attr_modelName in seg:
                    if not seg[self.attr_modelName] in model_occs:
                        model_occs[seg[self.attr_modelName]] = 1
                    else:
                        model_occs[seg[self.attr_modelName]] = model_occs[seg[self.attr_modelName]] + 1
#        for utt in self.__utts.keys():
#            for seg in self.__utts[utt]:
#                if seg.has_key(self.attr_modelName):
#                    if not seg[self.attr_modelName] in model_occs:
#                        model_occs[seg[self.attr_modelName]] = 1
#                    else:
#                        model_occs[seg[self.attr_modelName]] = int(model_occs[seg[self.attr_modelName]]) + 1
        return model_occs

    ##
    # Get lenght of input utterance(s).
    # @param ignore_models list of models not counted in (typically leading and trailing silences)
    # @param utts List of utterances (if empty all utterances are taken).
    # @return length (in sec) per utterances in MLF as a hash with utterance names as keys
    # @param self
    def utt_len(self, ignore_models=[], utts=[]):
        len = {}
        if utts == []:    # take all utterances if no defined
            utts = self.utt_names()
        for utt in utts:    # sum of model durations (ignored models are not counted in)
            len[utt] = sum([seg[self.attr_endTime]-seg[self.attr_begTime] for seg in self.__utts[utt] if not seg[self.attr_modelName] in ignore_models])
        return len

    ##
    # Return total length of given utterances.
    # @param ignore_models list of models not counted in (typically leading and trailing silences)
    # @param utts List of utterances to count in. If empty, all utterances in MLF are taken.
    # @return total length of all utterances in MLF
    # @param self
    def len(self, ignore_models=[], utts=[]):
        return sum(self.utt_len(ignore_models,utts).values())

    ##
    # Return lenght of given utterances in models.
    # @note Zero-long models are not counted in.
    # @param ignore List of models not counted in (typically leading and trailing silences).
    # @param utts List of utterances to count in. If empty, all utterance are taken in self.model_seq()
    # @see Mlf::model_seq()
    # @param self
    def model_len(self, ignore=[], utts=[]):    # zero-long models not counted in
        return sum([len([nonzero for nonzero in utt if nonzero > self.__epsilon]) for utt in self.model_seq(ignore,utts).values()])

    ##
    # Return lenght of given utterances in words.
    # @param ignore List of models not counted in
    # @param utts List of utterances (if empty all utterances are taken)
    # @param self
    def word_len(self, ignore=[], utts=[]):
        return sum([len(utt) for utt in self.word_seq(ignore,utts).values()])

    ##
    # For given utterances return number of models uttered per given time.
    # @param ignore_model_len   List of models not counted in  (typically leading and trailing silences)
    # @param ignore_tot_len     List of models not counted in for total duration (typically leading and trailing silences)
    # @param utts               List of utterances.
    # @param time               Time unit in seconds
    # @param self
    def model_rate(self, ignore_model_len=[], ignore_tot_len=[], utts=[], time=1):
        return self.model_len(ignore_model_len,utts)/self.len(ignore_tot_len,utts)*time

    ##
    # For given utterances return number of words uttered per given time.
    # @param ignore_word_len    List of words not counted in  (typically leading and trailing silences)
    # @param ignore_tot_len     List of models not counted in for total duration (typically leading and trailing silences)
    # @param utts               List of utterances.
    # @param time               Time unit in seconds
    def word_rate(self, ignore_word_len=[], ignore_tot_len=[], utts=[], time=60):
        return self.word_len(ignore_word_len, utts) / self.len(ignore_tot_len, utts)*time

    ##
    # Compute statistics of duration for each given label (or all if not specified).
    # @param supp_labs is a list of labels for which statistics are to be computed
    # @return stats is a hast with resulting statistics ('mean' and 'stdev' as keys)
    # @param self
    def dur_stats(self, supp_labs=[]):
        import stats
        durs= {}
        #for lab in supp_labs:   durs[lab] = [] # init duration lists
        # store durations of each label into a list
        for utt in self.__utts:
            for seg in self.__utts[utt]:
                if seg[self.attr_modelName] in supp_labs or supp_labs == []:
                    if seg[self.attr_modelName] not in durs: durs[seg[self.attr_modelName]] = []
                    durs[seg[self.attr_modelName]].append(seg[self.attr_endTime]-seg[self.attr_begTime])

        dur_stats = {}
        for lab in durs.keys():
            dur_stats[lab] = {}
            dur_stats[lab]['mean'] = stats.mean(durs[lab])
            dur_stats[lab]['stdev'] = stats.stdev(durs[lab], None, dur_stats[lab]['mean'])

        return dur_stats

#    Return global MLF stats
#    def stats(self, ignore_models=[], ignore_words=[], utts=[], time_models=1, time_words=60):
#        return {'dur': self.dur(ignore_models,utts), 'word_len': self.word_len(ignore_words,utts), 'model_len': self.model_len(ignore_models,utts),
#                'word_rate': self.word_rate(ignore_words,utts,time_words), 'model_rate': self.model_rate(ignore_models,utts,time_models)}

    ##
    # Get instances of words as hash of MLF segments.
    # @param words     List of words to look for (if none, all words are taken).
    # @param utts      List of utterances (if none, all utterances are taken).
    # @param phn_sep   Phone (or triphone, i.e. model) separator.
    # @param self
    # @return          Returns a structure of instances of the specified words: { utt1: [word, word, ..., word], utt2: [word, word, ..., word], ...}
    #                  where uttx is a name of utterance and word is a hash containing:
    #                  <ul>
    #                  <li> 'text':     (orthographic) text of word
    #                  <li> 'trans':    phonetic transcription of the word (each segment name possibly delimited with phone separator phn_sep)
    #                                   segment names are the actual labels from MLF (phones, triphones, etc.)
    #                  <li> 'segments': list of segments; segment is the same hash as returned by Mlf::getutts().
    #                  </ul>
    #                  Words are sorted by their appearence in utterances.
    #  @see Mlf::getutts()
    def word_insts(self, words=None, utts=None, phn_sep=''):
        # words not included in MLF
        if not self.words_included():
            raise MlfError, 'Word attributes not present in MLF!'

        # take all utterances if no ones are given
        if not utts:
            utts = self.utt_names()

        insts = {}  # hash with utterance names as keys, values are lists of word items
        for utt in utts:

            insts[utt] = []     # init utterance
            #word = []           # init word item
            word = {}           # init word item
            for seg in self.__utts[utt]:    # through all segments in the given utterance
                # the current segment starts a word
                if self.attr_word in seg:
                    # if word item exists (depict previous word)
                    if word:
                        insts[utt].append(word) # append word item to list of words in given utterances
                        word = {}
                    if words == None or seg[self.attr_word] in words : # word is the one under consideration or all words are required
                        #word = [seg[self.attr_word], [seg]]  # set up new word item
                        word['text']        = seg[self.attr_word]
                        word['segments']    = [seg]
                        word['trans']       = seg[self.attr_modelName]
                        continue
                    else:   # the word is not under consideration
                        #word = []
                        word = {}
                        continue
                # if word item exists, current segment is appended
                if word:
                    word['segments'].append(seg)
                    word['trans'] += phn_sep+seg[self.attr_modelName]
                    #word[1].append(seg)
            # end for

            # if word item exists at the end of the utterance
            if word:
                insts[utt].append(word) # append the last word item to list of words in given utterances

            # delete empty utterance from hash
            if not insts[utt]:
                del insts[utt]
        # end for

        return insts

    #---------------------------------------------------------------------------
    # List methods
    #---------------------------------------------------------------------------

    ##
    # Get list of names of utterances in MLF
    #
    # @return List of names of utterances in MLF
    # @param sort Sort the list of utterances
    #
    def utt_names(self, sort=True):
        return sorted(self.__utts.keys()) if sort else self.__utts.keys()


#    Get list of all words in MLF
#    def word_list(self):
#        return sorted(self.word_occs().keys())

#    def model_list(self):
#        return sorted(self.model_occs().keys())

    ##
    # Get list of models for all input utterances.
    # @param ignore list of models not counted in
    # @param utts List of utterances to count in. If None, all not ignored model names in all utterances are returned. If empty, return list of models per each utterance.
    # @see Mlf::model_occs()
    # @return list of models for each utterance
    # @param self
    def model_list(self, ignore=[], utts=None):
        if utts == None:    # Get list of all not ignored model names (e.g. triphones or phones)
          return sorted([model for model in self.model_occs(utts).keys() if not model in ignore])
        if self.__format.find('m') == -1:
            raise MlfError, 'Model labels not present in MLF'
        trans = {}
        if utts == []:    # take all utterances if no defined
            utts = self.utt_names()
        for utt in utts:    # extract model names from utterances (ignored models are not counted in)
            trans[utt] = sorted([model for model in self.model_occs([utt]).keys() if not model in ignore])
        return trans

    ##
    # Get model transcription for all input utterances.
    #
    # @param utts List of utterances to count in. If empty, all utterances are taken.
    # @param phn_sep phone (or triphone, i.e. model) separator
    # @param wrd_sep word separator
    # @param sil long pause symbol
    # @param sp short pause symbol
    # @param inc_sil include long pause in the transcriptions
    # @param inc_sp include short pause in the transcriptions
    # @return model-level transcription of each utterance
    #
    def model_trans(self, utts=[], phn_sep='', wrd_sep='|', sil='$', sp='#', inc_sil=True, inc_sp=True):
        if self.__format.find('m') == -1:
            raise MlfError, 'Model labels not present in MLF'
        trans = {}
        if utts == []:    # take all utterances if no defined
            utts = self.utt_names()
        for utt in utts:    # extract model names from utterances
            trans[utt] = ''
            for seg in self.__utts[utt]:
                if self.attr_word in seg or seg[self.attr_modelName] == sp: # az doplnime do MLF slovo za sp, cast po 'or' lze smazat
                    trans[utt] += wrd_sep
                trans[utt] += phn_sep+seg[self.attr_modelName]
            trans[utt] += wrd_sep
        return trans

    ##
    # Get sequence of words in the given utterances.
    # If no utterances are given, all uterances are taken.
    #
    # @param unames Names of utterances to process.
    # @param ignore List of ignored words.
    # @return hash of sequences of words per utterance
    #
    def word_seq(self, ignore=[], unames=[]):
        words = {}
        if self.__format_w not in ['w', 'W']:
            raise MlfError, 'Word labels not present in MLF'
        if not unames:
            unames = self.utt_names()
        for uname in unames:
            #for seg in self.__utts[uname]:
            words[uname] = [seg[self.attr_word] for seg in self.__utts[uname] if self.attr_word in seg and not seg[self.attr_word] in ignore]
        return words


    ###
    ## Get sequence of segments that start words.
    ##
    ## @param uname Names of utterance to process.
    ## @return List of segments that start words.
    ##
    #def word_segments(self, uname):
        #words = {}
        #if self.__format_w not in ['w', 'W']:
            #raise MlfError, 'Word labels not present in MLF'
        #if not unames:
            #unames = self.utt_names()
        #for uname in unames:
            ##for seg in self.__utts[uname]:
            #words[uname] = [seg[self.attr_word] for seg in self.__utts[uname] if self.attr_word in seg]
        #return words


    ##
    # Get word transcription for all input utterances.
    #
    # @param unames List of utterances to count in. If empty, all utterances are taken.
    # @param sep Word separator
    # @return Hash of word-level transcription of each utterance
    #
    def word_trans(self, unames=[], sep=" "):
        word_trans = {}
        if self.__format_w not in ['w', 'W']:
            raise MlfError, 'Word labels not present in MLF'
        if not unames:
            unames = self.utt_names()
        word_seqs = self.word_seq()
        for uname in unames:
            word_trans[uname] = sep+sep.join(word_seqs[uname])+sep
        return word_trans

    ##
    # Get sequence of models in the given utterances.
    # If no utterances are given, all uterances are taken.
    # @param unames Names of utterances to process.
    # @param ignore List of ignored models.
    # @return hash of sequences of models per utterance
    # @param self
    def model_seq(self, ignore=[], unames=[]):
        seq = {}
        if 'm' not in self.__format:
            raise MlfError, 'Model labels not present in MLF'
        if not unames:
            unames = self.utt_names()
        for uname in unames:
            #for seg in self.__utts[uname]:
            seq[uname] = [seg[self.attr_modelName] for seg in self.__utts[uname] if self.attr_modelName in seg and not seg[self.attr_modelName] in ignore]
        return seq

    ##
    # Get list of words for all input utterances.
    # @param ignore Words not counted in
    # @param utts List of utterances (if none, all utterances are taken)
    # @return List of words for each utterance
    # @param self
    def word_list(self, ignore=[], utts=None):
#        if utts == None:    # Get list of all not ignored words in MLF
#            return sorted([wrd for wrd in self.word_occs().keys() if not wrd in ignore])
        if not self.__format_w in ['w','W']:
            raise MlfError, 'Word labels not present in MLF'
        trans = {}
        if utts == []:    # take all utterances if no defined
            utts = self.utt_names()
        for utt in utts:    # extract word labels from utterances (ignored words not counted in)
            trans[utt] = [seg[self.attr_word] for seg in self.__utts[utt] if self.attr_word in seg and not seg[self.attr_word] in ignore]
        return trans

    ##
    # Get a segment given by the name of utterance and the index in the utterance.
    # @param uname Name of a utterance.
    # @param idx Index of the segment in the utterance or None
    # @return The segment (a hash) if exists and the input index is specified or list of segments if input index is None
    # @param self
    def get_segment(self, uname, idx=None):
        if uname in self.__utts and idx:    # if idx specified, return concrete segment given by name of utterance and the index in the utterance
            if idx >= 0 and idx < len(self.__utts[uname]):
                return self.__utts[uname][idx]
            else:
                raise MlfError('Index '+idx+' out of range in utterance '+uname)
        elif uname in self.__utts:  # if idx not specified, return list of segments in the utterance uname
            return self.__utts[uname]
        else:
            raise MlfError(uname+' is not in MLF')
    
    ##
    #  Delete a segment given by utterance name and index of segment in the utterance.
    #
    #  @param uname Utterance name.
    #  @param idx Index of the segment in the utterance.
    #
    def del_segment(self, uname, idx):
        del self.__utts[uname][idx]


    ##
    # Return length of the specified segment.
    # @param seg the segment
    # @param unit Lengt unit: seconds (s), miliseconds(ms) or nanoseconds (ns)
    # @param self
    def segment_len(self, seg, unit='s'):
        length = self.__seg_len(seg)
        if unit == 'ms':
            length *= 1000
        elif unit == 'ns':
            length *= 10000000
        return length

    ##
    # Get a list of segments present in MLF.
    # Does not get sentence names, end-of-utterances, etc., just segments.
    # @param ignore List of ignored segments - they are not counted in.
    # @param ignore_last Do not use the last segment in each utterance.
    # @return List of segments present in MLF.
    # @param self
    def get_segments(self, ignore=[], ignore_last=False):
        segments = []
        for sname in self.utt_names():
            if ignore_last:
                segments.extend([seg for seg in self.__utts[sname][0:-1] if not seg[self.attr_modelName] in ignore])
            else:
                segments.extend([seg for seg in self.__utts[sname] if not seg[self.attr_modelName] in ignore])
        return segments

    #---------------------------------------------------------------------------
    # Miscellaneous methods
    #---------------------------------------------------------------------------

    ##
    # Remove context from context-dependent model names.
    # @param to_attrib if not set (default), the context-less model names will be set to self.attr_modelName (replacing the original
    #        model names). Otherwise the context-less model names will be moved into the attributes named as set.
    # @param self
    def del_ctx(self, to_attrib = None):
        # Where to move?
        if to_attrib == None :
           to_attrib = self.attr_modelName
        # Delete
        for utt in self.__utts:
            for seg in self.__utts[utt]:
                if not seg.has_key(self.attr_modelName):
                    continue
                if seg[self.attr_modelName].find('+') != -1:
                    seg[to_attrib] = Mlf.__re_ctx.search(seg[self.attr_modelName]).group(1)
                else :
                    seg[to_attrib] = seg[self.attr_modelName]

    ##
    # Convert to diphones.
    # @param sep Separator of phone labels in the diphone label
    #
    def mk_diphone_labs(self, sep=u'-'):
        for utt in self.__utts:
            segs = self.__utts[utt]
            for i in range(len(segs)-1):
                segs[i][self.attr_modelName] = segs[i][self.attr_modelName]+sep+segs[i+1][self.attr_modelName]

    ##
    # Convert to triphones.
    # @param seps Tuple of phone separators (left and right) in the triphone label
    # @todo definovat seznam kontextove nezavislych labelu
    def mk_triphone_labs(self, seps=(u'-', u'+')):
        for utt in self.__utts:
            segs = self.__utts[utt]
            for i in range(1, len(segs)-1):
                prev = self.__re_ctx.search(segs[i-1][self.attr_modelName])
                if prev:
                    prev = prev.group(1)
                else:
                    prev = ""
                #curr = self.__re_ctx.search(segs[i][self.attr_modelName]).group(1)
                #next = self.__re_ctx.search(segs[i+1][self.attr_modelName]).group(1)
                segs[i][self.attr_modelName] = prev+seps[1]+segs[i][self.attr_modelName]+seps[1]+segs[i+1][self.attr_modelName]

    ##
    # Remove symbol of unsure boundary placement.
    # Unsure boundary placement is marked by unsure symbol ('?') at the beginning of the label (model) name in MLF. It denotes that the ending boundary of the phone (or some other unit) is unsure - it need not be correct.
    # @param self
    def rm_unsure_symbol(self):
        for utt in self.__utts.keys():
            for seg in self.__utts[utt]:
                if seg[self.attr_unsureBound]:
                    seg[self.attr_unsureBound] = False
                # unsure symbol is not removed if empty string will be the result
#                if seg[self.attr_modelName].startswith(unsure) and len(seg[self.attr_modelName])>1:
#                    seg[self.attr_modelName] = seg[self.attr_modelName].replace(unsure,'',1)

    ##
    # Check whether MLF contains supported labels.
    # @param supp_names supported model names
    # @return List of unsupported labels, or empty list if all labels are supported
    # @param self
    def check_model_names(self, supp_names):
        return [lab for lab in self.model_list([],None) if not lab in supp_names]

    ##
    # Replace labels (model names). The replacement is given by the conversion table (hash with keys as the original labels and values as the new labels).
    # @param table is a hash with keys as the original labels and values as the new labels
    # @param type specifies the position of a label to be replaced ('b' means beginnigs of words, empty string is everywhere)
    # @param self
    def repl_models(self, table, type=''):
        for utt in self.__utts:
            for seg in self.__utts[utt]:
                if not self.attr_modelName in seg:
                    continue
                if seg[self.attr_modelName] in table:
                    if type == '':   # all occurrences will be replaced
                        seg[self.attr_modelName] = table[seg[self.attr_modelName]]
                    elif type == 'b' and self.attr_word in seg:   # 'b' means that just occurrences at the beginnings of words will be replaced
                        seg[self.attr_modelName] = table[seg[self.attr_modelName]]

    ##
    # Remove labels (model names) present in dic and possibly shift the boundaries.
    # @param dic The dictionary with model labels to remove. The values are 'p' (the removed label will be included in the previous label), 'n' (in the next label), or '0' (no inclusion, label is just cut off resulting in time gap in MLF).
    # @param mark_unsure Mark the corresponding boundary as unsure when removing the segment.
    # @warning Works with model-level MLF! Does not work with state-level MLF so far!!!
    # @param self
    def rm_models(self, dic, mark_unsure=False):
        if "s" in self.__format:
            raise MlfError, "State-level MLF not supported so far."
        for utt in self.__utts.keys():
            segs = self.__utts[utt]
            idx = 1
            while idx<len(segs)-1:    # through all segments except the first one and the last one (they should be always long pause)
                if not self.attr_modelName in segs[idx]: #
                    idx += 1
                    continue
                if segs[idx][self.attr_modelName] in dic and dic[segs[idx][self.attr_modelName]] != "0":
                    if dic[segs[idx][self.attr_modelName]] == "p":
                        segs[idx-1][self.attr_endTime] = segs[idx][self.attr_endTime]
                        if mark_unsure:
                            segs[idx-1][self.attr_unsureBound] = True
                    elif dic[segs[idx][self.attr_modelName]] == "n":
                        segs[idx+1][self.attr_begTime] = segs[idx][self.attr_begTime]
                        if mark_unsure and idx>0:
                            segs[idx-1][self.attr_unsureBound] = True
                    else:
                        raise MlfError, "Unsupported shift symbol: "+dic[segs[idx][self.attr_modelName]]+" ('p', 'n', '0' are currently supported)"
                    del segs[idx]
                    continue
                idx += 1

    ##
    #
    # Remove zero-length models (tee-models, models with skips form the entry state to the exit state).
    # @param models List of tee models to count in. If empty, all models are processed.
    #
    def rm_zero_models(self, minlen=0.0, models=[]):
        if "s" in self.__format:
            raise MlfError, "State-level MLF not supported so far."
        if not self.__format.startswith('tt'):
            return
        for segs in self.__utts.values():
            for idx in range(len(segs)-2, 0, -1):   # first and last unit are not considered (it should be alwyas long pause)
                #if segs[idx][self.attr_begTime] == segs[idx][self.attr_endTime] and segs[idx][self.attr_modelName] not in ignore:
                if models and segs[idx][self.attr_modelName] not in models:
                    continue        # Skip segment as its name is not specified in the list of models to process

                if self.__seg_len(segs[idx]) < max(minlen, self.__epsilon):
                    segs[idx+1][self.attr_begTime] = segs[idx][self.attr_begTime]
                    del segs[idx]

    ##
    # Fix short pause alignments.
    # After HTK alignment, zero short pauses can occur in MLF => they are removed. In addition, when a short pause
    # is followed by 'occlusive phone' (plosive, affricate, glottal stop), it could fill the occlusive part of the
    # phone. Again, such suspicious pauses are detected (using duration statistics of occlusive phones) and removed.
    # @param sp Short pause symbol.
    # @param allow_occl_len Minimum length allowed for a short pause and occlusive standing close to each other.
    # @param self
    def fix_short_pause(self, pauses, allow_occl_len={}):
        for utt in self.__utts.keys():
            segs = self.__utts[utt]
            i = 0
            while i < len(segs)-1:  # last unit is not considered (it should be alwyas long pause) - (i+1)-index will be used
                if not segs[i][self.attr_modelName] in pauses:   # is current segment short pause?
                    i += 1                              # if not continue to the next segment
                    continue
                if self.__seg_len(segs[i]) < self.__epsilon :    # is short pause zero-length?
                    del segs[i]                                 # remove zero pause
                    continue
                # get next segment and, if context-dependent, convert it to phone
                if segs[i+1][self.attr_modelName].find('+') != -1:
                    next_name = self.__re_ctx.search(segs[i+1][self.attr_modelName]).group(1)
                else:
                    next_name = segs[i+1][self.attr_modelName]
                if next_name in allow_occl_len and i>0:
                    # test if combined length of short pause and oclusive phone is lesser than the given length
                    # if occlusive phone is the 1st one in utterance (except the 1st silence), nothing is done in order not to delete the very first silence (assuming that possible shortening of the occlusive doesn't mind as the occlusive will be always synthesised at the beginning of a clause-like unit, i.e. after a pause
                    #   if so => short pause is removed because it fills the oclusive part of the next unit
                    #   if not => short pause is left untouched assuming there is really a pause and then oclusive unit
                    if self.__seg_len(segs[i])+self.__seg_len(segs[i+1]) <= allow_occl_len[next_name]:
                        segs[i+1][self.attr_begTime] = segs[i][self.attr_begTime]
                        del segs[i]
                        # self.__log.write('blabla')
                i += 1

    ##
    # Fix diacritics after HTK manipulated with MLFs.
    # Non-ascii chars are replaced by the symbol '\\xxx'. This function get the right diacritic symbols back.
    #
    #def fix_diacritics(self):
    #    for utt in self.__utts.keys() :
    #        for seg in self.__utts[utt] :
    #
    #            if not self.attr_word in seg :  # process segments with words only
    #                continue
    #
    #            if self.__encoding in ["utf8", u"utf-8", u"UTF8", "UTF-8"] :
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\305\\241', u'š')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\305\\245', u'ť')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\305\\276', u'ž')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\305\\225', u'ŕ')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\303\\241', u'á')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\303\\244', u'ä')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\304\\272', u'ĺ')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\304\\215', u'č')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\303\\251', u'é')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\304\\233', u'ě')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\303\\255', u'í')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\304\\217', u'ď')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\305\\210', u'ň')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\303\\263', u'ó')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\303\\264', u'ô')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\303\\266', u'ö')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\305\\231', u'ř')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\305\\257', u'ů')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\303\\272', u'ú')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\303\\274', u'ü')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\303\\275', u'ý')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\304\\276', u'ľ')
    #            elif self.__encoding in [u"latin2", "iso8859-2", u"ISO-8859-2"] :
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\271', u'š')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\273', u'ť')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\276', u'ž')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\340', u'ŕ')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\341', u'á')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\344', u'ä')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\345', u'ĺ')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\346', u'č')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\350', u'č')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\351', u'é')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\354', u'ě')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\355', u'í')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\357', u'ď')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\362', u'ň')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\363', u'ó')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\364', u'ô')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\366', u'ö')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\370', u'ř')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\371', u'ů')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\372', u'ú')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\374', u'ü')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\375', u'ý')
    #                seg[self.attr_word] = seg[Mlf.attr_word].replace(u'\\265', u'ľ')
    #            else:
    #                raise MlfError, "Unsupported encoding: %s" % encoding


    ##
    # Remove multipauses.
    # A sequence of pause models (sil, sp) is replaced by a single space.
    # @param long_pause Symbol of long pause.
    # @param short_pause Symbol of short pause.
    # @param long_pause_word Symbol of long pause on a word-transcription level.
    # @param self
    def multipause(self, long_pause='$', short_pause='#', long_pause_word='_SIL_'):
        for utt in self.__utts.keys():
            segs = self.__utts[utt]
            i = 0
            while i<len(segs):
                if segs[i][self.attr_modelName] in [long_pause, short_pause]:
                    #beg = segs[i][self.attr_begTime]
                    i += 1
                    while i<len(segs) and segs[i][self.attr_modelName] in [long_pause, short_pause]:
                        if self.__format.startswith('tt'):
                            segs[i-1][self.attr_endTime] = segs[i][self.attr_endTime]
                        if segs[i][self.attr_modelName] == long_pause:
                            segs[i-1][self.attr_modelName] = long_pause
                            segs[i-1][self.attr_word] = long_pause_word
                        del segs[i]
                        #i += 1
                else:
                    i += 1

    ##
    # Remove defined utterances from MLF.
    # @param utts list of utterances to remove or regular expression
    # @param self
    def rm_utts(self, utts):
        if isinstance(utts, list) :     # utts is a list of utterances
            for utt in utts:
                if utt in self.__utts:
                    del self.__utts[utt]
        else:                           # utts is a mask for utterances
            reMatch = re.compile(utts)  
            for utt in self.utt_names() :
                if reMatch.search(utt) :
                    del self.__utts[utt]

    ##
    # Assign word attribute to a phone as specified in table.
    # @param table Table (hash) with phones and corresponding word attributes.
    # @note If the format of MLF is 'm' (i.e. just labels are present), nothing is done because it could be also a words MLF format!
    #
    def assign_attr_word(self, table={'$': '_SIL_', '#': '_SP_', '%': '_BREATH_'}):
        if self.__format == 'm': # if just labels are present in MLF, do nothing, as it could be also a words MLF
            return
        for utt in self.__utts.keys():
            for seg in self.__utts[utt]:
                if seg[self.attr_modelName] in table and self.attr_word not in seg:
                    seg[self.attr_word] = table[seg[self.attr_modelName]]   # add word attribute to a phone


    ##
    # Insert a model at the word boundaries.
    #
    # @param model Cross-word model symbol.
    # @param word Cross-word on word-level symbol.
    #
    def insert_word_bound(self, model='#', word='_SP_'):
        if self.__format != 'ttml':
            raise MlfError, 'The MLF format must be "ttml" + words!'
        if not self.words_included():
            raise MlfError, 'Cannot insert word boundary symbols into MLF: word-level transcription not provided!'
        for utt in self.__utts.keys():
            segs = self.__utts[utt]
            idx = 1
            while idx<len(segs):
                if segs[idx][self.attr_modelName] == model:
                    segs[idx][self.attr_word] = word
                    idx += 1
                elif self.attr_word in segs[idx]:
                    segs.insert(idx, { self.attr_modelName: model, self.attr_word: word, self.attr_begTime: segs[idx][self.attr_begTime], self.attr_endTime: segs[idx][self.attr_begTime], self.attr_modelScore: '0.0', self.attr_unsureBound: False })
                    idx += 1
                idx += 1

    ##
    # Check if words (or word-level transcriptions) are included in MLF.
    # @return True if words are included, or False if not.
    # @param self
    def words_included(self):
        return self.__format_w in ['w', 'W']


    ##
    # Does the given segment start a word?
    #
    # @param uname Name of the utterance
    # @param idx   Index of the segment
    # @return      True if the segment starts a word, or False otherwise.
    #
    def starts_word(self, uname, idx):
        #if idx < 0 or idx >= self.model_len():
        #    raise MlfError, "Index of model segment out of range"
        return self.attr_word in self.__utts[uname][idx]


    ##
    # Get current word. Go through current segments backwards until a word label
    # is found. Raise an exception when words are not included in MLF.
    #
    # @param uname Name of the utterance
    # @param idx   Index of the segment
    # @return      Return the word the segment is in.
    #
    def get_curr_word(self, uname, idx):
        if not self.words_included():
            raise MlfError, "Words not included in MLF"
        if idx >= self.model_len():
            raise MlfError, "Index of model segment out of range"
        while idx > 0:
            if self.starts_word(uname, idx):
                return self.__utts[uname][idx][self.attr_word]
            idx -= 1
        raise MlfError, "Start of utterance reached while searching for word label"


    ##
    # Convert a general MLF to words MLF.
    # Keep word attributes in MLF and remove all other segments.
    # @param self
    def towords(self):
        if self.__format == 'm': # if just labels are present in MLF, do nothing, as it could be also a words MLF
            return
        for utt in self.__utts.keys():
            segs = self.__utts[utt]
            idx = 0
            while idx < len(segs):
            #for idx in range(0, len(segs)):
                if self.attr_word in segs[idx]:    # modify segments with word attribute (they start a word)
                    segs[idx][self.attr_modelName] = segs[idx][self.attr_word]    # model name will be a word
                    if self.attr_begTime     in segs[idx]: del segs[idx][self.attr_begTime]    # all other features are deleted
                    if self.attr_endTime     in segs[idx]: del segs[idx][self.attr_endTime]
                    if self.attr_modelScore  in segs[idx]: del segs[idx][self.attr_modelScore]
                    if self.attr_stateScore  in segs[idx]: del segs[idx][self.attr_stateScore]
                    if self.attr_stateName   in segs[idx]: del segs[idx][self.attr_stateName]
                    del segs[idx][self.attr_word]
                    segs[idx][self.attr_unsureBound] = False
                    idx += 1
                else:
                    segs[idx].clear()
                    del segs[idx] # segments that not start a word are deleted
        self.__format = 'm' # MLF format is 'm' -> just labels (or words, respectivelly) are present


    ##
    # Convert a general MLF to model MLF (format 'm').
    # Keep model names in MLF and remove all other attributes.
    # @param self
    def tomodels(self):
        for utt in self.__utts.keys():
            for seg in self.__utts[utt]:
                if not self.attr_modelName in seg: # delete all non-models lines (i.e. just states lines)
                    seg.clear()
                    del seg
                else:
                    if self.attr_begTime       in seg: del seg[self.attr_begTime]
                    if self.attr_endTime       in seg: del seg[self.attr_endTime]
                    if self.attr_modelScore    in seg: del seg[self.attr_modelScore]
                    if self.attr_word          in seg: del seg[self.attr_word]
        self.__format = 'm'


    ##
    # Remove state lines from MLF.
    # @param self
    def rm_states(self):
        if not "s" in self.__format: return     # no states in MLF

        for uname in self.__utts.keys():
            for idx in range(len(self.__utts[uname])):
                seg = self.__utts[uname][idx]
                if self.attr_modelName in seg and self.__format.startswith("tt"):
                    if idx > 0: self.__utts[uname][idx-1][self.attr_endTime] = time
                    time = seg[self.attr_begTime]
                else:
                    seg.clear()
                    del seg

            # set end time of the last segment in the utterance
            if self.__format.startswith("tt"):
                self.__utts[uname][idx-1][self.attr_endTime] = time

            # upravi format MLF
            self.__format = self.__format.replace("s","")


    ##
    # Keep defined utterances in MLF.
    # @param utts list of utterances to keep or regular expression
    # @param self
    def keep_utts(self, utts):
        if isinstance(utts, list) :             # utts is a list of utterances
            for utt in self.__utts.keys():
                if not utt in utts:
                    del self.__utts[utt]
        else:                                   # utts is a mask for utterances
            reMatch = re.compile(utts)
            for utt in self.utt_names() :
                if not reMatch.search(utt) :
                    del self.__utts[utt]
            

    ##
    # Shift segment boundary times (ie beginning and ending times) by a constant offset.
    # @param offset Offset in seconds (float).
    # @note Zero times (usually the beginning time of the very first segment) and the ending time of the very last segment are not shifted.
    # @param self
    def shift_bound(self, offset):
        for sname in self.utt_names():
            nsegs = len(self.__utts[sname])
            for i in range(0, nsegs):
                # shift beginning times (except for the first one)
                if self.__utts[sname][i][self.attr_begTime] != 0:
                    self.__utts[sname][i][self.attr_begTime] += offset

                # shift ending times (except for the last one)
                if i < nsegs-1:
                    self.__utts[sname][i][self.attr_endTime] += offset

                # safety rules for start times
                if self.__utts[sname][i][self.attr_begTime] < 0:
                    self.__utts[sname][i][self.attr_begTime] = 0    # time is below zero
                elif self.__utts[sname][i][self.attr_begTime] > self.__utts[sname][nsegs-1][self.attr_endTime]:
                    self.__utts[sname][i][self.attr_begTime] = self.__utts[sname][nsegs-1][self.attr_endTime]   # time is after the end of file

                # safety rules for end times
                if self.__utts[sname][i][self.attr_endTime] < 0:
                    self.__utts[sname][i][self.attr_endTime] = 0    # time is below zero
                elif self.__utts[sname][i][self.attr_endTime] > self.__utts[sname][nsegs-1][self.attr_endTime]:
                    self.__utts[sname][i][self.attr_endTime] = self.__utts[sname][nsegs-1][self.attr_endTime]   # time is after the end of file


    ##
    # Round boundary times to the time of the nearest speech vector.
    # In HTK, the sampling period of the speech vectors is given by frame rate.
    # @param frame_rate Speech vectors sampling period frame rate (float in seconds).
    # @param type Type of rounding: 'l' - the left nearest, 'r' - the right nearest, 'b' - both
    # @param self
    def round_bound(self, frame_rate, type='b'):
        for sname in self.utt_names():
            for seg in self.__utts[sname]:
                # indexes of the speech vector (float)
                idx_beg = seg[self.attr_begTime]/frame_rate
                idx_end = seg[self.attr_endTime]/frame_rate

                if type == 'l':
                    idx_beg = math.floor(idx_beg)
                    idx_end = math.floor(idx_end)
                elif type == 'r':
                    idx_beg = math.ceil(idx_beg)
                    idx_end = math.ceil(idx_end)
                else:
                    idx_beg = round(idx_beg)
                    idx_end = round(idx_end)

                seg[self.attr_begTime] = idx_beg*frame_rate
                seg[self.attr_endTime] = idx_end*frame_rate


    ##
    # Changes the name of the MLF attribute according to the given ASF value. Overrides asf.ASF.add_asf2mlf_attribmap() method.
    #
    # @param  asf_att_name the name of attribute stored in the ASF
    # @param  mlf_att_name the name of attribute stored inthe MLF, corresponding to that attribute
    # @param  self
    # @see    asf.ASF.add_asf2mlf_attribmap()
    def add_asf2mlf_attribmap(self, asf_att_name, mlf_att_name) :
        # Change the value of the attribute
        if mlf_att_name == self.attr_begTime     : self.attr_begTime     = asf_att_name
        if mlf_att_name == self.attr_endTime     : self.attr_endTime     = asf_att_name
        if mlf_att_name == self.attr_stateName   : self.attr_stateName   = asf_att_name
        if mlf_att_name == self.attr_stateScore  : self.attr_stateScore  = asf_att_name
        if mlf_att_name == self.attr_modelName   : self.attr_modelName   = asf_att_name
        if mlf_att_name == self.attr_modelScore  : self.attr_modelScore  = asf_att_name
        if mlf_att_name == self.attr_word        : self.attr_word        = asf_att_name
        if mlf_att_name == self.attr_unsureBound : self.attr_unsureBound = asf_att_name

        # TODO: needs to call parent ASF once ASF becomes the parent of Mlf!

    ##
    # Adds the mapping from the ASF to attribute name to attribute name defined in mlf.Mlf (e.g. when phones are stored in the
    # ASF under 'phoneName' attribute, they can be remapped to 'modelName' attribute found in MLF.
    #
    # @param  asf_att_name the name of attribute stored in the ASF. If None, all attributes are deleted
    # @param  self
    def del_asf2mlf_attribmap(self, asf_att_name) :
        # Returns back the value of attribute
        if asf_att_name == None or asf_att_name == self.attr_begTime     : self.attr_begTime    = Mlf.attr_begTime
        if asf_att_name == None or asf_att_name == self.attr_endTime     : self.attr_endTime    = Mlf.attr_endTime
        if asf_att_name == None or asf_att_name == self.attr_stateName   : self.attr_stateName  = Mlf.attr_stateName
        if asf_att_name == None or asf_att_name == self.attr_stateScore  : self.attr_stateScore = Mlf.attr_stateScore
        if asf_att_name == None or asf_att_name == self.attr_modelName   : self.attr_modelName  = Mlf.attr_modelName
        if asf_att_name == None or asf_att_name == self.attr_modelScore  : self.attr_modelScore = Mlf.attr_modelScore
        if asf_att_name == None or asf_att_name == self.attr_word        : self.attr_word       = Mlf.attr_word
        if asf_att_name == None or asf_att_name == self.attr_unsureBound : self.attr_word       = Mlf.attr_unsureBound

        # TODO: needs to call parent ASF once ASF becomes the parent of Mlf!


    #
    # Internal methods.
    #

    ##
    # Read header from MLF.
    # @param self
    def __read_header(self):
        #if self.__file.readline().strip() != '#!MLF!#':
        if self.__file.readline().strip() != self.header:
            raise MlfError, 'invalid HTK MLF file'

    ##
    # Write header to MLF.
    # @param self
    def __write_header(self):
        #self.__file.write("#!MLF!#\n")
        self.__file.write(self.header+"\n")

    ##
    # Convert HTK time (100 ns) to seconds.
    # @param num The number to be converted.
    # @param self
    def __htk2sec(self, num):
        return float(num)/10000000

    ##
    # Convert seconds to HTK time (100 ns).
    # @param num The number to be converted.
    # @param self
    def __sec2htk(self, num):
        return long(round(float(num)*10000000,0))

    ##
    # Check format of MLF and set it to one of the supported ones.
    # @param items Items of segment to be checked.
    #
    def __check_format(self, items):
        if items[0].isdigit() and items[1].isdigit():  # check time boundaries
            if len(items)==7 and self.__islabel(items[2]) and self.__isscore(items[3]) and self.__islabel(items[4]) and self.__isscore(items[5]) and self.__islabel(items[6]):
                self.__format = "ttslml"    # state and model alignment + score (+word)
            elif len(items)==6 and self.__islabel(items[2]) and self.__isscore(items[3]) and self.__islabel(items[4]) and self.__isscore(items[5]):
                self.__format = "ttslml"    # state and model alignment + score
            elif len(items)==5 and self.__islabel(items[2]) and self.__isscore(items[3]) and self.__islabel(items[4]):
                self.__format = "ttml"  # model alignment + score (+word)
            elif len(items)==5 and self.__islabel(items[2]) and self.__islabel(items[3]) and self.__islabel(items[4]):
                self.__format = "ttsm"  # state and model alignment (+word)
            elif len(items)==4 and self.__islabel(items[2]) and self.__isscore(items[3]):
                self.__format = "ttml"  # model alignment + score
#            elif len(items)==4 and self.__islabel(items[2]) and self.__islabel(items[3]):
#                self.__format = "ttmw"  # state and model alignment
#                                        # TODO: ttms zatim neni podporovano, protoze nevim, jak je odlisit od ttmw
            elif len(items)==4 and self.__islabel(items[2]) and self.__islabel(items[3]):
                self.__format = "ttm"  # model alignment (+word)
            elif len(items) == 3 and self.__islabel(items[2]):
                self.__format = "ttm"  # model alignment
            else:
                self.__format = 'xxx'    # unsupported format
                raise MlfError, "unsupported MLF format"
        elif len(items)==1 and (self.__islabel(items[0]) or self.__islabel(items[0])):
            self.__format = 'm'    # labels or words
        else:
            self.__format = 'xxx'    # unsupported format
            raise MlfError, "unsupported MLF format"


    ##
    # Convert array of mlf-items to corresponding hash of mlf-items according to format.
    # @param items Items of segment (list).
    # @param self
    def __array2hash(self, items):
        item_hash = {}

        if self.__format == 'ttm':
            item_hash = {self.attr_begTime : items[0], self.attr_endTime : items[1], self.attr_modelName : items[2]}
            if len(items) == 4:
                item_hash[self.attr_word] = items[3]

        elif self.__format == 'ttml':
            item_hash = {self.attr_begTime : items[0], self.attr_endTime : items[1], self.attr_modelName : items[2],
                         self.attr_modelScore : items[3]}
            if len(items) == 5:
                item_hash[self.attr_word] = items[4]

        elif self.__format == 'ttsm':
            item_hash = {self.attr_begTime : items[0], self.attr_endTime : items[1], self.attr_stateName : items[2],
                         self.attr_modelName : items[3]}
            if len(items) > 3:
                self.attr_modelName = items[3]
            if len(items) > 4:
                item_hash[self.attr_word] = items[4]

        elif self.__format == 'ttslml':
            item_hash = {self.attr_begTime : items[0], self.attr_endTime : items[1], self.attr_stateName : items[2],
                         self.attr_stateScore : items[3], self.attr_modelName : items[4], self.attr_modelScore: items[5]}
            if len(items) > 4:
                item_hash[self.attr_modelName]  = items[4]
                item_hash[self.attr_modelScore] = items[5]
            if len(items) > 6:
                item_hash[self.attr_word] = items[6]

        elif self.__format == 'm':
            item_hash[self.attr_modelName] = items[0]
            if len(items) > 1:
                item_hash[self.attr_word] = items[1]

        item_hash[self.attr_unsureBound] = False # set boundary as not unsure by default

        # check unsure boundary location
        if 'm' in self.__format:
            if self.__isunsure(item_hash[self.attr_modelName]):
            #if item_hash[self.attr_modelName].startswith(self.__unsureBound) and len(item_hash[self.attr_modelName])>1:   # label "?" is not considered as symbol of unsure boundary (empty label would result)
                item_hash[self.attr_unsureBound] = True
                item_hash[self.attr_modelName] = item_hash[self.attr_modelName].replace(self.__unsureBound, "", 1)

        # specify word format if word attribute was read
        if item_hash.has_key(self.attr_word):
            if self.__format_w == '': # 1st word
                self.__format_w = 'w'
        elif self.__format_w == 'w': # no word present this time (but some word has been already present before)
            self.__format_w = 'W'

        return item_hash

    ##
    # Compute length of a segment
    # @param seg Segment.
    # @return length of the segment.
    # @param self
    def __seg_len(self, seg):
        return float(seg[self.attr_endTime])-float(seg[self.attr_begTime])

    ##
    # Check whether the given string stands for MLF score.
    #
    # @param str The string.
    # @return True if string represents score (incl. hand-labeled one), or False otherwise.
    #
    def __isscore(self, str):
        return str[0] == "-" or str[0].isdigit() or str == self.attr_handLab

#    def __isword(self, str):
#        return not str.isdigit()    # label could be also "$" or "#", so just test if the whole string is not a digit
        #return str[0].isalpha() or (str[0] == '\\' and str[1].isdigit())

    ##
    # Check whether the given string is a MLF label.
    # @param str The string
    # @return True if the string is a MLF label or False otherwise
    # @note Correct label is assumed to be a string which consist of at least one non-digit character
    # @param self
    def __islabel(self, str):
        return not str.isdigit()    # label could be also "$" or "#", so just test if the whole string is not a digit

    ##
    # Check whether a label (or the corresponding label-ending boundary) is unsure.
    # @param lab MLF label.
    # @note Label starting with self.__unsureBound ("?") is unsure (our definition -- not defined in HTK MLF)
    # @param self
    def __isunsure(self, lab):
        return lab.startswith(self.__unsureBound) and len(lab)>1   # label "?" is not considered as symbol of unsure boundary (empty label would result)
