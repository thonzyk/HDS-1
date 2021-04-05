# """ Support for processing pitch-mark file
# """
#
# import bisect
#
#
# ##
# #  Class for representation of particular pitch-marks.
# #
# #  A pitch-mark is defined by its time instant and type.
# #  Pre-defined types (constants in the class):
# #  <ul>
# #  <li><i> type_voiced </i>
# #  <li><i> type_unvoiced </i>
# #  <li><i> type_transitional </i>
# #  <li><i> type_unsure </i>
# #  </ul>
# #
# class OnePm(object):
#
#     # constants - do not change!
#     type_voiced         = 'V'
#     type_unvoiced       = 'U'
#     type_transitional   = 'T'
#     type_unsure         = '?'
#
#
#     ##
#     #  Constructor.
#     #
#     #  @param pm_time time instant of the pitch-mark
#     #  @param pm_type type of the pitch-mark
#     #
#     def __init__(self, pm_time, pm_type):
#         self.__time = pm_time
#         self.__type = pm_type
#
#
#     ##
#     #  The method getting the time instant of the pitch-mark.
#     #
#     def get_time(self):
#         return self.__time
#
#
#     ##
#     #  Set a new time instant of the pitch-mark.
#     #
#     #  @param time new time instant
#     #
#     def set_time(self, time):
#         self.__time = time
#
#
#     ##
#     #  The method getting the type of the pitch-mark.
#     #
#     def get_type(self):
#         return self.__type
#
#
#     ##
#     #  Set a new type of pitch-mark.
#     #
#     #  @param type new type
#     #
#     def set_type(self, type):
#         self.__type = type
#
#
#     ##
#     #  Test whether the pitch-mark type is voiced.
#     #
#     def is_voiced(self):
#         return self.__type == OnePm.type_voiced
#
#
#     ##
#     #  Test whether the pitch-mark type is unvoiced.
#     #
#     def is_unvoiced(self):
#         return self.__type == OnePm.type_unvoiced
#
#
#     ##
#     #  Test whether the pitch-mark type is transitional.
#     #
#     def is_transitional(self):
#         return self.__type == OnePm.type_transitional
#
#
#     ##
#     # The method printing user-readable information about the pitch-mark object.
#     #
#     # @param  self
#     #
#     def __repr__(self):
#         return "[pitch-mark " + str(self.__time) + " " + str(self.__type) + "]"
#
#
# # ==============================
#
#
# ##
# #  An auxiliary class. When F<sub>0</sub> is calculated by class Pm, boundary correction (alignment to pitch-mark)
# #  is performed. Some functions return instance of this class which contains corrected (shifted) boundaries
# #  and resulting F<sub>0</sub>.
# #
# class Segment(object):
#
#     ##
#     #  Constructor.
#     #
#     #  @param time1 begin of the segment (float)
#     #  @param time2 end of the segment (float)
#     #  @param f0 average F<sub>0</sub> between <i>time1</i> and <i>time2</i>
#     #
#     def __init__(self, time1, time2, f0):
#         self.__time1 = time1
#         self.__time2 = time2
#         self.__f0 = f0
#
#
#     ##
#     #  Return the begin of the segment.
#     #
#     def get_time1(self):
#         return self.__time1
#
#
#     ##
#     #  Return the end of the segment.
#     #
#     def get_time2(self):
#         return self.__time2
#
#
#     ##
#     #  Return the average F<sub>0</sub> within the segment.
#     #
#     def get_f0(self):
#         return self.__f0
#
#
# # ====================
#
#
# ##
# #  Class for manipulating sequences of pitch-marks corresponding to an utterance.
# #
# #  When seek the index for a time instance (boundary between 2 units) or calculate F<sub>0</sub> of an unit,
# #  boundaries of this unit can be shifted to an surounding pitch-mark
# #  according to the pre-set shift type (set_shift_type(), get_shift_type())
# #  <ul>
# #  <li><i> shift_none </i>    no shift is performed
# #  <li><i> shift_left </i>    shift to the nearest pitch-mark on the left
# #  <li><i> shift_right </i>   shift to the nearest pitch-mark on the right
# #  <li><i> shift_nearest </i> shift to the nearest pitch-mark
# #  </ul>
# #  After this basic shift, an additional boundary correction between voiced and unvoiced unit can be performed,
# #  first or last unvoiced pitch-mark is sought. It is activated by when following constants are used
# #  <ul>
# #  <li><i> shift_Left </i>
# #  <li><i> shift_Right </i>
# #  <li><i> shift_Nearest </i>
# #  </ul>
# #
# #  When the nearest pitch-mark is sought (left, rigth or both), first the absolutely nearest pitch-mark is found,
# #  if its in the area around the given time, then this pitch-mark is selected (no matter whether left or right
# #  parameter was used). This area is defined using the variable <i> match_tol </i> (default value is 0.001 [sec]).
# #
# #  During the additional boundary correction, first/last unvoiced pitch mark is sought in the area given by
# #  variable <i> uv_boundary_tol </i> (default value is 0.02 [sec]).
# #
#
# class Pm(object):
#
#
#     # common class constants and variables
#     shift_none    = 0
#     shift_left    = 1
#     shift_right   = 2
#     shift_nearest = 3
#     shift_Left    = shift_left
#     shift_Right   = shift_right
#     shift_Nearest = shift_nearest
#
#     # boundary type
#     bound_time = 'T'    # time (need not correspond to time of a concrete pitch-mark)
#     bound_idx  = 'I'    # index of pitch-mark
#
#     # some parametres used within calculating f0
#     match_tol       = 0.001  # tolerance for pitch-mark placement
#     uv_boundary_tol = 0.02   # tolerance for pitch-mark placement
#                              # in case of boundary between voiced and unvoiced unit
#                              # (first or last unvoiced pitch-mark is searched)
#     voiced_ratio    = 0.5    # what minimum part of unit should be voiced as to the whole unit is voiced
#     voiced_pm_dist  = 0.02   # maximum distance between 2 pitch-marks in the voiced signal
#     invalid_f0      = -1     # f0 value for unvoiced units
#     idx_continue    = -1     # if the 1st parameter (time) in get_f0 or get_segment is of this value,
#                              # the corresponding 1st index will automatically take the same value
#                              # as the previous end index
#
#
#     ##
#     #  Constructor.
#     #
#     #  @param filename name of text file containing pitch-marks
#     #  @param shift_type
#     #
#     def __init__(self, filename = None, shift_type = shift_nearest):
#         self.__fname = filename
#         self.__last_idx = 0
#         self.__pmlist = []
#         self.__shift_type = shift_type
#
#         if filename != None:
#             self.read_file(filename)
#
#     ##
#     #  Returns new Pm instance, which contains pitch-marks between two given time instances.
#     #
#     #  @param self
#     #  @param time_beg
#     #  @param time_end
#     #
#     def time_slice( self, time_beg=0, time_end=10**100 ):
#
#         if time_beg < 0:
#             time_beg = 0;
#
#         if time_beg >= time_end:
#             return None
#
#         new_pm_obj = Pm( )
#         idx = 0;
#         while ( idx < len( self.__pmlist ) ) and ( time_beg > self.get_time( idx ) ):
#             idx += 1
#
#         while ( idx < len( self.__pmlist ) ) and ( time_end > self.get_time( idx ) ):
#             new_one_pm_obj = OnePm( self.get_time( idx )-time_beg, self.get_type( idx ) )
#             new_pm_obj.append( new_one_pm_obj )
#             idx += 1
#
#         return new_pm_obj
#
#
#     ##
#     #  Read a text file containing pitch-marks.
#     #
#     #  @param filename name of text file containing pitch-marks, or a file-like object from which to read the data.
#     #
#     def read_file(self, filename):
#         try:
#
#             # fname is an object from which to read the data
#             if not isinstance(filename, str) and not isinstance(filename, unicode):
#                self.__fname = 'Unknown source represented by %s' % str(filename)
#                buffer = filename.readlines()
#             # Read from "classic" file
#             else:
#                self.__fname = filename
#                file = open(filename, 'r')
#                buffer = file.readlines()
#                file.close()
#             # Process the buffer
#             self.__process_file(buffer)
#         except IOError, (errno, strerror):
#             raise Exception, 'File "' + filename + '" cannot be processed...'
#
#     ##
#     #  Writes pitch-marks to the text file.
#     #
#     #  @param filename name of text file with pitch-marks stored
#     #
#     def write_file(self, filename):
#         # TODO: zapisovat komentar
#
#         try:
#             file = open(filename, 'w')
#             for p in self.__pmlist:
#                 file.write("%f %f %c\n" % (p.get_time(), p.get_time(), p.get_type()))
#             file.close()
#         except IOError, (errno, strerror):
#             raise Exception, 'File "' + filename + '" cannot be written...'
#
#
#     ##
#     #  Sets the sequence of pitch-marks into the class. The original pitch-marks holded by the class will be lost!
#     #
#     #  @param pmlist the array of new pitch-marks to set (array of pm.OnePm instances: [pm.OnePm, pm.OnePm, ...])
#     #  @param self
#     #
#     def set_pmks(self, pmlist):
#         # TODO: testovat spravnost dat??
#
#         self.__fname = None
#         self.__last_idx = 0
#         self.__pmlist = list(pmlist) # Make copy to prevent modification from outside
#
#     ##
#     #  Clears all pitch-marks in the class.
#     #
#     #  @param self
#     #
#     def clear(self):
#         self.set_pmks([])
#
#     ##
#     #  Test whether the index is in the range of the utterance and can be used.
#     #
#     #  @param idx tested index
#     #
#     def index_feasible(self, idx):
#         return (len(self.__pmlist) > idx) and (0 <= idx)
#
#
#     ##
#     #  Return the time instance of the idx-th pitch-mark
#     #
#     #  @param idx index of desired pitch-mark
#     #
#     def get_time(self, idx):
#         return self.__pmlist[idx].get_time()
#
#
#     ##
#     #  Return the type of the idx-th pitch-mark
#     #
#     #  @param idx index of desired pitch-mark
#     #
#     def get_type(self, idx):
#         return self.__pmlist[idx].get_type()
#
#
#     ##
#     #  Set the type of (unit) time boundary shifting (eg. for F<sub>0</sub> calculation)
#     #
#     def set_shift_type(self):
#         self.__shift_type = type
#
#
#     ##
#     #  Return the type of (phonetic) time boundary shifting
#     #
#     def get_shift_type(self):
#         return self.__shift_type
#
#
#     ##
#     #  Test whether the idx-th pitch-mark is voiced
#     #
#     #  @param idx index of desired pitch-mark
#     #
#     def is_voiced(self, idx):
#         return self.__pmlist[idx].is_voiced()
#
#
#     ##
#     #  Test whether the idx-th pitch-mark is unvoiced
#     #
#     #  @param idx index of desired pitch-mark
#     #
#     def is_unvoiced(self, idx):
#         return self.__pmlist[idx].is_unvoiced()
#
#
#     ##
#     #  Test whether the idx-th pitch-mark is transitional
#     #
#     #  @param idx index of desired pitch-mark
#     #
#     def is_transitional(self, idx):
#         return self.__pmlist[idx].is_transitional()
#
#
#     ##
#     #  Calculate the average F<sub>0</sub> in the interval between 2 given indexes or 2 time instances.
#     #  <br>
#     #  When the unit is unvoiced, the value given by variable <i> invalid_f0 </i> is returned.
#     #  <br>
#     #  Some units are partly voiced and partly unvoiced; the minimum ratio voiced/unvoiced part for
#     #  voiced unit is defined by variable <i> voiced_ratio </i> (default vaue is 0.5).
#     #
#     #  @param param_type type of following parameters (must be set to constant bound_time or bound_idx)
#     #  @param param_begin starting time instance or index (float or int)
#     #  @param param_end terminal time instance or index (float or int)
#     #
#     def get_f0(self, param_type, param_begin, param_end):
#         if param_type == Pm.bound_time:
#
#             if param_begin == Pm.idx_continue:  # continue from the last method usage
#                 idx1 = self.__last_idx
#             else:  # seeking the first index from the start of the utterance
#                 idx1 = self.find_idx(param_begin)
#             idx2 = self.find_idx(param_end, idx1)
#
#         elif param_type == Pm.bound_idx:
#             idx1 = param_begin
#             idx2 = param_end
#         else:
#             pass
#
#         return self.__count_f0(idx1, idx2)
#
#
#     ##
#     #  Calculate the average F<sub>0</sub> in the interval between 2 given time instances
#     #  and return objects of class Segment with resulting F<sub>0</sub> and corrected boundaries.
#     #
#     #  @param time_begin start time instance (float)
#     #  @param time_end terminal time instance (float)
#     #
#     def get_segment(self, time_begin, time_end):
#
#         if self.__shift_type in [ Pm.shift_Left, Pm.shift_Right, Pm.shift_Nearest ]:
#
#             if time_begin == Pm.idx_continue:  # continue from the last method usage
#                 idx1 = self.__last_idx
#             else:
#                 idx1 = self.find_idx_uv(time_begin)
#             idx2 = self.find_idx_uv(time_end, idx1)
#
#         else:
#             if time_begin == Pm.idx_continue:
#                 idx1 = self.__last_idx
#             else:
#                 idx1 = self.find_idx(time_begin)
#             idx2 = self.find_idx(time_end, idx1)
#
#         f0 = self.__count_f0(idx1, idx2)
#
#         if (self.__shift_type != Pm.shift_none):
#             return Segment(self.get_time(idx1), self.get_time(idx2), f0)
#         else:
#             return Segment(time_begin, time_end, f0)
#
#     ##
#     #  Return the sequence of pitch-marks in the interval <code>time_begin, time_end</code> as array [pm.OnePm, pm.OnePm, ...]
#     #
#     #  @param time_begin start time instance (float)
#     #  @param time_end terminal time instance (float)
#     #  @param pm_type_incl types of pitch-marks returned in the resulting array (string, optional)
#     #  @param pm_type_excl types of pitch-marks not returned in the resulting array (string, optional)
#     #
#     #  Either <code>pm_type_incl</code> or <code>pm_type_excl</code> should be defined.
#     #  If none of them is defined, all pitch-marks will be returned.
#     #
#     #  Example:
#     #  <code>get_pmks( 1.0, 2.0, OnePm.type_voiced + OnePm.type_unsure )</code>
#     #
#     def get_pmks( self, time_begin, time_end, pm_type_incl = None, pm_type_excl = None ):
#         ( idx_beg, idx_end ) = self.find_inner_idxs( time_begin, time_end )
#
#         if ( pm_type_incl == None ) and ( pm_type_excl == None ): # all pitch-marks
#             return self.__pmlist[ idx_beg : idx_end+1 ]
#
#         elif ( pm_type_incl != None ):
#             pmk_list = []
#             for pmk in self.__pmlist[ idx_beg : idx_end+1 ]:
#                 if ( pm_type_incl.find( pmk.get_type() ) != -1 ): # found in the "white-list"
#                     pmk_list.append( pmk )
#             return pmk_list
#
#         elif ( pm_type_excl != None ):
#             pmk_list = []
#             for pmk in self.__pmlist[ idx_beg : idx_end+1 ]:
#                 if ( pm_type_excl.find( pmk.get_type() ) == -1 ): # not found in the "black-list"
#                     pmk_list.append( pmk )
#             return pmk_list
#
#
#     ##
#     #  Return all pitch-marks as array [pm.OnePm, pm.OnePm, ...]
#     #
#     #  @param pm_type_incl types of pitch-marks returned in the resulting array (string, optional)
#     #  @param pm_type_excl types of pitch-marks not returned in the resulting array (string, optional)
#     #
#     #  Either <code>pm_type_incl</code> or <code>pm_type_excl</code> should be defined.
#     #  If none of them is defined, all pitch-marks will be returned.
#     #
#     #  Example:
#     #  <code>get_pmks( pm_type_excl = OnePm.type_unvoiced + OnePm.type_transitional )</code>
#     #
#     def get_all_pmks( self, pm_type_incl = None, pm_type_excl = None ):
#
#         if ( pm_type_incl == None ) and ( pm_type_excl == None ): # all pitch-marks
#             return self.__pmlist
#
#         elif ( pm_type_incl != None ):
#             pmk_list = []
#             for pmk in self.__pmlist:
#                 if ( pm_type_incl.find( pmk.get_type() ) != -1 ): # found in the "white-list"
#                     pmk_list.append( pmk )
#             return pmk_list
#
#         elif ( pm_type_excl != None ):
#             pmk_list = []
#             for pmk in self.__pmlist:
#                 if ( pm_type_excl.find( pmk.get_type() ) == -1 ): # not found in the "black-list"
#                     pmk_list.append( pmk )
#             return pmk_list
#
#
#
#     ##
#     #  Return tuple of 2 indices which delimite inner pitch-marks between given time instances
#     #
#     #  @param time_beg
#     #  @param time_end
#     #
#     def find_inner_idxs( self, time_beg, time_end ):
#         if time_beg < 0:
#             time_beg = 0;
#
#         if time_beg >= time_end:
#             return []
#
#         idx = 0;
#         while ( idx < len( self.__pmlist ) ) and ( time_beg > self.get_time( idx ) ):
#             idx += 1
#         idx_beg = idx
#
#         while ( idx < len( self.__pmlist ) ) and ( time_end >= self.get_time( idx ) ):
#             idx += 1
#         idx_end = idx-1
#
#         return ( idx_beg, idx_end )
#
#
#     ##
#     #  Find the nearest pitch-mark for given time instance (according to pre-set shift type).
#     #
#     #  @param time time instance for which the pitch mark index is sought (float)
#     #  @param idx_start starting index for seeking (int, default is 0, if set to <i> idx_continue </i>,
#     #    seeking will start from index where last seeking ended)
#     #  @param skip_T if <code>True</code>, transitional pitch-marks will be skipped during the search
#     #
#     def find_idx(self, time, idx_start = 0, skip_T = True):
#
#         # Find the nearest bigger or equal
#         indx  = bisect.bisect_left([p.get_time() for p in self.__pmlist], time, idx_start)
#         # Must not be out of range
#         indx  = indx >= len(self.__pmlist) and indx -1 or indx
#         indxr = indx
#         indxl = indx -1
#
#         # If equal is expected and not found, error
#         if self.__shift_type == Pm.shift_none :
#            if   self.__pmlist[indx].get_time() != time :
#                 raise ValueError, "Pitch-mark exact to time %f not found, nearest found %f (file %s)"   % (time, self.__pmlist[indx].get_time(), self.__fname)
#            elif self.__pmlist[indx].is_transitional() and skip_T :
#                 raise ValueError, "Pitch-mark exact to time %f found, but it is transitional (file %s)" % (time, self.__fname)
#            else :
#                 return indx
#
#         # Avoid transitional, if required (only one transitional is expected)
#         if skip_T and self.__pmlist[indxr].is_transitional() :
#               indxr = indxr < len(self.__pmlist) -1 and indxr + 1 or indxr - 1
#         if skip_T and self.__pmlist[indxl].is_transitional() :
#               indxl = indxl > 0                     and indxl - 1 or indxl + 1
#
#         # Check nearest
#         if self.__shift_type == Pm.shift_nearest :
#            return abs(time - self.__pmlist[indxl].get_time()) < abs(time - self.__pmlist[indxr].get_time()) and indxl or indxr
#
#         if self.__shift_type == Pm.shift_left :
#            return indxl
#
#         if self.__shift_type == Pm.shift_right :
#            return indxr
#
#
#         #if ( time >= self.__pmlist[-1].get_time() ):
#             #return len( self.__pmlist )-1
#
#         #idx = idx_start
#         #while self.get_time(idx + 1) < time:
#             #idx = idx + 1
#
#         #if skip_T and self.is_transitional(idx):
#             #idx1 = idx-1
#         #else:
#             #idx1 = idx
#
#         #time1 = self.get_time(idx1)
#
#         #if skip_T and self.is_transitional(idx+1):
#             #idx2 = idx+2
#         #else:
#             #idx2 = idx+1
#
#         #time2 = self.get_time(idx2)
#
#         #if  (self.__shift_type == Pm.shift_left) or (self.__shift_type == Pm.shift_Left):
#             ## shift to left pitch-mark
#
#             ## right pitch-mark satisfies tolerance and is nearer than the left one
#             #if time2 < time + Pm.match_tol and time2 - time < time1 - time:
#                 #idx = idx2
#             #else:
#                 #idx = idx1
#
#         #elif (self.__shift_type == Pm.shift_right) or (self.__shift_type == Pm.shift_Right):
#             ## shift to right pitch-mark
#
#             ## left pitch-mark satisfies tolerance and is nearer than the right one
#             #if time1 > time - Pm.match_tol and time2 - time > time - time1:
#                 #idx = idx1
#             #else:  # move to next (right) pitch-mark
#                 #idx = idx2
#
#         #elif (self.__shift_type == Pm.shift_nearest) or (self.__shift_type == Pm.shift_Nearest):
#             ## shift to nearest pitch-mark
#
#             ## right pitch-mark is nearer than left pitch-mark
#             #if time2 - time < time - time1:
#                 #idx = idx2
#             #else:
#                 #idx = idx1
#
#         #self.__last_idx = idx
#         #return idx
#
#     ##
#     #  Find the nearest pitch-mark for given time instance (according to pre-set shift type).
#     #  On boundaries between voiced and unvoiced unit try to find first/last unvoiced pitch-mark
#     #
#     #  @param time time instance for which the pitch mark index is sought (float)
#     #  @param idx_start starting index for seeking (int, default is 0, if set to <i> idx_continue </i>,
#     #    seeking will start from index where last seeking ended)
#     #
#     def find_idx_uv(self, time, idx_start = 0):
#
#         idx = self.find_idx(time, idx_start)
#         if self.is_voiced(idx):
#             idx2 = idx - 1
#             while self.index_feasible(idx2) and (self.get_time(idx2) > time - Pm.uv_boundary_tol):
#                 if self.is_unvoiced(idx2):
#                     idx = idx2
#                     break
#                 idx2 -= 1
#
#             else:
#                 idx2 = idx + 1
#                 while self.index_feasible(idx2) and (self.get_time(idx2) < time + Pm.uv_boundary_tol):
#                     if self.is_unvoiced(idx2):
#                         idx = idx2
#                         break
#                     idx2 += 1
#
#         elif self.is_unvoiced(idx):
#             idx2 = idx - 1
#             while self.index_feasible(idx2) and (self.get_time(idx2) > time - Pm.uv_boundary_tol):
#                 if self.is_voiced(idx2):
#                     idx = idx2+1
#                     break
#                 idx2 -= 1
#
#             else:
#                 idx2 = idx + 1
#                 while self.index_feasible(idx2) and (self.get_time(idx2) < time + Pm.uv_boundary_tol):
#                     if self.is_voiced(idx2):
#                         idx = idx2-1
#                         break
#                     idx2 += 1
#
#         self.__last_idx = idx
#         return idx
#
#     ##
#     #  Find the nearest pitch-mark for given time instance (according to pre-set shift type) and returns its instance.
#     #
#     #  @param time time instance for which the pitch mark index is sought (float)
#     #  @param idx_start starting index for seeking (int, default is 0, if set to <i> idx_continue </i>,
#     #    seeking will start from index where last seeking ended)
#     #  @param skip_T if <code>True</code>, transitional pitch-marks will be skipped during the search
#     #  @return the instance of pitch-mark found (pm.OnePm)
#     #  @see pm.Pm.find_idx()
#     #
#     def find_pmk(self, time, idx_start = 0, skip_T = True):
#         return self.__pmlist[self.find_idx(time, idx_start, skip_T)]
#
#     ##
#     #  Find the nearest pitch-mark for given time instance (according to pre-set shift type).
#     #
#     #  @param time time instance for which the pitch mark index is sought (float)
#     #  @param idx_start starting index for seeking (int, default is 0, if set to <i> idx_continue </i>,
#     #    seeking will start from index where last seeking ended)
#     #  @return the instance of pitch-mark found (pm.OnePm)
#     #  @see pm.Pm.find_idx_uv()
#     #
#     def find_pmk_uv(self, time, idx_start = 0):
#         return self.__pmlist[self.find_idx_uv(time, idx_start)]
#
#
#     ##
#     #  Return the name of loaded text file with pitch-marks.
#     #
#     def get_file_name(self):
#         return self.__fname
#
#
#     ##
#     #  Appends a new pitch-mark.
#     #
#     #  @param self
#     #  @param item
#     #
#     def append( self, items ):
#         if isinstance( items, OnePm ):
#             self.__pmlist.append( items )
#         elif isinstance( items, list ):
#             self.__pmlist.extend( items )
#         elif isinstance( items, Pm ):
#             self.__pmlist.extend( items.get_all_pmks() )
#
#
#     ##
#     # Insert new pitch-mark(s)
#     #
#     # @param idx    Index of a pitch-mark to insert before (like in standard insert function)
#     # @param items  Single pitch-mark or a list of pitch-marks or a pitch-mark object
#     #
#     def insert(self, idx, items) :
#         if isinstance(items, OnePm) :
#             self.__pmlist.insert(idx, items)
#         elif isinstance(items, list) :
#             self.__pmlist = self.__pmlist[:idx] + items + self.__pmlist[idx+1:]
#         elif isinstance(items, Pm) :
#             self.__pmlist = self.__pmlist[:idx] + items.get_all_pmks() + self.__pmlist[idx+1:]
#
#
#     ##
#     # The method enabling index-like access into the array of pitch-marks.
#     #
#     # @param  index the index of the required pitch-mark (int)
#     # @param  self
#     # @return OnePm object
#     #
#     def __getitem__(self, index):
#         return self.__pmlist[index]
#
#
#     ##
#     #  The metod for deleting pitch-mark given by index
#     #
#     # @param self
#     # @param index the index of the required pitch-mark (int)
#     #
#     def __delitem__( self, index ):
#         if ( index < len( self.__pmlist ) ):
#             del self.__pmlist[ index ]
#
#     ##
#     # The method getting the number of pitch-marks in the class
#     #
#     # @param  self
#     #
#     def __len__(self):
#         return len(self.__pmlist)
#
#     ##
#     # The method printing user-readable information about the pitch-mark object
#     #
#     # @param  self
#     #
#     def __repr__(self):
#         return "[Array of %8d pitch-marks, read form: %s]" % (len(self.__pmlist), self.__fname)
#
#
#     ##
#     #  Process the content of pitch-mark text file.
#     #
#     #  @param buffer loaded content of the file
#     #
#     def __process_file(self, buffer):
#
#         for line in buffer:
#             stringlist = line.split()
#             time = float(stringlist[1])
#             type = stringlist[2]
#
#             #if type == OnePm.type_transitional:
#             #    continue
#
#             self.__pmlist.append( OnePm(time, type) )
#
#
#     ##
#     #  Counts the average F<sub>0</sub> in the interval between 2 indexes.
#     #
#     def __count_f0(self, idx1, idx2):
#
#         vpm_count = 0
#         f0_sum = 0
#         v_signal = 0
#         u_signal = 0
#
#         time1 = self.get_time(idx1)
#
#         idx = idx1
#         while idx2 > idx:
#
#             if self.is_transitional(idx):
#                 idx = idx + 1
#                 continue
#
#             time2 = self.get_time(idx + 1)
#             pm_dist = time2 - time1
#
#             if self.is_voiced(idx) and self.is_voiced(idx+1):
#
#                 if pm_dist <= Pm.voiced_pm_dist:
#                     f0_sum = f0_sum + 1/pm_dist
#                     v_signal = v_signal + pm_dist
#                 else:
#                     u_signal = u_signal + pm_dist
#                 vpm_count = vpm_count + 1
#             else:
#                 u_signal = u_signal + pm_dist
#
#             time1 = time2
#             idx = idx + 1
#
#         if vpm_count > 0 and v_signal/float(v_signal + u_signal) >= Pm.voiced_ratio:
#             f0 = f0_sum/vpm_count  # frequency of voiced unit
#         else:
#             f0 = Pm.invalid_f0 # unvoiced unit has no f0 frequency
#
#         return f0
#
#
#
# ##
# # Procedure computing the mean F0 from the list (or tuple) of pm.OnePm classes.
# # Only pitch-marks of given type are taken into account.
# #
# # @param  pmarks the sequence of pitch-marks (list or tuple of pm.OnePm instances)
# # @param  typ    the type of pitch-marks computed (pm.OnePm.type_voiced or pm.OnePm.type_unvoiced)
# #                The default is voiced type.
# # @return the mean F0 value (float), or -1 when it cannot be computed
# #
# def counf_f0(pmarks, typ = OnePm.type_voiced):
#
#     sum_F0 = 0
#     num_F0 = 0
#     # Process all pitch-marks
#     for i in range(1, len(pmarks)) :
#         if (pmarks[i -1].get_type() == typ and pmarks[i].get_type() == typ) :
#             sum_F0 += 1.0 / (pmarks[i].get_time() - pmarks[i -1].get_time())
#             num_F0 += 1
#
#     # Return the value
#     if num_F0 == 0 :
#        return -1.0
#     else :
#        return sum_F0 / num_F0
#
# ##
# # Procedure computing the mean T0 from the list (or tuple) of pm.OnePm classes.
# # Only pitch-marks of given type are taken into account.
# #
# # @param  pmarks the sequence of pitch-marks (list or tuple of pm.OnePm instances)
# # @param  typ    the type of pitch-marks computed (pm.OnePm.type_voiced or pm.OnePm.type_unvoiced)
# #                The default is voiced type.
# # @return the mean T0 value (float), or -1 when it cannot be computed
# #
# def counf_t0(pmarks, typ = OnePm.type_voiced):
#
#     sum_T0 = 0
#     num_T0 = 0
#     # Process all pitch-marks
#     for i in range(1, len(pmarks)) :
#         if (pmarks[i -1].get_type() == typ and pmarks[i].get_type() == typ) :
#             sum_T0 += pmarks[i].get_time() - pmarks[i -1].get_time()
#             num_T0 += 1
#
#     # Return the value
#     if num_T0 == 0 :
#        return -1.0
#     else :
#        return sum_T0 / num_T0
#
