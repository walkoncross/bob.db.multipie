#!/usr/bin/env python
# encoding: utf-8
# Guillaume HEUSCH <guillaume.heusch@idiap.ch>
# Mon 24 Apr 09:35:40 CEST 2017

""" Run face cropping on the Multi Pie database (%(version)s) 

Usage:
  %(prog)s <basedir> <croppeddir> 
           [--width=<int>] [--height=<int>] [--gray]
           [--force] [--gridcount] [--cluster] 
           [--verbose ...] [--show]

Options:
  -h, --help                Show this screen.
  -V, --version             Show version.
      --height=<int>        Height of the cropped image [default: 96]. 
      --width=<int>         Width of the cropped image [default: 96]. 
  -g, --gray                Convert to grayscale.
  -f, --force               Overwrite existing cropped image files.
  -G, --gridcount           Display the number of objects and exits.
  -c, --cluster             Cluster the cropped face images by pose.
  -v, --verbose             Increase the verbosity (may appear multiple times).
  -s, --show                Show some stuff.

Example:

  To run the face cropping process

    $ %(prog)s path/to/orignal/data path/to/cropped

See '%(prog)s --help' for more information.

"""

import os
import sys
import pkg_resources

from docopt import docopt

version = pkg_resources.require('bob.db.multipie')[0].version

import numpy
import math

import bob.io.base
import bob.io.image
import bob.bio.face
import bob.db.multipie
import bob.ip.facedetect
import bob.ip.draw

import bob.core
logger = bob.core.log.setup("bob.db.multipie")

from bob.bio.face.preprocessor import FaceCrop, FaceDetect

import gridtk

def filter_for_sge_task(l):
  '''Breaks down a list of objects as per SGE task requirements'''

  # identify which task I am running on
  task_id = int(os.environ['SGE_TASK_ID'])
  logger.debug('SGE_TASK_ID=%d' % task_id)
  task_first = int(os.environ['SGE_TASK_FIRST'])
  logger.debug('SGE_TASK_FIRST=%d' % task_first)
  task_last = int(os.environ['SGE_TASK_LAST'])
  logger.debug('SGE_TASK_LAST=%d' % task_last)
  task_step = int(os.environ['SGE_TASK_STEPSIZE'])
  logger.debug('SGE_TASK_STEPSIZE=%d' % task_step)

  # build a list of tasks, like the SGE manager has
  tasks = list(range(task_first, task_last+1, task_step))

  # creates an array with the limits of each task
  length = len(l)
  limits = list(range(0, length, int(math.ceil(float(length)/len(tasks)))))

  # get the index of the slot for the given task id
  task_index = tasks.index(task_id)

  # yields only the elements for the current slot
  if task_id != tasks[-1]: # not the last
    logger.info('[SGE task %d/%d] Returning entries %d:%d out of %d samples',
        task_index+1, len(tasks), limits[task_index], limits[task_index+1],
        len(l))
    return l[limits[task_index]:limits[task_index+1]]
  else: # it is the last
    logger.info('[SGE: task %d/%d] Returning entries %d:%d out of %d samples',
        task_index+1, len(tasks), limits[task_index], len(l), len(l))
    return l[limits[task_index]:]


