import os
import copy
from random import shuffle
import itertools

import numpy as np

from unet3d.utils import pickle_dump, pickle_load
from unet3d.utils.patches import compute_patch_indices, get_random_nd_index, get_patch_from_3d_data
from unet3d.augment import augment_data, random_permutation_x_y



def get_training_and_validation_generators(data_file0, data_file1, batch_size, n_labels, training_keys_file, validation_keys_file,
                                           data_split=0.8, overwrite=False, labels=None, augment=False,
                                           augment_flip=True, augment_distortion_factor=0.25, patch_shape=None,
                                           validation_patch_overlap=0, training_patch_start_offset=None,
                                           validation_batch_size=None, skip_blank=True, permute=False):
    """
    Creates the training and validation generators that can be used when training the model.
    :param skip_blank: If True, any blank (all-zero) label images/patches will be skipped by the data generator.
    :param validation_batch_size: Batch size for the validation data.
    :param training_patch_start_offset: Tuple of length 3 containing integer values. Training data will randomly be
    offset by a number of pixels between (0, 0, 0) and the given tuple. (default is None)
    :param validation_patch_overlap: Number of pixels/voxels that will be overlapped in the validation data. (requires
    patch_shape to not be None)
    :param patch_shape: Shape of the data to return with the generator. If None, the whole image will be returned.
    (default is None)
    :param augment_flip: if True and augment is True, then the data will be randomly flipped along the x, y and z axis
    :param augment_distortion_factor: if augment is True, this determines the standard deviation from the original
    that the data will be distorted (in a stretching or shrinking fashion). Set to None, False, or 0 to prevent the
    augmentation from distorting the data in this way.
    :param augment: If True, training data will be distorted on the fly so as to avoid over-fitting.
    :param labels: List or tuple containing the ordered label values in the image files. The length of the list or tuple
    should be equal to the n_labels value.
    Example: (10, 25, 50)
    The data generator would then return binary truth arrays representing the labels 10, 25, and 30 in that order.
    :param data_file: hdf5 file to load the data from.
    :param batch_size: Size of the batches that the training generator will provide.
    :param n_labels: Number of binary labels.
    :param training_keys_file: Pickle file where the index locations of the training data will be stored.
    :param validation_keys_file: Pickle file where the index locations of the validation data will be stored.
    :param data_split: How the training and validation data will be split. 0 means all the data will be used for
    validation and none of it will be used for training. 1 means that all the data will be used for training and none
    will be used for validation. Default is 0.8 or 80%.
    :param overwrite: If set to True, previous files will be overwritten. The default mode is false, so that the
    training and validation splits won't be overwritten when rerunning model training.
    :param permute: will randomly permute the data (data must be 3D cube)
    :return: Training data generator, validation data generator, number of training steps, number of validation steps
    """
    if not validation_batch_size:
        validation_batch_size = batch_size

    training_list, validation_list = get_validation_split(data_file0,
                                                          data_split=data_split,
                                                          overwrite=overwrite,
                                                          training_file=training_keys_file,
                                                          validation_file=validation_keys_file)

    training_generator = data_generator(data_file0, data_file1, training_list,
                                        batch_size=batch_size,
                                        n_labels=n_labels,
                                        labels=labels,
                                        augment=augment,
                                        augment_flip=augment_flip,
                                        augment_distortion_factor=augment_distortion_factor,
                                        patch_shape=patch_shape,
                                        patch_overlap=0,
                                        patch_start_offset=training_patch_start_offset,
                                        shuffle_index_list=True,
                                        skip_blank=skip_blank,
                                        permute=permute)
    validation_generator = data_generator(data_file0, data_file1, validation_list,
                                          batch_size=validation_batch_size,
                                          n_labels=n_labels,
                                          labels=labels,
                                          patch_shape=patch_shape,
                                          patch_overlap=validation_patch_overlap,
                                          skip_blank=skip_blank)

    # Set the number of training and testing samples per epoch correctly
    num_training_steps = get_number_of_steps(get_number_of_patches(data_file0, training_list, patch_shape,
                                                                   skip_blank=skip_blank,
                                                                   patch_start_offset=training_patch_start_offset,
                                                                   patch_overlap=0), batch_size)
    print("Number of training steps: ", num_training_steps)

    num_validation_steps = get_number_of_steps(get_number_of_patches(data_file0, validation_list, patch_shape,
                                                                     skip_blank=skip_blank,
                                                                     patch_overlap=validation_patch_overlap),
                                               validation_batch_size)
    print("Number of validation steps: ", num_validation_steps)

    return training_generator, validation_generator, num_training_steps, num_validation_steps


def get_number_of_steps(n_samples, batch_size):
    if n_samples <= batch_size:
        return n_samples
    elif np.remainder(n_samples, batch_size) == 0:
        return n_samples//batch_size
    else:
        return n_samples//batch_size + 1


