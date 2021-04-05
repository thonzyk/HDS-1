# -*- coding: utf-8 -*-
# ASF - ARTIC Segmentation File
# New format for storing information on phonetic segmentation and information on particular units.
# Last modification: October 30, 2006 (zhanzlic@kky.zcu.cz)

import os.path
import bisect
import re
import copy
import codecs
import sys

import mlfext, mlf

## Error class
class Error(Exception):
    pass


## Class for manipulating ASF format (derived from MLF format)
#
# @TODO: zmenit hierarchii trid z <code>mlf <-- mlf_ext <-- asf</code> na <code>asf <-- mlf <-- mlf_ext</code>
class ASF(mlfext.MlfExt):

    ### Constructor
    ##
    ## @param fname is name of ASF (not MLF) file that is to be loaded (optional)
    #def __init__(self, fname = None):

        #mlfext.MlfExt.__init__(self, None)  # no MLF will be loaded (general initialization only)

        ## Initialize innter attributes to their default values
        #self.custom_format()
        ## Prepare data
        #self.__attrib_order = []
        #self.__attrib_align = {}
        #self.__comment_list = []

        ## Rwad file, if set`
        #if ( fname != None ):
            #self.read_asf(fname)

    ## Constructor. Reads the ASF file from path given by: fdir/fname.fext
    #
    # @param fname is name of ASF file that is to be read (without path and extension, if fdir and/or fext are set),
    #        mlf.Mlf.io_stdin if to read from standard input, or a file-like object from which to read the data.
    #        If 'encoding' is set, the object is passed through the codecs to convert the data to unicode.
    # @param fdir  is directory where to look for ASF file (string)
    # @param fext  is extension of the ASF file (string, '.' does not have to be included)
    # @param encoding Input MLF encoding.
    def __init__(self, fname = None, fdir = None, fext = None, encoding='utf8'):
        # no MLF will be loaded (general initialization only)
        mlfext.MlfExt.__init__(self, None, encoding = encoding)

        # Initialize innter attributes to their default values
        self.custom_format()
        # Prepare data
        self.__attrib_order   = []
        self.__attrib_align   = {}
        self.__attrib_asf2mlf = {}
        self.__comment_list   = []
        self.__fname          = None
        self.__encoding       = encoding      # ASF file encoding

        # Rwad file, if set`
        if (fname != None):
            self.read_asf(fname, fdir, fext)

    ## Reads MLF file
    #
    # @param fname Name of MLF, or Mlf.io_stdin (standard input)
    # @param encoding   Input file encoding (that set in constructor is used it None is set)
    def read_mlf(self, fname, encoding=None):
        if encoding:
           self.__encoding = encoding
        mlf.Mlf.read_mlf(self, fname, self.__encoding)
        self.__init_order()