def main(user_input=None):
  """
  
  Main function to crop faces in Multi Pie images 

  """
  # Parse the command-line arguments
  if user_input is not None:
      arguments = user_input
  else:
      arguments = sys.argv[1:]

  prog = os.path.basename(sys.argv[0])
  completions = dict(prog=prog, version=version,)
  args = docopt(__doc__ % completions,argv=arguments,version='Face cropping (%s)' % version,)

  # set verbosity level 
  bob.core.log.set_verbosity_level(logger, args['--verbose'])
  
  # === collect the objects to process ===
  
  # the database
  annotations_dir = "/idiap/group/biometric/annotations/multipie"
  if not os.path.isdir(annotations_dir):
    logger.error("You should provide a directory containing annotations !")
    sys.exit()

  db = bob.db.multipie.Database(annotation_directory = annotations_dir) 
  
  # dict with the file stem as key and the (File, camera name) as value
  to_process = {}
  for camera in sorted(db.camera_names()):
    
    objs = db.objects(cameras=camera)
    if (camera == '19_1') or (camera == '08_1'):
      continue

    for obj in objs:
      to_process[obj.path] = (obj, camera)
 
  # create the list of objects for the grid
  objs = []
  for name in to_process.keys():
    objs.append(to_process[name][0])

  # if we are on a grid environment, just find what I have to process.
  if os.environ.has_key('SGE_TASK_ID'):
    objs = filter_for_sge_task(objs)

  if args['--gridcount']:
    print len(objs)
    sys.exit()

  # dict to map cameras to pose
  camera_to_pose = {'11_0': 'l90',
                    '12_0': 'l75',
                    '09_0': 'l60',
                    '08_0': 'l45',
                    '13_0': 'l30',
                    '14_0': 'l15',
                    '05_1': '0',
                    '05_0': 'r15',
                    '04_1': 'r30',
                    '19_0': 'r45',
                    '20_0': 'r60',
                    '01_0': 'r75',
                    '24_0': 'r90',
                   }
  
  color_channel = 'rgb'
  if bool(args['--gray']):
    color_channel = 'gray'


  # === the face croppers ===
  # 
  # This have been done to be compliant with bob.chapter.FRICE
  #
  # - 3 croppers: frontal, left and right
  #
  # - cropped image size is hard-coded 
  # - position of eyes (and mouth) in cropped images are hard-coded
  #   (this should maybe change in the future)
  #

  # frontal face cropper
  CROPPED_IMAGE_HEIGHT = 96 
  CROPPED_IMAGE_WIDTH = 96

  cropped_positions_frontal =  {"reye": (19, 22), "leye" : (19, 72)}
  cropped_positions_left = cropped_positions={"eye" : (19, 37), "mouth": (62, 37)}
  cropped_positions_right = cropped_positions={"eye" : (19, 57), "mouth": (62, 57)}


  face_cropper_frontal = FaceCrop(cropped_image_size=(CROPPED_IMAGE_HEIGHT, CROPPED_IMAGE_WIDTH),
                                  cropped_positions=cropped_positions_frontal,
                                  color_channel=color_channel,
                                  dtype='uint8')
  
  face_cropper_left = FaceCrop(cropped_image_size=(CROPPED_IMAGE_HEIGHT, CROPPED_IMAGE_WIDTH),
                               cropped_positions=cropped_positions_left,
                               color_channel=color_channel,
                               dtype='uint8')

  face_cropper_right = FaceCrop(cropped_image_size=(CROPPED_IMAGE_HEIGHT, CROPPED_IMAGE_WIDTH),
                                cropped_positions=cropped_positions_right,
                                color_channel=color_channel,
                                dtype='uint8')

  # cameras
  cam_frontal = ('19_0', '04_1', '05_0', '05_1', '13_0', '14_0', '08_0')
  cam_left = ('09_0', '11_0', '12_0')
  cam_right = ('24_0', '01_0', '20_0')

  # LET'S GO
  for obj in objs:
 
    # get the camera name
    camera = to_process[obj.path][1]
    logger.info("Processing file {0} (camera {1})".format(obj.path, camera))

    # the resulting filename
    cropped_filename = obj.make_path(directory=args['<croppeddir>'], extension='.png')
    if bool(args['--cluster']):
      temp = os.path.split(obj.path)
      cropped_filename = os.path.join(args['<croppeddir>'], camera_to_pose[camera], temp[1])
      cropped_filename += '.png'
     
    # skip if the file exists
    if os.path.isfile(cropped_filename) and not args['--force']:
      logger.warn("{0} already exists !".format(cropped_filename))
      continue
      
    # get the original image
    img_filename = obj.make_path(directory=args['<basedir>'], extension='.png')
    image = bob.io.base.load(img_filename) 

    # get the annotations 
    annotations = db.annotations(obj)

    if bool(args['--show']):
      from matplotlib import pyplot
      display = numpy.copy(image)
      annot_int = {}
      for key in annotations:
        annot_int[key] = (int(annotations[key][0]), int(annotations[key][1])) 
        bob.ip.draw.cross(display, annot_int[key], 3, (0, 255, 0))
      pyplot.imshow(numpy.rollaxis(numpy.rollaxis(display, 2),2))
      pyplot.show()

    # check which cropper has to be called
    if camera in cam_frontal:
      cropped = face_cropper_frontal(image, annotations)
    if camera in cam_left:
      cropped = face_cropper_left(image, annotations)
    if camera in cam_right:
      cropped = face_cropper_right(image, annotations)
    
    if bool(args['--show']):
      from matplotlib import pyplot
      if color_channel == 'rgb':
        pyplot.imshow(numpy.rollaxis(numpy.rollaxis(cropped, 2),2))
      else:
        pyplot.imshow(cropped, cmap='gray')
      pyplot.show()

    # save the cropped image
    bob.io.base.save(cropped, cropped_filename, create_directories=True)
