#!/usr/bin/env python
# encoding: utf-8
# Guillaume HEUSCH <guillaume.heusch@idiap.ch>
# Mon 24 Apr 09:35:40 CEST 2017

""" Run face cropping on the Multi Pie database (%(version)s) 

Usage:
  %(prog)s --basedir=<path> --croppeddir=<path>
           [--log=<string>] [--gridcount] 
           [--verbose ...] [--plot]

Options:
  -h, --help                Show this screen.
  -V, --version             Show version.
  -b, --basedir=<path>      Base dir containing the images.
  -c, --croppeddir=<path>   Where to store results.
  -l, --log=<string>        Log filename [default: log_face_detect.txt]
  -G, --gridcount           Display the number of objects and exits.
  -v, --verbose             Increase the verbosity (may appear multiple times).
  -P, --plot                Show some stuff

Example:

  To run the face cropping process

    $ %(prog)s --croppeddir path/to/cropped

See '%(prog)s --help' for more information.

"""

import os
import sys
import pkg_resources

import logging
__logging_format__='[%(levelname)s] %(message)s'
logging.basicConfig(format=__logging_format__)
logger = logging.getLogger("face_crop_log")

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
  
  Main function to crop faces in Multi Pie frontal images 

  """

  # Parse the command-line arguments
  if user_input is not None:
      arguments = user_input
  else:
      arguments = sys.argv[1:]

  prog = os.path.basename(sys.argv[0])
  completions = dict(prog=prog, version=version,)
  args = docopt(__doc__ % completions,argv=arguments,version='Face cropping (%s)' % version,)

  # if the user wants more verbosity, lowers the logging level
  if args['--verbose'] == 1: logging.getLogger("face_crop_log").setLevel(logging.INFO)
  elif args['--verbose'] >= 2: logging.getLogger("face_crop_log").setLevel(logging.DEBUG)

 
  # === collect the objects to process ===
  
  # the database
  annotations_dir = "/idiap/group/biometric/annotations/multipie"
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


  # === the face cropper ===
  CROPPED_IMAGE_HEIGHT = 64
  CROPPED_IMAGE_WIDTH = 64 
  RIGHT_EYE_POS = (CROPPED_IMAGE_HEIGHT // 5, CROPPED_IMAGE_WIDTH // 4 - 1)
  LEFT_EYE_POS = (CROPPED_IMAGE_HEIGHT // 5, CROPPED_IMAGE_WIDTH // 4 * 3)
  face_cropper = FaceCrop(cropped_image_size=(CROPPED_IMAGE_HEIGHT, CROPPED_IMAGE_WIDTH),
                                              cropped_positions={'leye': LEFT_EYE_POS, 'reye': RIGHT_EYE_POS},
                                              color_channel='rgb',
                                              dtype='uint8'
                                              )

  for obj in objs:
 
    # get the camera name
    camera = to_process[obj.path][1]
    logger.info("Processing file {0} (camera {1})".format(obj.path, camera))

    # the resulting filename
    temp = os.path.split(obj.path)
    cropped_filename = os.path.join(args['--croppeddir'], camera_to_pose[camera], temp[1])
    cropped_filename += '.png'
     
    # skip if the file exists
    if os.path.isfile(cropped_filename):
      logger.warn("{0} already exists !".format(cropped_filename))
      continue
      
    # get the original image
    img_file = os.path.join(args['--basedir'], obj.path)
    img_file += ".png"
    image = bob.io.base.load(img_file) 

    # get the annotations 
    annotations = db.annotations(obj)

    if bool(args['--plot']):
      from matplotlib import pyplot
      display = numpy.copy(image)
      annot_int = {}
      for key in annotations:
        annot_int[key] = (int(annotations[key][0]), int(annotations[key][1])) 
        bob.ip.draw.cross(display, annot_int[key], 3, (0, 255, 0))
      pyplot.imshow(numpy.rollaxis(numpy.rollaxis(display, 2),2))
      pyplot.show()

    # if this is a profile, infer position to perform the cropping
    if len(annotations) == 6:

      dist = numpy.linalg.norm(numpy.array(annotations['eye']) - numpy.array(annotations['nose']))
      eyes_dist = dist / 1.618 
      
      annotations_new = {}
      annotations_new['leye'] =  (int(annotations['eye'][0]), int(annotations['eye'][1] + eyes_dist))
      annotations_new['reye'] =  (int(annotations['eye'][0]), int(annotations['eye'][1] - eyes_dist))
      annotations_new['leye'] =  (int(annotations['eye'][0]), int(annotations['eye'][1] + eyes_dist))
      annotations_new['reye'] =  (int(annotations['eye'][0]), int(annotations['eye'][1] - eyes_dist))
      annotations = annotations_new

      if bool(args['--plot']):
        for key in annotations_new:
          bob.ip.draw.cross(display, annotations_new[key], 3, (255, 0, 0))
        pyplot.imshow(numpy.rollaxis(numpy.rollaxis(display, 2),2))
        pyplot.show()

    cropped = face_cropper(image, annotations)
        
    if bool(args['--plot']):
      from matplotlib import pyplot
      pyplot.imshow(numpy.rollaxis(numpy.rollaxis(cropped, 2),2))
      pyplot.show()
 
    if not os.path.isdir(os.path.dirname(cropped_filename)):
      os.makedirs(os.path.dirname(cropped_filename))
    bob.io.base.save(cropped, cropped_filename)
