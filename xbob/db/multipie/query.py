#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Laurent El Shafey <Laurent.El-Shafey@idiap.ch>

"""This module provides the Dataset interface allowing the user to query the
Multi-PIE database in the most obvious ways.
"""

import os
from bob.db import utils
from .models import *
from .driver import Interface

INFO = Interface()

SQLITE_FILE = INFO.files()[0]

class Database(object):
  """The dataset class opens and maintains a connection opened to the Database.

  It provides many different ways to probe for the characteristics of the data
  and for the data itself inside the database.
  """

  def __init__(self):
    # opens a session to the database - keep it open until the end
    self.connect()

  def connect(self):
    """Tries connecting or re-connecting to the database"""
    if not os.path.exists(SQLITE_FILE):
      self.session = None

    else:
      self.session = utils.session_try_readonly(INFO.type(), SQLITE_FILE)

  def is_valid(self):
    """Returns if a valid session has been opened for reading the database"""

    return self.session is not None

  def assert_validity(self):
    """Raise a RuntimeError if the database backend is not available"""

    if not self.is_valid():
      raise RuntimeError, "Database '%s' cannot be found at expected location '%s'. Create it and then try re-connecting using Database.connect()" % (INFO.name(), SQLITE_FILE)

  def __check_validity__(self, l, obj, valid, default):
    """Checks validity of user input data against a set of valid values"""
    if not l: return default
    elif not isinstance(l, (tuple,list)):
      return self.__check_validity__((l,), obj, valid, default)
    for k in l:
      if k not in valid:
        raise RuntimeError, 'Invalid %s "%s". Valid values are %s, or lists/tuples of those' % (obj, k, valid)
    return l

  def groups(self):
    """Returns the names of all registered groups"""

    return ProtocolPurpose.group_choices # Same as Client.group_choices for this database

  def genders(self):
    """Returns the list of genders"""

    return Client.gender_choices

  def subworlds(self):
    """Returns the list of subworlds"""

    self.assert_validity()

    return list(self.session.query(Subworld))

  def has_subworld(self, name):
    """Tells if a certain subworld is available"""

    self.assert_validity()
    return self.session.query(Subworld).filter(Subworld.name==name).count() != 0

  def subworld_names(self):
    """Returns all registered subworld names"""

    self.assert_validity()
    l = self.subworlds()
    retval = [str(k.name) for k in l]
    return retval

  def expressions(self):
    """Returns the list of expressions"""

    self.assert_validity()

    return list(self.session.query(Expression))

  def has_expression(self, name):
    """Tells if a certain expression is available"""

    self.assert_validity()
    return self.session.query(Expression).filter(Expression.name==name).count() != 0

  def expression_names(self):
    """Returns all registered expression names"""

    self.assert_validity()
    l = self.expressions()
    retval = [str(k.name) for k in l]
    return retval

  def cameras(self):
    """Returns the list of cameras"""

    self.assert_validity()

    return list(self.session.query(Camera))

  def has_camera(self, name):
    """Tells if a certain camera is available"""

    self.assert_validity()
    return self.session.query(Camera).filter(Camera.name==name).count() != 0

  def camera_names(self):
    """Returns all registered camera names"""

    self.assert_validity()
    l = self.cameras()
    retval = [str(k.name) for k in l]
    return retval

  def clients(self, protocol=None, groups=None, subworld=None, gender=None, birthyear=None):
    """Returns a set of Clients for the specific query by the user.

    Keyword Parameters:

    protocol
      One of the Multi-PIE protocols (use protocol_names() to get the list of
      available ones)

    groups
      The groups to which the clients belong ('dev', 'eval', 'world')

    subworld
      Specify a split of the world data ('sub41', 'sub81', 'sub121', 'sub161')
      In order to be considered, "world" should be in groups.

    gender
      The genders to which the clients belong ('female', 'male')

    birthyear
      The birth year of the clients (in the range [1900,2050])

    Returns: A list containing all the Clients which have the given properties.
    """

    self.assert_validity()

    VALID_PROTOCOLS = self.protocol_names()
    VALID_GROUPS = self.groups()
    VALID_SUBWORLDS = self.subworld_names()
    VALID_GENDERS = self.genders()
    VALID_BIRTHYEARS = range(1900, 2050)
    VALID_BIRTHYEARS.append(57) # bug in subject_list.txt (57 instead of 1957)
    protocol = self.__check_validity__(protocol, 'protocol', VALID_PROTOCOLS, VALID_PROTOCOLS)
    groups = self.__check_validity__(groups, 'group', VALID_GROUPS, VALID_GROUPS)
    if subworld: subworld = self.__check_validity__(subworld, 'subworld', VALID_SUBWORLDS, '')
    gender = self.__check_validity__(gender, 'gender', VALID_GENDERS, VALID_GENDERS)
    birthyear = self.__check_validity__(birthyear, 'birthyear', VALID_BIRTHYEARS, VALID_BIRTHYEARS)
    # List of the clients
    retval = []
    # World data
    if "world" in groups:
      q = self.session.query(Client)
      if subworld:
        q = q.join(Subworld, Client.subworld).filter(Subworld.name.in_(subworld))
      q = q.filter(Client.sgroup == 'world').\
            filter(Client.gender.in_(gender)).\
            filter(Client.birthyear.in_(birthyear)).\
            order_by(Client.id)
      retval += list(q)
    # dev / eval data
    if 'dev' in groups or 'eval' in groups:
      q = self.session.query(Client).\
            filter(and_(Client.sgroup != 'world', Client.sgroup.in_(groups))).\
            filter(Client.gender.in_(gender)).\
            filter(Client.birthyear.in_(birthyear)).\
            order_by(Client.id)
      retval += list(q)
    return retval

  def has_client_id(self, id):
    """Returns True if we have a client with a certain integer identifier"""

    self.assert_validity()
    return self.session.query(Client).filter(Client.id==id).count() != 0

  def client(self, id):
    """Returns the Client object in the database given a certain id. Raises
    an error if that does not exist."""

    self.assert_validity()
    return self.session.query(Client).filter(Client.id==id).one()

  def tclients(self, protocol=None, groups=None):
    """Returns a set of T-Norm clients for the specific query by the user.

    Keyword Parameters:

    protocol
      One of the Multi-PIE protocols (use protocol_names() to get the list of
      available ones)

    groups
      The groups to which the clients belong ('dev', 'eval').

    Returns: A list containing all the client ids belonging to the given group.
    """

    VALID_GROUPS = ('dev', 'eval')
    groups = self.__check_validity__(groups, "group", VALID_GROUPS, VALID_GROUPS)
    tgroups = []
    if 'dev' in groups: tgroups.append('eval')
    if 'eval' in groups: tgroups.append('dev')
    return self.clients(protocol, tgroups)

  def zclients(self, protocol=None, groups=None):
    """Returns a set of Z-Norm clients for the specific query by the user.

    Keyword Parameters:

    protocol
      One of the Multi-PIE protocols (use protocol_names() to get the list of
      available ones)

    groups
      The groups to which the clients belong ('dev', 'eval').

    Returns: A list containing all the client ids belonging to the given group.
    """

    VALID_GROUPS = ('dev', 'eval')
    groups = self.__check_validity__(groups, "group", VALID_GROUPS, VALID_GROUPS)
    zgroups = []
    if 'dev' in groups: zgroups.append('eval')
    if 'eval' in groups: zgroups.append('dev')
    return self.clients(protocol, zgroups)

  def models(self, protocol=None, groups=None):
    """Returns a set of models for the specific query by the user.

    Keyword Parameters:

    protocol
      One of the Multi-PIE protocols (use protocol_names() to get the list of
      available ones)

    groups
      The groups to which the subjects attached to the models belong ('dev', 'eval', 'world')

    Returns: A list containing all the model ids belonging to the given group.
    """

    return self.clients(protocol, groups)

  def tmodels(self, protocol=None, groups=None):
    """Returns a set of T-Norm models for the specific query by the user.

    Keyword Parameters:

    protocol
      One of the Multi-PIE protocols (use protocol_names() to get the list of
      available ones)

    groups
      The groups to which the models belong ('dev', 'eval').

    Returns: A list containing all the model ids belonging to the given group.
    """

    return self.tclients(protocol, groups)

  def get_client_id_from_model_id(self, model_id):
    """Returns the client_id attached to the given model_id

    Keyword Parameters:

    model_id
      The model_id to consider

    Returns: The client_id attached to the given model_id
    """
    return model_id

  def objects(self, protocol=None, purposes=None, model_ids=None, groups=None,
      classes=None, subworld=None, expressions=None, cameras=None, world_sampling=1,
      world_noflash=False, world_first=False, world_second=False, world_third=False,
      world_fourth=False, world_nshots=None, world_shots=None):
    """Returns a set of Files for the specific query by the user.

    Keyword Parameters:

    protocol
      One of the Multi-PIE protocols (use protocol_names() to get the list of
      available ones)

    purposes
      The purposes required to be retrieved ('enrol', 'probe', 'train') or a tuple
      with several of them. If 'None' is given (this is the default), it is
      considered the same as a tuple with all possible values. This field is
      ignored for the data from the "world" group.

    model_ids
      Only retrieves the files for the provided list of model ids (claimed
      client id).  If 'None' is given (this is the default), no filter over
      the model_ids is performed.

    groups
      One of the groups ('dev', 'eval', 'world') or a tuple with several of them.
      If 'None' is given (this is the default), it is considered the same as a
      tuple with all possible values.

    classes
      The classes (types of accesses) to be retrieved ('client', 'impostor')
      or a tuple with several of them. If 'None' is given (this is the
      default), it is considered the same as a tuple with all possible values.

    subworld
      Specify a split of the world data ('sub41', 'sub81', 'sub121', 'sub161')
      In order to be considered, "world" should be in groups.

    expressions
      The (face) expressions to be retrieved (use expression_names() to get the
      list of expressions) or a tuple with several of them.
      If 'None' is given (this is the default), it is considered the same as
      a tuple with all possible values. Notice that some protocols only contain
      images with 'neutral' expression.

    cameras
      The cameras to be retrieved (use camera_names() to get the list of cameras)
      r a tuple with several of them. If 'None' is given (this is the default),
      it is considered the same as a tuple with all possible values. The cameras
      keyword has no impact for some protocols (frontal images ones).

    world_sampling
      Samples the files from the world data set. Keeps only files such as::

        File.client_id + File.shot_id % world_sampling == 0

      This argument should be an integer between 1 (keep everything) and 19.
      It is not used if world_noflash is also set.

    world_nshots
      Only considers the n first shots from the world data set.

    world_shots
      Only considers the shots with the given ids.

    world_noflash
      Keeps the files from the world dataset recorded without flash (shot 0)

    world_first
      Only uses data from the first recorded session of each user of the world
      dataset.

    world_second
      Only uses data from the second recorded session of each user of the world
      dataset.

    world_third
      Only uses data from the third recorded session of each user of the world
      dataset.

    world_fourth
      Only uses data from the fourth recorded session of each user of the world
      dataset.

    Returns: A set of Files with the given properties.
    """

    self.assert_validity()

    VALID_PROTOCOLS = self.protocol_names()
    VALID_PURPOSES = self.purposes()
    VALID_GROUPS = self.groups()
    VALID_CLASSES = ('client', 'impostor')
    VALID_SUBWORLDS = self.subworld_names()
    VALID_EXPRESSIONS = self.expression_names()
    VALID_CAMERAS = self.camera_names()

    protocol = self.__check_validity__(protocol, 'protocol', VALID_PROTOCOLS, VALID_PROTOCOLS)
    purposes = self.__check_validity__(purposes, 'purpose', VALID_PURPOSES, VALID_PURPOSES)
    groups = self.__check_validity__(groups, 'group', VALID_GROUPS, VALID_GROUPS)
    classes = self.__check_validity__(classes, 'class', VALID_CLASSES, VALID_CLASSES)
    if subworld: subworld = self.__check_validity__(subworld, 'subworld', VALID_SUBWORLDS, VALID_SUBWORLDS)
    if expressions: expressions = self.__check_validity__(expressions, 'expression', VALID_EXPRESSIONS, VALID_EXPRESSIONS)
    if cameras: cameras = self.__check_validity__(cameras, 'camera', VALID_CAMERAS, VALID_CAMERAS)

    import collections
    if(model_ids is None):
      model_ids = ()
    elif(not isinstance(model_ids,collections.Iterable)):
      model_ids = (model_ids,)

    # Now query the database
    retval = []
    if 'world' in groups:
      q = self.session.query(File).join(Client).join(ProtocolPurpose, File.protocol_purposes).join(Protocol).\
                  filter(and_(Protocol.name.in_(protocol), ProtocolPurpose.sgroup == 'world'))
      if subworld:
        q = q.join(Subworld, Client.subworld).filter(Subworld.name.in_(subworld))
      if expressions:
        q = q.join(Expression).filter(Expression.name.in_(expressions))
      if cameras:
        q = q.join(FileMultiview).join(Camera).filter(Camera.name.in_(cameras))
      if(world_nshots):
        max1 = 19
        max2 = 19
        max3 = 19
        max4 = 19
        if world_nshots < 19:
          max1 = world_nshots
          max2 = 0
          max3 = 0
          max4 = 0
        elif world_nshots < 38:
          max2 = world_nshots - 19
          max3 = 0
          max4 = 0
        elif world_nshots < 57:
          max3 = world_nshots - 38
          max4 = 0
        else:
          max4 = world_nshots - 57
        q = q.filter(or_( and_( File.session_id == Client.first_session, or_(and_(File.recording_id == 1, FileMultiview.shot_id < max1),
                                                                             and_(File.recording_id == 2, FileMultiview.shot_id < max2))),
                          and_( File.session_id == Client.second_session, or_(and_(File.recording_id == 1, FileMultiview.shot_id < max2),
                                                                              and_(File.recording_id == 2, FileMultiview.shot_id < max3))),
                          and_( File.session_id == Client.third_session, or_(and_(File.recording_id == 1, FileMultiview.shot_id < max3),
                                                                             and_(File.recording_id == 2, FileMultiview.shot_id < max4))),
                          and_( File.session_id == Client.fourth_session, FileMultiview.shot_id < max4)))
      if(world_shots):
        q = q.filter(FileMultiview.shot_id.in_(world_shots))
      if( world_sampling != 1 and world_noflash == False):
        q = q.filter(((File.client_id + FileMultiview.shot_id) % world_sampling) == 0)
      if( world_noflash == True):
        q = q.filter(FileMultiview.shot_id == 0)
      if( world_first == True):
        q = q.filter(and_(File.session_id == Client.first_session, or_(Client.first_session != 4,
                  and_(Client.first_session == 4, File.recording_id == 1))))
      if( world_second == True):
        q = q.filter(or_( and_(Client.second_session != 4, File.session_id == Client.second_session),
                          or_( and_(Client.first_session == 4, and_(File.session_id == 4, File.recording_id == 2)),
                               and_(Client.second_session == 4, and_(File.session_id == 4, File.recording_id == 1)))))
      if( world_third == True):
        q = q.filter(or_( and_(Client.third_session != 4, File.session_id == Client.third_session),
                          or_( and_(Client.second_session == 4, and_(File.session_id == 4, File.recording_id == 2)),
                               and_(Client.third_session == 4, and_(File.session_id == 4, File.recording_id == 1)))))
      if( world_fourth == True):
        q = q.filter(or_( and_(Client.fourth_session != 4, File.session_id == Client.fourth_session),
                          or_( and_(Client.third_session == 4, and_(File.session_id == 4, File.recording_id == 2)),
                               and_(Client.fourth_session == 4, and_(File.session_id == 4, File.recording_id == 1)))))
      if model_ids:
        q = q.filter(Client.id.in_(model_ids))
      q = q.order_by(File.client_id, File.session_id, File.recording_id, File.id)
      retval += list(q)

    if ('dev' in groups or 'eval' in groups):
      if('enrol' in purposes):
        q = self.session.query(File).join(Client).join(ProtocolPurpose, File.protocol_purposes).join(Protocol).\
              filter(and_(Protocol.name.in_(protocol), ProtocolPurpose.sgroup.in_(groups), ProtocolPurpose.purpose == 'enrol'))
        if expressions:
          q = q.join(Expression).filter(Expression.name.in_(expressions))
        if cameras:
          q = q.join(FileMultiview).join(Camera).filter(Camera.name.in_(cameras))
        if model_ids:
          q = q.filter(Client.id.in_(model_ids))
        q = q.order_by(File.client_id, File.session_id, File.recording_id, File.id)
        retval += list(q)

      if('probe' in purposes):
        if('client' in classes):
          q = self.session.query(File).join(Client).join(ProtocolPurpose, File.protocol_purposes).join(Protocol).\
                filter(and_(Protocol.name.in_(protocol), ProtocolPurpose.sgroup.in_(groups), ProtocolPurpose.purpose == 'probe'))
          if expressions:
            q = q.join(Expression).filter(Expression.name.in_(expressions))
          if cameras:
            q = q.join(FileMultiview).join(Camera).filter(Camera.name.in_(cameras))
          if model_ids:
            q = q.filter(Client.id.in_(model_ids))
          q = q.order_by(File.client_id, File.session_id, File.recording_id, File.id)
          retval += list(q)

        if('impostor' in classes):
          q = self.session.query(File).join(Client).join(ProtocolPurpose, File.protocol_purposes).join(Protocol).\
                filter(and_(Protocol.name.in_(protocol), ProtocolPurpose.sgroup.in_(groups), ProtocolPurpose.purpose == 'probe'))
          if expressions:
            q = q.join(Expression).filter(Expression.name.in_(expressions))
          if cameras:
            q = q.join(FileMultiview).join(Camera).filter(Camera.name.in_(cameras))
          if len(model_ids) == 1:
            q = q.filter(not_(Client.id.in_(model_ids)))
          q = q.order_by(File.client_id, File.session_id, File.recording_id, File.id)
          retval += list(q)

    return list(set(retval)) # To remove duplicates

  def tobjects(self, protocol=None, model_ids=None, groups=None, expressions=None):
    """Returns a set of filenames for enrolling T-norm models for score
       normalization.

    Keyword Parameters:

    protocol
      One of the Multi-PIE protocols (use protocol_names() to get the list of
      available ones)

    model_ids
      Only retrieves the files for the provided list of model ids (claimed
      client id).  If 'None' is given (this is the default), no filter over
      the model_ids is performed.

    groups
      The groups to which the clients belong ('dev', 'eval').

    expressions
      The (face) expressions to be retrieved (use expression_names() to get the
      list of expressions) or a tuple with several of them.
      If 'None' is given (this is the default), it is considered the same as
      a tuple with all possible values. Notice that some protocols only contain
      images with 'neutral' expression.

    Returns: A list of Files with the given properties.
    """

    VALID_GROUPS = ('dev', 'eval')
    groups = self.__check_validity__(groups, "group", VALID_GROUPS, VALID_GROUPS)
    tgroups = []
    if 'dev' in groups:
      tgroups.append('eval')
    if 'eval' in groups:
      tgroups.append('dev')
    return self.objects(protocol, 'enrol', model_ids, tgroups, 'client', None, expressions)

  def zobjects(self, protocol=None, model_ids=None, groups=None, expressions=None):
    """Returns a set of filenames of impostors for Z-norm score normalization.

    Keyword Parameters:

    protocol
      One of the Multi-PIE protocols (use protocol_names() to get the list of
      available ones)

    model_ids
      Only retrieves the files for the provided list of model ids (client id).
      If 'None' is given (this is the default), no filter over the model_ids
      is performed.

    groups
      The groups to which the clients belong ('dev', 'eval').

    expressions
      The (face) expressions to be retrieved (use expression_names() to get the
      list of expressions) or a tuple with several of them.
      If 'None' is given (this is the default), it is considered the same as
      a tuple with all possible values. Notice that some protocols only contain
      images with 'neutral' expression.

    Returns: A list of Files with the given properties.
    """

    VALID_GROUPS = ('dev', 'eval')
    groups = self.__check_validity__(groups, "group", VALID_GROUPS, VALID_GROUPS)

    zgroups = []
    if 'dev' in groups:
      zgroups.append('eval')
    if 'eval' in groups:
      zgroups.append('dev')
    return self.objects(protocol, 'probe', model_ids, zgroups, 'client', None, expressions)

  def protocol_names(self):
    """Returns all registered protocol names"""

    self.assert_validity()
    l = self.protocols()
    retval = [str(k.name) for k in l]
    return retval

  def protocols(self):
    """Returns all registered protocols"""

    self.assert_validity()
    return list(self.session.query(Protocol))

  def has_protocol(self, name):
    """Tells if a certain protocol is available"""

    self.assert_validity()
    return self.session.query(Protocol).filter(Protocol.name==name).count() != 0

  def protocol(self, name):
    """Returns the protocol object in the database given a certain name. Raises
    an error if that does not exist."""

    self.assert_validity()
    return self.session.query(Protocol).filter(Protocol.name==name).one()

  def protocol_purposes(self):
    """Returns all registered protocol purposes"""

    self.assert_validity()
    return list(self.session.query(ProtocolPurpose))

  def purposes(self):
    """Returns the list of allowed purposes"""

    return ProtocolPurpose.purpose_choices

  def paths(self, ids, prefix='', suffix=''):
    """Returns a full file paths considering particular file ids, a given
    directory and an extension

    Keyword Parameters:

    id
      The ids of the object in the database table "file". This object should be
      a python iterable (such as a tuple or list).

    prefix
      The bit of path to be prepended to the filename stem

    suffix
      The extension determines the suffix that will be appended to the filename
      stem.

    Returns a list (that may be empty) of the fully constructed paths given the
    file ids.
    """

    self.assert_validity()

    fobj = self.session.query(File).filter(File.id.in_(ids))
    retval = []
    for p in ids:
      retval.extend([k.make_path(prefix, suffix) for k in fobj if k.id == p])
    return retval

  def reverse(self, paths):
    """Reverses the lookup: from certain stems, returning file ids

    Keyword Parameters:

    paths
      The filename stems I'll query for. This object should be a python
      iterable (such as a tuple or list)

    Returns a list (that may be empty).
    """

    self.assert_validity()

    fobj = self.session.query(File).filter(File.path.in_(paths))
    for p in paths:
      retval.extend([k.id for k in fobj if k.path == p])
    return retval