#        self.__correct_values() # !!!Do not convert to strings!!!
        self.__fname = fname


    ## Reads the ASF file from path given by: fdir/fname.fext
    #
    # @param fname is name of ASF file that is to be read (without path and extension, if fdir and/or fext are set),
    #        mlf.Mlf.io_stdin if to read from standard input, or a file-like object from which to read the data.
    #        If 'encoding' is set, the object is passed through the codecs to convert the data to unicode.
    # @param fdir is directory where to look for ASF file (string); ignored when read from stdin
    # @param fext is extension of the ASF file (string, '.' is added when missing); ignored when read from stdin
    # @param encoding   Input file encoding (that set in constructor is used it None is set)
    # @see   mlf.Mlf:io_stdin
    def read_asf(self, fname=mlf.Mlf.io_stdin, fdir = None, fext = None, encoding=None):
        if fname ==  None:
           raise Error, 'no input file specified'
        if encoding:
           self.__encoding = encoding

        try:
            # Read from stdio
            if fname == mlf.Mlf.io_stdin:
               fHandle = codecs.getreader(self.__encoding)(sys.__stdin__)
            # fname is an object from which to read the data
            elif not isinstance(fname, (str, unicode)):
                fHandle = fname if not encoding else codecs.getreader(self.__encoding)(fname)
                fname = 'Unknown source represented by %s' % str(fname)
            else:
               # Add dir and extension, if set
               if fdir:
                  fname = os.path.join(fdir, fname)
               if fext:
                  # Add dot, if not set
                  if fext[0] != '.':
                     fext = '.' + fext
                  fname += fext
               # Open the file
               fHandle = codecs.open(fname, 'rt', encoding = self.__encoding)

            # Read the data
            self.__read_header(fHandle)
            self.__read_body(fHandle)
            self.__fname = fname

            # Close only if not stdin!
            if fname != mlf.Mlf.io_stdin:
               fHandle.close()
        except IOError:
            raise Error, 'error reading file: ' + fname


    ## Writes ASF file
    #
    # @param fname is name of ASF file to write, Mlf.io_stdout if output to stdout is wanted, or
    #        an file-like object to which to write the data. If 'encoding' is set, the object
    #        is passed through the codecs to convert them to the given encoding.
    # @param attrib_order is list of attributes to be printed
    # @param encoding output file encoding (utf8 when not specified).
    # @see   mlf.Mlf:io_stdin
    def write_asf(self, fileName=mlf.Mlf.io_stdout, attrib_order = None, encoding="utf8"):

        if attrib_order != None and not self.attrib_exist(attrib_order):
            raise Error, 'bad attribute list'

        if attrib_order == None:
           attrib_order = self.__attrib_order
        if encoding == None:
           encoding = self.__encoding

        if fileName == mlf.Mlf.io_stdout:
            fHandle = codecs.getwriter(encoding)(sys.__stdout__)
        # fname is an object from which to read the data
        elif not isinstance(fileName, str):
            fHandle = fileName if not encoding else codecs.getwriter(encoding)(fileName)
        else:
            fHandle = codecs.open(fileName, 'wt', encoding = encoding)

        self.__set_alignment()
        self.__write_header(fHandle, attrib_order)
        self.__write_body(fHandle, attrib_order)

        if fileName != mlf.Mlf.io_stdout:
            fHandle.close()

    ## Get name of the processed MLF file.
    #  @return name of the processed MLF file
    #  @param self
    def getfname(self):
        return self.__fname

    ## Gets the list of attributes.
    #
    # @return list of attribute names (equals to get_attrib_order())
    def get_attrib_names(self):
        return self.__attrib_order


    ## Tests whether all attributes from list exist.
    #
    # @param is list of attributes
    # @return True if all attributes from list exist
    def attrib_exist(self, attr_list):
        for attr_name in attr_list:
            if not (attr_name in self.__attrib_order):
                return False
        return True

    ## Appends an empty utterance.
    #
    # @param utt_name is the name of new utterance
    def append_utt(self, utt_name):
        utts = self.getutts()
        if utts.has_key(utt_name):
            raise Error, 'utterance ' + utt_name + ' already exists'
        utts[utt_name] = []


    ## Deletes given utterance.
    #
    # @param utt_name is the name of utterance to be deleted
    def delete_utt(self, utt_name):
        utts = self.getutts()
        if not utts.has_key(utt_name):
            raise Error, 'utterance ' + utt_name + ' does not exist'
        del utts[utt_name]


    ## Gets one utterance (list of segments)
    #
    # @param utt_name is name (label) of requested utterance
    # @return list of segments
    def get_utt(self, utt_name):
        # If the utterance is not defined, use the 'undefined'
        if utt_name == None:
           utt_name = self.__undef_uttname
        # Get the utterance
        return self.getutts()[utt_name]


    ## Gets one segment from the utterance
    #
    # @param seg_idx is index of requested segment
    # @param utt_name is name (label) of requested utterance
    # @return segment (dictionary of attributes)
    def get_segment(self, seg_idx, utt_name = None):
        # Use 'inknown' utterance if other not specified
        if utt_name == None:
            utt_name = self.__undef_uttname
        # Return the item
        return self.getutts()[utt_name][seg_idx]


    ## Gets the value of attribute
    #
    # @param utt_name is name (label) of requested utterance
    # @param seg_idx is index of requested segment
    # @param attrib_name is name of requested attribute
    # @return value of attribute
    def get_attrib(self, utt_name, seg_idx, attrib_name):

        utts = self.getutts()
        if not utts.has_key(utt_name):
            raise Error, 'utterance ' + utt_name + 'not defined'

        utt = utts[utt_name]
        if len(utt) < seg_idx:
            raise Error, 'segment index out of range'

        segment = utt[seg_idx]
        if segment.has_key(attrib_name):
            return segment[attrib_name]
        else:
            return None


    ## Gets length of one utterance
    #
    # @param utt_name is name (label) of requested utterance
    # @return length of utterance
    def get_utt_len(self, utt_name):
        return len(self.getutts()[utt_name])


    ## Gets length of all utterances together
    #
    # @return total length of all utterances
    def get_utts_len(self, utt_name):
        total_len = 0
        for utt_name in self.getutts():
            total_len += len(self.getutts()[utt_name])
        return total_len


    ## Sets the value of given attribute in given utterance
    #
    # @param utt_name is name of requested utterance
    def set_attrib(self, utt_name, seg_idx, attrib_name, attrib_value):
        if not (attrib_name in self.__attrib_order): # new attribute
            self.__attrib_order.append(attrib_name)
        # Set value
        self.getutts()[utt_name][seg_idx][attrib_name] = unicode(attrib_value)

    ## Sets the value of given attribute in given utterance
    #
    # @param utt_name is name of requested utterance
    # @param attribs is hash of attributes to add for the given sentence
    def add_attribs(self, attribs, utt_name):
        # Convert values to string and add keys
        a = {}
        for (k,v) in attribs.items():
            a[k] = unicode(v)
            if not (k in self.__attrib_order): # new attribute
               self.__attrib_order.append(k)
        # Set new line
        self.getutts()[utt_name].append(a)


    ## Adds the list of segments to the given utterance
    #
    # @param segments is a list of segments, where each segment is dictionary containing attributes related to the segment.
    #        Attributes in segments may differ: ({att1:val1, att2:val2, ...}, {att1:val1, att3:val3, ...}, ... {att1:val1, ...})
    # @param utt_name is name of requested utterance
    def add_segments(self, utt_name, segments):
        # If there is not the sentence required, add it
        if utt_name == None:
            utt_name = self.__undef_uttname
        if not self.getutts().has_key(utt_name):
            self.append_utt(utt_name)

        # Add keys
        for s in segments :
            for a in s.keys() :
                if a not in self.__attrib_order : # new attribute
                   self.__attrib_order.append(a)
        # Set new line
        self.getutts()[utt_name].extend(segments)
        # TODO: list of attributes required for all sentence could be given (in case of MLF it is e.g. time beg/end,
        #       modelName, etc.). The attributes of segments could be checked against the list


    ## Returns list of attribute values from utterance (or from all utterances if utt_name isn't given)
    #
    # @param att_name is name of desired attribute
    # @param utt_name is name of desired utterance
    # @return list of attribute values or dictionary of attribute lists (if no utterance is specified)
    def get_values(self, att_name, utt_name = None):
        if utt_name != None:
            values = [];
            for seg_idx in range(self.get_utt_len(utt_name)):
                values.append(self.get_attrib(utt_name, seg_idx, att_name))
        elif self.__undef_uttname not in self.utt_names():
            values = {}
            for utt_name in self.utt_names():
                values[utt_name] = self.get_values(att_name, utt_name)
        else:
            values = [];
            for seg_idx in range(self.get_utt_len(self.__undef_uttname)):
                values.append(self.get_attrib(self.__undef_uttname, seg_idx, att_name))

        return values


    # --------------------------------------------------

    ## Sets values of given attribute (or appends new attributes) in given utterance
    # (when the utterance is empty, new segments are automatically created)
    #
    # @param att_name is name of desired attribute
    # @param values is list of values
    # @param utt_name is (optional) name of desired utterance (if it is not given, self.__undef_uttname will be used)
    def set_values(self, att_name, values, utt_name = None):

        if utt_name == None:
            utt_name = self.__undef_uttname

        if not self.getutts().has_key(utt_name):
            self.append_utt(utt_name)

        utt_len = self.get_utt_len(utt_name)
        if (utt_len != len(values)) and (utt_len != 0):
            raise Error, 'unequal lengths of attribute lists'

        if not (att_name in self.__attrib_order): # new attribute
            self.__attrib_order.append(att_name)

        if utt_len == 0:
            utt_len = len(values)
            for seg_idx in range(utt_len): # new segments have to be created
                self.getutts()[utt_name].append({})

        for seg_idx in range(utt_len):
            self.set_attrib(utt_name, seg_idx, att_name, values[seg_idx])


    # --------------------------------------------------

    ## Deletes all attributes of given name
    #
    # @param attrib_name is the name of attributes to be removed
    def delete_attribs(self, attrib_name):

        for ii in range(len(self.__attrib_order)):
            if self.__attrib_order[ii] == attrib_name:
                del self.__attrib_order[ii]
                break

        if self.__attrib_align.has_key(attrib_name):
            del self.__attrib_align[attrib_name]

        utts = self.getutts()
        for utt_name in self.utt_names():
            utt = utts[utt_name]
            for segment in utt:
                if segment.has_key(attrib_name):
                    del segment[attrib_name]



    ## Sets the comment that will be included in the file header
    #
    # @param comment_list is list of comment lines (each item equals one line in file)
    def set_comment(self, comment_list):
        self.__comment_list = [(c.decode(self.__encoding) if not isinstance(c, unicode) else c) for c in comment_list]


    ## Returns comment which was (will be) included in the file header
    #
    # @param return is list of comment lines (each item equals one line in file)
    def get_comment(self):
        return self.__comment_list


    ## Returns the value of comment-related attribute. The line with comment attributes is expected to be in form:
    #  <code>"#  att_name = att_value/{att_value}/(att_value)"</code>
    #
    #  where value can be simple string, dictionary or tuple, as illustrated.
    #
    # @param  att_name the name of the attribute to find
    # @param  not_found_val the value returned if the attribute was not found
    # @param  self
    # @return the value of attribute as string (in one value is stored) or as dict (if begins with '{' and ends with '}') or
    #         tuple (if begins with '(' and ends with ')'), or 'not_found_val'.
    #
    # @todo   the method could be optimized to parse the attributes in advance. However, in that case the self.set_comment()
    #         method will have to parse the comments set again, plus there will be a problem with adding comment line outside
    #         this class - the adition of new attribute will not be handled at all (e.g. get_comment().append("attrib = value"))
    #         Could it be solved by the replacement of set/get_comment() methods by new methods add_comment(comment_line or [lines]),
    #         clear_comment() and returning copy.deepcopy() in get_comments() method?
    def get_comment_attrib(self, att_name, not_found_val = None):
        ## Deletes ' and " characters from the beginning and the end of string 's'
        def del_quots(s) :
            if s.startswith('"') or s.startswith("'") : s = s[1:]
            if s.endswith('"')   or s.endswith("'")   : s = s[0:-1]
            return s

        # TODO: delat funkci 'eval(".....")'?
        # Search through all the comment lines. Search from the end to return values last added
        for line in reversed(self.__comment_list) :
            data = re.split('[\s]*=[\s]*', line.strip(), 1)
            # If there is only one item in the splitted array, it does not contain the attribute item.
            # Ignore the line also when the first item does not contain the required attribute name
            if len(data) != 2 or data[0] != att_name :
               continue
            # Is the attribute dict? Convert it to dict if so
            if   data[1].startswith('{') and data[1].endswith('}') :
                 try :
                          items     = [ re.split('[\s]*:[\s]*', d)  for d   in re.split('[\s]*,[\s]*', data[1][1:-1])]
                          return dict([(del_quots(k), del_quots(s)) for k,s in items])
                 except :
                          raise  Error, "Incorrect dict format in attribute (comment) line %s" % line

            # Is the attribute tuple? Convert it to tuple if so
            if   data[1].startswith('(') and data[1].endswith(')') :
                 try :
                          return tuple([del_quots(v) for v in re.split('[\s]*,[\s]*', data[1][1:-1])])
                 except :
                          raise  Error, "Incorrect tuple format in attribute (comment) line %s" % line

            # "normal" string attribute
            else :
                 return del_quots(data[1])

        # Not found ...
        return not_found_val

    ## Returns the value of comment-related attribute. The line with comment attributes is expected to be in form:
    #  <code>"#  att_name = att_value/{att_value}/(att_value)"</code>
    #
    #  where value can be simple string, dictionary or tuple, as illustrated.
    #
    # @param  att_name the name of the attribute to find
    # @param  not_found_val the value returned if the attribute was not found
    # @param  self
    # @return the value of attribute as string (in one value is stored) or as dict (if begins with '{' and ends with '}') or
    #         tuple (if begins with '(' and ends with ')'), or 'not_found_val'.
    #
    # @todo   the method could be optimized to parse the attributes in advance. However, in that case the self.set_comment()
    #         method will have to parse the comments set again, plus there will be a problem with adding comment line outside
    #         this class - the adition of new attribute will not be handled at all (e.g. get_comment().append("attrib = value"))
    #         Could it be solved by the replacement of set/get_comment() methods by new methods add_comment(comment_line or [lines]),
    #         clear_comment() and returning copy.deepcopy() in get_comments() method?
    def get_comment_attribs(self):
        attr_list = []
        # Search through all the comment lines
        for line in self.__comment_list :
            data = re.split('[\s]*=[\s]*', line.strip())
            # If there is only one item in the splitted array, it does not contain the attribute item.
            # Ignore the line also when the first item does not contain the required attribute name
            if len(data) == 2  :
               attr_list.append(data[0])
        # Vrat seznam
        return tuple(attr_list)


    ##
    # Returns the mapping of attribute names in the ASF to attribute names defined in mlf.Mlf. The key is the name of attribute stored
    # in the ASF, the value the name of MLF attribute corresponding to this attribute.
    #
    # @param  self
    # @return the dict of attribute mappings or empry dict if no mapping was defined. Copy is returned!
    def get_asf2mlf_attribmap(self) :
        return copy.deepcopy(self.__attrib_asf2mlf)

    ##
    # Returns the mapping of attribute names in the ASF to attribute names defined in mlf.Mlf. The key is the name of attribute stored
    # in the MLF, the value the name of ASF attribute corresponding to this attribute (inversion of ASF.get_asf2mlf_attribmap() method).
    #
    # @param  self
    # @return the dict of attribute mappings or empty dict if no mapping was defined. Copy is returned!
    def get_mlf2asf_attribmap(self) :
        return dict((v,k) for k,v in self.__attrib_asf2mlf.items())

    ##
    # Adds the mapping from the ASF to attribute name to attribute name defined in mlf.Mlf (e.g. when phones are stored in the
    # ASF under 'phoneName' attribute, they can be remapped to 'modelName' attribute found in MLF.
    #
    # @param  asf_att_name the name of attribute stored in the ASF
    # @param  mlf_att_name the name of attribute stored inthe MLF, corresponding to that attribute
    # @param  self
    def add_asf2mlf_attribmap(self, asf_att_name, mlf_att_name) :
        self.__attrib_asf2mlf[asf_att_name] = mlf_att_name

        # HACK: must call parent in mlf.Mlf, to simulate the correct behaviour of case when ASF is parent of Mlf!
        mlf.Mlf.add_asf2mlf_attribmap(self, asf_att_name, mlf_att_name)

    ##
    # Adds the mapping from the ASF to attribute name to attribute name defined in mlf.Mlf (e.g. when phones are stored in the
    # ASF under 'phoneName' attribute, they can be remapped to 'modelName' attribute found in MLF.
    #
    # @param  asf_att_name the name of attribute stored in the ASF. If None, all attributes are deleted
    # @param  self
    def del_asf2mlf_attribmap(self, asf_att_name) :
        if asf_att_name : del self.__attrib_asf2mlf[asf_att_name]
        else            :     self.__attrib_asf2mlf = {}

        # HACK: must call parent in mlf.Mlf, to simulate the correct behaviour of case when ASF is parent of Mlf!
        mlf.Mlf.del_asf2mlf_attribmap(self, asf_att_name)



    # --------------------------------------------------