def get_validation_split(data_file, training_file, validation_file, data_split=0.8, overwrite=False):
    """
    Splits the data into the training and validation indices list.
    :param data_file: pytables hdf5 data file
    :param training_file:
    :param validation_file:
    :param data_split:
    :param overwrite:
    :return:
    """


    if overwrite or not os.path.exists(training_file):
        print("Creating validation split...")
        #nb_samples = data_file.root.data.shape[0]
        #sample_list = list(range(nb_samples))
        #training_list, validation_list = split_list(sample_list, split=data_split)

        test_listA  = list(range(10, 30))
        train_listA1  = list(range(0, 10))
        train_listA2  = list(range(30, 42))

        test_listB  = list(range(52, 72))
        train_listB1  = list(range(42, 52))
        train_listB2  = list(range(72, 239))

        test_listC  = list(range(249, 269))
        train_listC1  = list(range(239, 249))
        train_listC2  = list(range(269, 299))
    
        training_list = train_listA1 + train_listA2 + train_listB1 + train_listB2 + [train_listB2[-1]] + train_listC1 * 5 + train_listC2 * 5
        validation_list = test_listA + test_listB + test_listC

        shuffle(training_list)
        #shuffle(validation_list)
        pickle_dump(training_list, training_file)
        pickle_dump(validation_list, validation_file)
        return training_list, validation_list
    else:
        print("Loading previous validation split...")
        return pickle_load(training_file), pickle_load(validation_file)
    

def split_list(input_list, split=0.8, shuffle_list=True):
    if shuffle_list:
        shuffle(input_list)
    n_training = int(len(input_list) * split)
    training = input_list[:n_training]
    testing = input_list[n_training:]
    print (training)
    raise
    return training, testing


def data_generator(data_file0, data_file1, index_list, batch_size=1, n_labels=1, labels=None, augment=False, augment_flip=True,
                   augment_distortion_factor=0.25, patch_shape=None, patch_overlap=0, patch_start_offset=None,
                   shuffle_index_list=False, skip_blank=True, permute=False):
    orig_index_list = index_list
    while True:
        x_list = [[], []]
        y_list = [[], [], []]
        if patch_shape:
            index_list = create_patch_index_list(orig_index_list, data_file.root.data.shape[-3:], patch_shape,
                                                 patch_overlap, patch_start_offset)
        else:
            index_list = copy.copy(orig_index_list)

        if shuffle_index_list:
            shuffle(index_list)
        while len(index_list) > 0:
            index = index_list.pop()
            add_data(x_list, y_list, data_file0, data_file1, index, augment=augment, augment_flip=augment_flip,
                     augment_distortion_factor=augment_distortion_factor, patch_shape=patch_shape,
                     skip_blank=skip_blank, permute=permute)

            if len(y_list[0]) == batch_size or (len(index_list) == 0 and len(y_list[0]) > 0):
                yield convert_data(x_list, y_list, n_labels=n_labels, labels=labels)

                x_list = [[], []]
                y_list = [[], [], []]


def get_number_of_patches(data_file, index_list, patch_shape=None, patch_overlap=0, patch_start_offset=None,
                          skip_blank=True):
    if patch_shape:
        index_list = create_patch_index_list(index_list, data_file.root.data.shape[-3:], patch_shape, patch_overlap,
                                             patch_start_offset)
        count = 0
        for index in index_list:
            x_list = list()
            y_list = list()
            add_data(x_list, y_list, data_file, index, skip_blank=skip_blank, patch_shape=patch_shape)
            if len(x_list) > 0:
                count += 1
        return count
    else:
        return len(index_list)


def create_patch_index_list(index_list, image_shape, patch_shape, patch_overlap, patch_start_offset=None):
    patch_index = list()
    for index in index_list:
        if patch_start_offset is not None:
            random_start_offset = np.negative(get_random_nd_index(patch_start_offset))
            patches = compute_patch_indices(image_shape, patch_shape, overlap=patch_overlap, start=random_start_offset)
        else:
            patches = compute_patch_indices(image_shape, patch_shape, overlap=patch_overlap)
        patch_index.extend(itertools.product([index], patches))
    return patch_index


