import numpy
import pyculib

def nroot(array, n):
    """

    :param array:   A n dimensional numpy array by default. Of course this works
                    with single numbers and whatever the interpreter can understand
    :param n:       The root - a number
    :return:
    """
    return array ** (1.0 / n)


def normalize(array):
    """
    Normalizes a numpy array by dividing each element with the array.sum()

    :param array: a numpy.array
    :return:
    """
    return array / array.sum()


def float2dtype(float_type):
    """Return numpy float dtype object from float type label.
    """
    if float_type == 'single' or float_type is None:
        return numpy.float32
    if float_type == 'double':
        return numpy.float64
    raise NotImplementedError (`float_type`)


def contract_to_shape(data, shape):
    """
    Remove padding from input data array. The function
    expects the padding to be symmetric on all sides
    """
    assert shape <= data.shape

    if shape != data.shape:

        slices = []
        for s1, s2 in zip(data.shape, shape):
            slices.append(slice((s1 - s2) // 2, (s1 + s2) // 2))

        image = data[tuple(slices)]
    else:
        image = data

    return image

def expand_to_shape(data, shape, dtype=None, background=None):
    """
    Expand data to given shape by zero-padding.
    """
    if dtype is None:
        dtype = data.dtype

    start_index = numpy.array(shape) - data.shape
    data_start = numpy.negative(start_index.clip(max=0))
    data = cast_to_dtype(data, dtype, rescale=False)
    if data.ndim == 3:
        data = data[data_start[0]:, data_start[1]:, data_start[2]:]
    else:
        data = data[data_start[0]:, data_start[1]:]

    if background is None:
        background = 0

    if (shape != data.shape):
        expanded_data = numpy.zeros(shape, dtype=dtype) + background
        slices = []
        rhs_slices = []
        for s1, s2 in zip(shape, data.shape):
            a, b = (s1 - s2 + 1) // 2, (s1 + s2 + 1) // 2
            c, d = 0, s2
            while a < 0:
                a += 1
                b -= 1
                c += 1
                d -= 1
            slices.append(slice(a, b))
            rhs_slices.append(slice(c, d))
        try:
            expanded_data[tuple(slices)] = data[tuple(rhs_slices)]
        except ValueError:
            print data.shape, shape
            raise
        return expanded_data
    else:
        return data


def mul_seq(seq):
    return reduce(lambda x, y: x * y, seq, 1)


def float2dtype(float_type):
    """Return numpy float dtype object from float type label.
    """
    if float_type == 'single' or float_type is None:
        return numpy.float32
    if float_type == 'double':
        return numpy.float64
    raise NotImplementedError(`float_type`)

def cast_to_dtype(data, dtype, rescale=True, remove_outliers=False):
    """
     A function for casting a numpy array into a new data type.
    The .astype() property of Numpy sometimes produces satisfactory
    results, but if the data type to cast into has a more limited
    dynamic range than the original data type, problems may occur.

    :param data:            a numpy.array object
    :param dtype:           data type string, as in Python
    :param rescale:         switch to enable rescaling pixel
                            values to the new dynamic range.
                            This should always be enabled when
                            scaling to a more limited range,
                            e.g. from float to int
    :param remove_outliers: sometimes deconvolution/fusion generates
                            bright artifacts, which interfere with
                            the rescaling calculation. You can remove them
                            with this switch
    :return:                Returns the input data, cast into the new datatype
    """
    if data.dtype == dtype:
        return data

    if 'int' in str(dtype):
        data_info = numpy.iinfo(dtype)
        data_max = data_info.max
        data_min = data_info.min
    elif 'float' in str(dtype):
        data_info = numpy.finfo(dtype)
        data_max = data_info.max
        data_min = data_info.min
    else:
        data_max = data.max()
        data_min = data.min()
        print "Warning casting into unknown data type. Detail clipping" \
              "may occur"

    # In case of unsigned integers, numbers below zero need to be clipped
    if 'uint' in str(dtype):
        data_max = 255
        data_min = 0

    if remove_outliers:
        data = data.clip(0, numpy.percentile(data, 99.99))

    if rescale is True:
        return rescale_to_min_max(data, data_min, data_max).astype(dtype)
    else:
        return data.clip(data_min, data_max).astype(dtype)


def rescale_to_min_max(data, data_min, data_max):
    """
    A function to rescale image intensities to range, define by
    data_min and data_max input parameters.

    :param data:        Input image (Numpy array)
    :param data_min:    Minimum pixel value. Can be any type of a number
                        (preferably of the same type with the data.dtype)
    :param data_max:    Maximum pixel value
    :return:            Return the rescaled array
    """
    # Return array with max value in the original image scaled to correct
    # range
    if abs(data.max()) > abs(data.min()) or data_min == 0:
        return data_max / data.max() * data
    else:
        return data_min / data.min() * data


def fft(array, cuda=False): # type: (numpy.ndarray, bool) -> numpy.ndarray
    if cuda:
        return numpy.fft.fftshift(pyculib.fft_inplace(array.astype('complex64')))
    else:
        return numpy.fft.fftshift(numpy.fft.rfftn(array))


def safe_divide(numerator, denominator):
    """
    Division of numpy arrays that can handle division by zero. NaN results are
    coerced to zero. Also suppresses the division by zero warning.
    :param numerator:
    :param denominator:
    :return:
    """
    with numpy.errstate(divide="ignore"):
        result = numerator / denominator
        result[result == numpy.inf] = 0.0
        return numpy.nan_to_num(result)