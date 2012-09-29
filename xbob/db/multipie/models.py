#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Laurent El Shafey <laurent.el-shafey@idiap.ch>

"""Table models and functionality for the Multi-PIE database.
"""

import os, numpy
import bob.db.utils
from sqlalchemy import Table, Column, Integer, String, ForeignKey, or_, and_, not_
from bob.db.sqlalchemy_migration import Enum, relationship
from sqlalchemy.orm import backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

subworld_client_association = Table('subworld_client_association', Base.metadata,
  Column('subworld_id', Integer, ForeignKey('subworld.id')),
  Column('client_id',  Integer, ForeignKey('client.id')))

protocolPurpose_file_association = Table('protocolPurpose_file_association', Base.metadata,
  Column('protocolPurpose_id', Integer, ForeignKey('protocolPurpose.id')),
  Column('file_id',  Integer, ForeignKey('file.id')))

class Client(Base):
  """Database clients, marked by an integer identifier and the group they belong to"""

  __tablename__ = 'client'

  # Key identifier for the client
  id = Column(Integer, primary_key=True)
  # Group to which the client belongs to
  group_choices = ('dev', 'eval', 'world')
  sgroup = Column(Enum(*group_choices))
  # Birthyear of the client
  birthyear = Column(Integer)
  # Gender to which the client belongs to
  gender_choices = ('male','female')
  gender = Column(Enum(*gender_choices))
  first_session = Column(Integer)
  second_session = Column(Integer)
  third_session = Column(Integer)
  fourth_session = Column(Integer)

  def __init__(self, id, group, birthyear, gender, first_session, second_session, third_session, fourth_session):
    self.id = id
    self.sgroup = group
    self.birthyear = birthyear
    self.gender = gender
    self.first_session = first_session
    self.second_session = second_session
    self.third_session = third_session
    self.fourth_session = fourth_session

  def __repr__(self):
    return "Client(%d, '%s')" % (self.id, self.sgroup)

class Subworld(Base):
  """Database clients belonging to the world group are split in two disjoint subworlds, 
     onethird and twothirds"""

  __tablename__ = 'subworld'
  
  # Key identifier for this Subworld object
  id = Column(Integer, primary_key=True)
  # Subworld to which the client belongs to
  name = Column(String(20), unique=True)
  
  # for Python: A direct link to the client
  clients = relationship("Client", secondary=subworld_client_association, backref=backref("subworld", order_by=id))

  def __init__(self, name):
    self.name = name

  def __repr__(self):
    return "Subworld('%s')" % (self.name)

class File(Base):
  """Generic file container"""

  __tablename__ = 'file'

  # Key identifier for the file
  id = Column(Integer, primary_key=True)
  # Key identifier of the client associated with this file
  client_id = Column(Integer, ForeignKey('client.id')) # for SQL
  # Unique path to this file inside the database
  path = Column(String(100), unique=True)
  # Identifier of the session
  session_id = Column(Integer)
  # Identifier of the recording
  recording_id = Column(Integer)
  # Image type
  imagetype_choices = ('multiview', 'highres')
  img_type = Column(Enum(*imagetype_choices))
  # Identifier of the expression
  expression_id = Column(Integer, ForeignKey('expression.id'))

  # for Python
  client = relationship("Client", backref=backref("files", order_by=id))

  def __init__(self, client_id, path, session_id, recording_id, img_type, expression_id):
    self.client_id = client_id
    self.path = path
    self.session_id = session_id
    self.recording_id = recording_id
    self.img_type = img_type
    self.expression_id = expression_id

  def __repr__(self):
    return "File('%s')" % self.path

  def make_path(self, directory=None, extension=None):
    """Wraps the current path so that a complete path is formed

    Keyword parameters:

    directory
      An optional directory name that will be prefixed to the returned result.

    extension
      An optional extension that will be suffixed to the returned filename. The
      extension normally includes the leading ``.`` character as in ``.jpg`` or
      ``.hdf5``.

    Returns a string containing the newly generated file path.
    """

    if not directory: directory = ''
    if not extension: extension = ''

    return os.path.join(directory, self.path + extension)

  def save(self, data, directory=None, extension='.hdf5'):
    """Saves the input data at the specified location and using the given
    extension.

    Keyword parameters:

    data
      The data blob to be saved (normally a :py:class:`numpy.ndarray`).

    directory
      If not empty or None, this directory is prefixed to the final file
      destination

    extension
      The extension of the filename - this will control the type of output and
      the codec for saving the input blob.
    """

    path = self.make_path(directory, extension)
    bob.utils.makedirs_safe(os.path.dirname(path))
    bob.io.save(data, path)