#    ## Finds the item of 'atrib_name' column nearest to the 'attrib_reqr' value for the utterance 'utt_name'
#    #  <b>The sequence of attributes in the required column must be sorted in ascending order</b>
#    #
#    #
#    # @param attrib_name is the name of attributes column
#    # @param attrib_reqr is the value of attribute for which the nearest is required
#    # @param utt_name is (optional) name of desired utterance (if it is not given, self.__undef_uttname will be used)
#    # @return index of the nearest item (int)
#    def get_nearest_indx(self, attrib_name, attrib_reqr, dist = cmp, utt_name = None):
#        # If the utterance is not defined, use the 'undefined'
#        if utt_name == None:
#           utt_name = self.__undef_uttname
#        # Get all utterances
#        utts = self.getutts()
#        if not utts.has_key(utt_name):
#            raise Error, 'utterance ' + utt_name + 'not defined'
#
#        # Creates the vector of distances - not very optimal but working ;-)
#        dists = [dist(attrib_reqr, attr[attrib_name]) for attr in utts[utt_name]]
#        # Return the index of the nearest item - first with the lowest distance
#        return dists.index(min(dists))
#
#    ## Finds the item of 'atrib_name' column nearest to the 'attrib_reqr' value for the utterance 'utt_name'
#    #  <b>The sequence of attributes in the required column must be sorted in ascending order</b>
#    #
#    # @param attrib_name is the name of attributes column
#    # @param attrib_reqr is the value of attribute for which the nearest is required
#    # @param utt_name is (optional) name of desired utterance (if it is not given, self.__undef_uttname will be used)
#    # @return index of the nearest item
#    def get_nearest_attrib(self, attrib_name, attrib_reqr, dist = cmp, utt_name = None):
#        return self.get_utt(utt_name)[self.get_nearest_indx(attrib_name, attrib_reqr, dist, utt_name)]
#
#    ## @todo: dopsat!
#    #
#    def get_nearest_sortindx(self, attrib_name, attrib_reqr, utt_name = None):
#        print "required: ", attrib_reqr
#        print "have:     ", self.get_values(attrib_name, utt_name)
#        print "len:      ", len(self.get_values(attrib_name, utt_name))
#        print "found:    ", bisect.bisect_right(self.get_values(attrib_name, utt_name), attrib_reqr)
#        #print ""
#
#        # Find the nearest item on the sorted array
#        return bisect.bisect_right(self.get_values(attrib_name, utt_name), attrib_reqr)
#
#    ## @todo: dopsat!
#    #
#    def get_nearest_sortattr(self, attrib_name, attrib_reqr, utt_name = None):
#        return self.get_utt(utt_name)[self.get_nearest_sortindx(attrib_name, attrib_reqr, utt_name)]
#
#    # Finds the item which is "nearest" to the 'reqr_value' value. The "nearest" is defined by the 'dist' function, and can be used
#    #  as follows:
#    #
#    #  Let us expect that we have only "undefined: utterace with atributes:  { "desc" : str, "value" : int, "time" : float }
#    #
#    # When the item with exact description is required, just call:           index = instance.get_attrib_indx(lambda x: cmp("reqr_description", y["desc"]) )
#    # or you can even use function which defines regular expressions
#    #
#    # When the item with exact value is required, just call:                 index = instance.get_attrib_indx(lambda x: indx - x["value"])
#    # or if items with values range are required, call:                      index = instance.get_attrib_indx(lambda x: if x["value"] < lowest_value and x["value"] > highest_value) : return 0 else return 1)
#    #
#    # When the item with time nearest to given time is required, just call:  index = instance.get_attrib_indx(lambda x: abs(reqr_time - x["time"])
#    # etc. You can also look through multiple columns or to use regular
#    # expressions.
#    #
#    # @param dist function (or lambda function) returning distance between two values (always in order: required_value, examined_item)
#    # @param utt_name is (optional) name of desired utterance (if it is not given, self.__undef_uttname will be used)
#    # @return index of the item found
#    #def get_attrib_indx(self, dist, utt_name = None):
#    #    # If the utterance is not defined, use the 'undefined'
#    #    if utt_name == None:
#    #       utt_name = self.__undef_uttname
#    #    # Get all utterances
#    #    utts = self.getutts()
#    #    if not utts.has_key(utt_name):
#    #        raise Error, 'utterance ' + utt_name + 'not defined'
#    #
#    #    # Create the vectror of distances - not very optimal but working even for not sorted sequences ;-)
#    #    dist_vals = [dist(attr) for attr in utts[utt_name]]
#    #    dist_min  =  min(dist_vals)
#    #    # Return the index of the item with the (first) lowest distance
#    #    return [i for i in range(len(dist_vals)) if not dist_vals[i] > dist_min))


    ## Allows to customize the "format" of the output.
    #
    # <b>BE CAREFUL</b>, it overrides the default settings which can lead to error when file with default settings is going to be rerad.
    # <b>USE WITH CARE!</b>
    #
    # @param header_id         identification string at the beginning of asf file
    # @param attrib_separator  character that separates columns of artributes in the asf file
    # @param keylist_begin     character that denotes the begin of attribute list
    # @param keylist_right     character that denotes the end of attribute list
    # @param keylist_separator character that separates attribute names in the file header
    # @param keylist_prefix    string before the list of attributes (in the file header)
    # @param comment_prefix    string before any comment line
    # @param uttname_begin     string that denotes the begin of utterance name in the asf file
    # @param uttname_end       string that denotes the end of utterance name in the asf file
    # @param undef_value       character that indicate undefined values
    def custom_format(self, attrib_separator  = '|',
                            keylist_begin     = '[',
                            keylist_end       = ']',
                            keylist_separator = '|',
                            keylist_prefix    = '',
                            comment_prefix    = '#',
                            uttname_begin     = '"',
                            uttname_end       = '"',
                            undef_value       = '.' ) :

        self.__undef_uttname     = '#!undef!#'             # the name of "dummy utterance" when no utterqnces are added.
                                                           # the value isn't important (won't be used for outprint)
        self.__header_id         = '#!ASF!#'               # identification string at the beginning of asf file
        self.__asf2mlf_mappkeys  = '!MLF!-attrib-mapping'  # The  mapping of attributes between ASF and MLF
        self.__attrib_separator  = attrib_separator
        self.__keylist_begin     = keylist_begin
        self.__keylist_end       = keylist_end
        self.__keylist_separator = keylist_separator
        self.__keylist_prefix    = keylist_prefix
        self.__comment_prefix    = comment_prefix
        self.__uttname_begin     = uttname_begin
        self.__uttname_end       = uttname_end
        self.__undef_value       = undef_value


    ## Wrapps mlf.Mlf.from_asf() method and copies ASF-related attributes when asf.ASF.from_asf() method is called
    #  Implemented to simulate correct behaviour of (planned) case that ASF is parent of MLF.
    #
    #  @todo  this method will not be required once ASF becomes parent of Mlf. Override asf.ASF.read_asf() method in mlf.Mlf, providing
    #         check of attributes (if they correspond to what is expected in MLF) and set the format
    def from_asf(self, asfdata, deep_copy = True) :
        # Call parent
        mlf.Mlf.from_asf(self, asfdata, deep_copy)
        # Copy other attributes
        if deep_copy :
           self.__comment_list = copy.deepcopy(asfdata.get_comment())
           self.__attrib_order = copy.deepcopy(asfdata.__attrib_order)
        else :
           self.__comment_list = asfdata.get_comment()
           self.__attrib_order = asfdata.__attrib_order

    ##
    # The method printing user-readable information about the pitch-mark object
    #
    # @param  self
    #
    def __repr__(self):
        return "[ASF data with %s labels, read form: %s]" % (str(self.__attrib_order), self.__fname)



    # --------------------------------------------------
    #
    #  Internal methods:
    #

    # Inits the order of attributes when a MLF file is loaded.
    def __init_order(self):
        format = self.get_format()

        if format.startswith('m'):
            self.__attrib_order = [ mlf.Mlf.attr_modelName ]
        elif format.startswith('ttml'):
            self.__attrib_order = [ mlf.Mlf.attr_begTime, mlf.Mlf.attr_endTime, mlf.Mlf.attr_modelName,
                                    mlf.Mlf.attr_modelScore ]
        elif format.startswith('ttslml'):
            self.__attrib_order = [ mlf.Mlf.attr_begTime, mlf.Mlf.attr_endTime, mlf.Mlf.attr_stateName,
                                    mlf.Mlf.attr_stateScore, mlf.Mlf.attr_modelName, mlf.Mlf.attr_modelScore ]
        if format.endswith('w') or format.endswith('W'):
            self.__attrib_order.append(mlf.Mlf.attr_word)


    # --------------------------------------------------

    # Replaces numeric values with string
    def __correct_values(self):

        utts = self.getutts()
        for utt_name in self.utt_names():
            utt = utts[utt_name]
            for segment in utt:
                for attrib_name in self.__attrib_order:
                    if segment.has_key(attrib_name):
                        segment[attrib_name] = unicode(segment[attrib_name])


    # --------------------------------------------------

    # Sets optimal alignment (lengths of attributes) for the output
    def __set_alignment(self):
        self.__attrib_align = {};
        for attrib_name in self.__attrib_order:
            self.__attrib_align[attrib_name] = len(attrib_name)

        utts = self.getutts()
        for utt_name in self.utt_names():
            utt = utts[utt_name]
            for segment in utt:
                for attrib_name in self.__attrib_order:
                    if segment.has_key(attrib_name):
                        this_len = len(unicode(segment[attrib_name]))
                        if this_len > self.__attrib_align[attrib_name]:
                            self.__attrib_align[attrib_name] = this_len


    # --------------------------------------------------

    # Reads the header of ASF file
    def __read_header(self, f_handle):
        if f_handle == None:
            raise Error, 'no file opened'
        elif f_handle.readline().strip() != self.__header_id:
            raise Error, 'invalid file header'
        else:
            self.__attrib_order = [];
            line = f_handle.readline().strip()

            # If the next line contains attrbute mapping, read the mapping from it. Little bit hack ...
            if line.find(self.__asf2mlf_mappkeys) > 0 :
               self.__comment_list   = [line[1:], ]
               self.__attrib_asf2mlf =  self.get_comment_attrib(self.__asf2mlf_mappkeys, {})
               self.__comment_list   = []
               # Next line
               line = f_handle.readline().strip()

               # Force the attribute mapping
               for asf_attr, mlf_attr in self.__attrib_asf2mlf.items() :
                   mlf.Mlf.add_asf2mlf_attribmap(self, asf_attr, mlf_attr)


            if self.__keylist_prefix == '':  # no special keylist prefix is defined
                # until keylist is found
                while not ( line.startswith(self.__keylist_begin) and line.endswith(self.__keylist_end) ):
                    line = f_handle.readline().strip()
                    if line == None:
                        raise Error, 'attribute list not found'
                    if line.startswith(self.__comment_prefix):  # comment line
                        #line = line[len(self.__comment_prefix):].lstrip(1)
                        self.__comment_list.append(line[len(self.__comment_prefix):].lstrip())
            else:
                # until keylist prefix is found
                while not ( line.startswith(self.__keylist_prefix) ):
                    line = f_handle.readline().strip()
                    if line == None:
                        raise Error, 'attribute list not found'
                    if line.startswith(self.__comment_prefix):  # comment line
                        #line = line[len(self.__comment_prefix):].lstrip(1)
                        self.__comment_list.append(line[len(self.__comment_prefix):].lstrip())

                # keylist prefix has been found
                left_shift = len(self.__keylist_prefix)
                line = line[left_shift:].lstrip()
                if not ( line.startswith(self.__keylist_begin) and line.endswith(self.__keylist_end) ):
                    raise Error, 'invalid attribute list'

            self.__valid_comment()

            # keylist processing
            left_shift  = len(self.__keylist_begin)
            right_shift = len(self.__keylist_end)
            attribs = line[left_shift:-right_shift].split(self.__keylist_separator)
            for attrib in attribs:
                self.__attrib_order.append(attrib.strip())


    # --------------------------------------------------

    # Reads the content of ASF file (after the header)
    def __read_body(self, f_handle):

        if f_handle == None:
            raise Error, 'no file opened'

        utt_name = self.__undef_uttname
        utt_list = self.getutts()

        line = f_handle.readline()

        while line != '':

            line = line.strip()
            if line.startswith(self.__uttname_begin) and line.endswith(self.__uttname_end):
                utt_name = line[1:-1]
                utt_list[utt_name] = []

            elif line.startswith(self.__attrib_separator) and line.endswith(self.__attrib_separator):

                if (utt_name == self.__undef_uttname) and (not utt_list.has_key(utt_name)):
                # no division into utterances and this is the first unit
                    utt_list[utt_name] = []

                attribs = line[1:-1].split(self.__attrib_separator)
                segment = {}
                for attrib_idx in range(len(self.__attrib_order)):
                    attrib_value = attribs[attrib_idx].strip()
                    if attrib_value == self.__undef_value:
                        continue
                    segment[self.__attrib_order[attrib_idx]] = attrib_value
                utt_list[utt_name].append(segment)

            line = f_handle.readline()


    # --------------------------------------------------

    # Writes the header into ASF file
    def __write_header(self, f_handle, attrib_order):
        if f_handle == None:
            raise Error, 'no file opened'
        else:
            f_handle.write(self.__header_id + '\n')
            if len(self.__attrib_asf2mlf.items()) > 0 :
               f_handle.write(self.__comment_prefix + self.__asf2mlf_mappkeys + ' = {' + ', '.join(["'%s': '%s'" % itm for itm in self.__attrib_asf2mlf.items()]) + '} \n')
            f_handle.write(self.__format_comments() + '\n')
            f_handle.write(self.__format_attrib_names(attrib_order) + '\n')


    # --------------------------------------------------

    # Writes the content into ASF file
    def __write_body(self, f_handle, attrib_order):
        utts = self.getutts()

        for utt_name in self.utt_names():
            if utt_name != self.__undef_uttname:
                f_handle.write('\n' + self.__uttname_begin + utt_name + self.__uttname_end + '\n')
            else:
                f_handle.write('\n')
            utt = utts[utt_name]

            for segment in utt:
                f_handle.write(self.__format_attrib_values(segment, attrib_order) + '\n')


    # --------------------------------------------------

    # Formats the string that contains list of attribute names
    def __format_attrib_names(self, attrib_order):

        format_string = ''
        for name in attrib_order:
            if format_string == '':  # first attribute
                format_string = ' ' + name + (' ' * (self.__attrib_align[name] - len(name) + 1))
            else:
                format_string += self.__keylist_separator + ' ' + name + (' ' * (self.__attrib_align[name] - len(name) + 1))

        if self.__keylist_prefix == '':
            format_string = self.__keylist_begin + format_string + self.__keylist_end
        else:
            format_string = self.__keylist_prefix + ' ' + self.__keylist_begin + format_string + self.__keylist_end

        return format_string


    # --------------------------------------------------

    # Removes empty lines from begin and end of commments
    def __valid_comment(self):

        if self.__comment_list == []: # no comment defined at all
            return

        idx_begin = 0
        idx_end = len(self.__comment_list) - 1

        while self.__comment_list[idx_begin] == '':
            idx_begin += 1
            if idx_begin > idx_end:
                self.__comment_list = []
                return

        while self.__comment_list[idx_end] == '':
            idx_end -= 1
            if idx_end < idx_begin:
                self.__comment_list = []
                return

        self.__comment_list = self.__comment_list[idx_begin:idx_end+1]


    # --------------------------------------------------

    # Returns the string with comments in format for the outprint
    def __format_comments(self):

        if self.__comment_list == []:
            return ''
        else:
            comment_string = self.__comment_prefix + '\n'
            for comment_line in self.__comment_list:
                comment_string += self.__comment_prefix + ' ' + comment_line + '\n'
            comment_string += self.__comment_prefix + '\n'
            return comment_string


    # --------------------------------------------------

    # Formats the string that contains list of attribute values
    def __format_attrib_values(self, segment, attrib_order):

        format_string = ''
        for attrib_name in attrib_order:
            if segment.has_key(attrib_name):
                attrib_value = segment[attrib_name]
            else:
                attrib_value = self.__undef_value

            if format_string == '':  # first attribute

                if self.__keylist_prefix == '':
                    left_space  = ' '
                else:
                    left_space  = ' ' * (len(self.__keylist_prefix) + 2)

                right_space = ' ' * (self.__attrib_align[attrib_name] - len(unicode(attrib_value)) + 1)
                format_string = self.__attrib_separator + left_space + unicode(attrib_value) + right_space + self.__attrib_separator
            else:
                left_space  = ' '
                right_space = ' ' * (self.__attrib_align[attrib_name] - len(unicode(attrib_value)) + 1)
                format_string += left_space + unicode(attrib_value) + right_space + self.__attrib_separator

        return format_string