def add_data(x_list, y_list, data_file0, data_file1, index, augment=False, augment_flip=False, augment_distortion_factor=0.25,
             patch_shape=False, skip_blank=True, permute=False):
    """
    Adds data from the data file to the given lists of feature and target data
    :param skip_blank: Data will not be added if the truth vector is all zeros (default is True).
    :param patch_shape: Shape of the patch to add to the data lists. If None, the whole image will be added.
    :param x_list: list of data to which data from the data_file will be appended.
    :param y_list: list of data to which the target data from the data_file will be appended.
    :param data_file: hdf5 data file.
    :param index: index of the data file from which to extract the data.
    :param augment: if True, data will be augmented according to the other augmentation parameters (augment_flip and
    augment_distortion_factor)
    :param augment_flip: if True and augment is True, then the data will be randomly flipped along the x, y and z axis
    :param augment_distortion_factor: if augment is True, this determines the standard deviation from the original
    that the data will be distorted (in a stretching or shrinking fashion). Set to None, False, or 0 to prevent the
    augmentation from distorting the data in this way.
    :param permute: will randomly permute the data (data must be 3D cube)
    :return:
    """

    data0, truth0, label0 = get_data_from_file(data_file0, index, patch_shape=patch_shape)
    data1, truth1, label1 = get_data_from_file(data_file1, index, patch_shape=patch_shape)

    if label0 != label1:
        print ('label0 and label1 not equal !!!')
        print (label0)
        print (label1)
        raise

    if augment:
        if patch_shape is not None:
            affine0 = data_file0.root.affine[index[0]]
            affine1 = data_file1.root.affine[index[0]]
        else:
            affine0 = data_file0.root.affine[index]
            affine1 = data_file1.root.affine[index]
        data0, truth0, data1, truth1 = augment_data(data0, data1, truth0, truth1, affine0, affine1, flip=augment_flip, scale_deviation=augment_distortion_factor)

    if permute:
        if data.shape[-3] != data.shape[-2] or data.shape[-2] != data.shape[-1]:
            raise ValueError("To utilize permutations, data array must be in 3D cube shape with all dimensions having "
                             "the same length.")
        data, truth = random_permutation_x_y(data, truth[np.newaxis])
    else:
        truth0 = truth0[np.newaxis]
        truth1 = truth1[np.newaxis]

    if not skip_blank or (np.any(truth0 != 0) or np.any(truth1 != 0)):

        #data0_0_temp = data0[0,...]
        #data0_0 = data0_0_temp[None, ...]
        #data1_0_temp = data1[0,...]
        #data1_0 = data1_0_temp[None, ...]

        data0_0 = data0
        data1_0 = data1

        if data0_0.min() == data0_0.max():
            data0_0 = data0_0 - data0_0
        else:                
            data0_0 = (data0_0-data0_0.min())/(data0_0.max()-data0_0.min())

        if data1_0.min() == data1_0.max():
            data1_0 = data1_0 - data1_0
        else:                
            data1_0 = (data1_0-data1_0.min())/(data1_0.max()-data1_0.min())

        x_list[0].append(data0_0)
        x_list[1].append(data1_0)

        #x_list.append([data0, data1, truth0, truth1])
        y_list[0].append(label0)
        y_list[1].append(truth0)
        y_list[2].append(truth1)
    else:
        #print ('here')
        #print (np.any(truth0 != 0))
        #print (np.any(truth1 != 0))
        #raise
        pass

def get_data_from_file(data_file, index, patch_shape=None):
    if patch_shape:
        index, patch_index = index
        data, truth = get_data_from_file(data_file, index, patch_shape=None)
        x = get_patch_from_3d_data(data, patch_shape, patch_index)
        y = get_patch_from_3d_data(truth, patch_shape, patch_index)
    else:
        x, y = data_file.root.data[index], data_file.root.truth[index, 0]
        ids = data_file.root.subject_ids[index]
        ids = ids.decode()
        ids_AC = ids.split('-')[-1][0]
        if ids_AC == 'C':
            label = 1
        elif ids_AC == 'A' or ids_AC == 'B':
            label = 0
        else:
            print ('not A or B, C !!!')
            raise
    return x, y, label

'''
def convert_data(x_list, y_list, n_labels=1, labels=None):

    x = [np.asarray(i) for i in x_list]
    #x = np.asarray(x_list)
    #x = x_list
    #y = np.asarray(y_list)
    y = [np.asarray(i) for i in y_list]
    y[0] = list(y[0])

    if n_labels == 1:
        y[1][y[1] > 0] = 1
        y[2][y[2] > 0] = 1
    elif n_labels > 1:
        y = get_multi_class_labels(y, n_labels=n_labels, labels=labels)

    return x, y
'''

def convert_data(x_list, y_list, n_labels=1, labels=None):

    x = [np.asarray(i) for i in x_list]
    #x = np.asarray(x_list)
    #x = x_list
    #y = np.asarray(y_list)
    y = [np.asarray(i) for i in y_list]
    #y[0] = list(y[0])

    if n_labels == 1:
        y[1][y[1] > 0] = 1
        y[2][y[2] > 0] = 1
    elif n_labels > 1:
        y = get_multi_class_labels(y, n_labels=n_labels, labels=labels)
    
    #print (type(y[0]))
    #raise
    #return x[0], y[0]
    return x, y

def get_multi_class_labels(data, n_labels, labels=None):
    """
    Translates a label map into a set of binary labels.
    :param data: numpy array containing the label map with shape: (n_samples, 1, ...).
    :param n_labels: number of labels.
    :param labels: integer values of the labels.
    :return: binary numpy array of shape: (n_samples, n_labels, ...)
    """
    new_shape = [data.shape[0], n_labels] + list(data.shape[2:])
    y = np.zeros(new_shape, np.int8)
    for label_index in range(n_labels):
        if labels is not None:
            y[:, label_index][data[:, 0] == labels[label_index]] = 1
        else:
            y[:, label_index][data[:, 0] == (label_index + 1)] = 1
    return y