class FileMultiview(Base):
  """Additional file information for multiview-like files"""

  __tablename__ = 'fileMultiview'

  # Key identifier for the file multiview
  id = Column(Integer, ForeignKey('file.id'), primary_key=True) # for SQL
  # Identifier of the shot
  shot_id = Column(Integer)
  # Identifier of the camera
  camera_id = Column(Integer, ForeignKey('camera.id'))

  # for Python
  file = relationship("File", uselist=False, backref=backref("file_multiview", uselist=False, order_by=id))

  def __init__(self, file_id, shot_id, camera_id):
    self.id = file_id
    self.shot_id = shot_id
    self.camera_id = camera_id

  def __repr__(self):
    return "FileMultiview('%s')" % (self.file.path)

class Expression(Base):
  """Multi-PIE expressions"""

  __tablename__ = 'expression'
  
  id = Column(Integer, primary_key=True)
  name = Column(String(20), unique=True)

  # for Python: A direct link to the files with this expression
  files = relationship("File", backref=backref("expression", order_by=id))

  def __init__(self, name):
    self.name = name

  def __repr__(self):
    return "Expression('%s')" % (self.name)

class Camera(Base):
  """Multi-PIE cameras"""

  __tablename__ = 'camera'
  
  id = Column(Integer, primary_key=True)
  name = Column(String(10), unique=True)

  # for Python: A direct link to the files (multiview) recorded with this camera
  files_multiview = relationship("FileMultiview", backref=backref("camera", order_by=id))

  def __init__(self, name):
    self.name = name

  def __repr__(self):
    return "Camera('%s')" % (self.name)

class Protocol(Base):
  """Multi-PIE protocols"""

  __tablename__ = 'protocol'

  # Unique identifier for this protocol object
  id = Column(Integer, primary_key=True)
  # Name of the protocol associated with this object
  name = Column(String(20), unique=True)

  def __init__(self, name):
    self.name = name

  def __repr__(self):
    return "Protocol('%s')" % (self.name,)

class ProtocolPurpose(Base):
  """Multi-PIE protocol purposes"""

  __tablename__ = 'protocolPurpose'

  # Unique identifier for this protocol purpose object
  id = Column(Integer, primary_key=True)
  # Id of the protocol associated with this protocol purpose object
  protocol_id = Column(Integer, ForeignKey('protocol.id')) # for SQL
  # Group associated with this protocol purpose object
  group_choices = Client.group_choices
  sgroup = Column(Enum(*group_choices))
  # Purpose associated with this protocol purpose object
  purpose_choices = ('train', 'enrol', 'probe')
  purpose = Column(Enum(*purpose_choices))

  # For Python: A direct link to the Protocol object that this ProtocolPurpose belongs to
  protocol = relationship("Protocol", backref=backref("purposes", order_by=id))
  # For Python: A direct link to the File objects associated with this ProtcolPurpose
  files = relationship("File", secondary=protocolPurpose_file_association, backref=backref("protocol_purposes", order_by=id))

  def __init__(self, protocol_id, sgroup, purpose):
    self.protocol_id = protocol_id
    self.sgroup = sgroup
    self.purpose = purpose

  def __repr__(self):
    return "ProtocolPurpose('%s', '%s', '%s')" % (self.protocol.name, self.sgroup, self.purpose)

