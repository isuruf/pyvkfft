# -*- coding: utf-8 -*-

# PyVkFFT
#   (c) 2021- : ESRF-European Synchrotron Radiation Facility
#       authors:
#         Vincent Favre-Nicolin, favre@esrf.fr

import os
import platform
import sysconfig
import ctypes
import warnings
from enum import Enum
import numpy as np
from .config import USE_LUT

# np.complex32 does not exist yet https://github.com/numpy/numpy/issues/14753
complex32 = np.dtype([('re', np.float16), ('im', np.float16)])


class VkFFTResult(Enum):
    """ VkFFT error codes from vkFFT.h """
    VKFFT_SUCCESS = 0
    VKFFT_ERROR_MALLOC_FAILED = 1
    VKFFT_ERROR_INSUFFICIENT_CODE_BUFFER = 2
    VKFFT_ERROR_INSUFFICIENT_TEMP_BUFFER = 3
    VKFFT_ERROR_PLAN_NOT_INITIALIZED = 4
    VKFFT_ERROR_NULL_TEMP_PASSED = 5
    VKFFT_ERROR_INVALID_PHYSICAL_DEVICE = 1001
    VKFFT_ERROR_INVALID_DEVICE = 1002
    VKFFT_ERROR_INVALID_QUEUE = 1003
    VKFFT_ERROR_INVALID_COMMAND_POOL = 1004
    VKFFT_ERROR_INVALID_FENCE = 1005
    VKFFT_ERROR_ONLY_FORWARD_FFT_INITIALIZED = 1006
    VKFFT_ERROR_ONLY_INVERSE_FFT_INITIALIZED = 1007
    VKFFT_ERROR_INVALID_CONTEXT = 1008
    VKFFT_ERROR_INVALID_PLATFORM = 1009
    VKFFT_ERROR_ENABLED_saveApplicationToString = 1010,
    VKFFT_ERROR_EMPTY_FFTdim = 2001
    VKFFT_ERROR_EMPTY_size = 2002
    VKFFT_ERROR_EMPTY_bufferSize = 2003
    VKFFT_ERROR_EMPTY_buffer = 2004
    VKFFT_ERROR_EMPTY_tempBufferSize = 2005
    VKFFT_ERROR_EMPTY_tempBuffer = 2006
    VKFFT_ERROR_EMPTY_inputBufferSize = 2007
    VKFFT_ERROR_EMPTY_inputBuffer = 2008
    VKFFT_ERROR_EMPTY_outputBufferSize = 2009
    VKFFT_ERROR_EMPTY_outputBuffer = 2010
    VKFFT_ERROR_EMPTY_kernelSize = 2011
    VKFFT_ERROR_EMPTY_kernel = 2012
    VKFFT_ERROR_EMPTY_applicationString = 2013,
    VKFFT_ERROR_UNSUPPORTED_RADIX = 3001
    VKFFT_ERROR_UNSUPPORTED_FFT_LENGTH = 3002
    VKFFT_ERROR_UNSUPPORTED_FFT_LENGTH_R2C = 3003
    VKFFT_ERROR_UNSUPPORTED_FFT_LENGTH_DCT = 3004
    VKFFT_ERROR_UNSUPPORTED_FFT_OMIT = 3005
    VKFFT_ERROR_FAILED_TO_ALLOCATE = 4001
    VKFFT_ERROR_FAILED_TO_MAP_MEMORY = 4002
    VKFFT_ERROR_FAILED_TO_ALLOCATE_COMMAND_BUFFERS = 4003
    VKFFT_ERROR_FAILED_TO_BEGIN_COMMAND_BUFFER = 4004
    VKFFT_ERROR_FAILED_TO_END_COMMAND_BUFFER = 4005
    VKFFT_ERROR_FAILED_TO_SUBMIT_QUEUE = 4006
    VKFFT_ERROR_FAILED_TO_WAIT_FOR_FENCES = 4007
    VKFFT_ERROR_FAILED_TO_RESET_FENCES = 4008
    VKFFT_ERROR_FAILED_TO_CREATE_DESCRIPTOR_POOL = 4009
    VKFFT_ERROR_FAILED_TO_CREATE_DESCRIPTOR_SET_LAYOUT = 4010
    VKFFT_ERROR_FAILED_TO_ALLOCATE_DESCRIPTOR_SETS = 4011
    VKFFT_ERROR_FAILED_TO_CREATE_PIPELINE_LAYOUT = 4012
    VKFFT_ERROR_FAILED_SHADER_PREPROCESS = 4013
    VKFFT_ERROR_FAILED_SHADER_PARSE = 4014
    VKFFT_ERROR_FAILED_SHADER_LINK = 4015
    VKFFT_ERROR_FAILED_SPIRV_GENERATE = 4016
    VKFFT_ERROR_FAILED_TO_CREATE_SHADER_MODULE = 4017
    VKFFT_ERROR_FAILED_TO_CREATE_INSTANCE = 4018
    VKFFT_ERROR_FAILED_TO_SETUP_DEBUG_MESSENGER = 4019
    VKFFT_ERROR_FAILED_TO_FIND_PHYSICAL_DEVICE = 4020
    VKFFT_ERROR_FAILED_TO_CREATE_DEVICE = 4021
    VKFFT_ERROR_FAILED_TO_CREATE_FENCE = 4022
    VKFFT_ERROR_FAILED_TO_CREATE_COMMAND_POOL = 4023
    VKFFT_ERROR_FAILED_TO_CREATE_BUFFER = 4024
    VKFFT_ERROR_FAILED_TO_ALLOCATE_MEMORY = 4025
    VKFFT_ERROR_FAILED_TO_BIND_BUFFER_MEMORY = 4026
    VKFFT_ERROR_FAILED_TO_FIND_MEMORY = 4027
    VKFFT_ERROR_FAILED_TO_SYNCHRONIZE = 4028
    VKFFT_ERROR_FAILED_TO_COPY = 4029
    VKFFT_ERROR_FAILED_TO_CREATE_PROGRAM = 4030
    VKFFT_ERROR_FAILED_TO_COMPILE_PROGRAM = 4031
    VKFFT_ERROR_FAILED_TO_GET_CODE_SIZE = 4032
    VKFFT_ERROR_FAILED_TO_GET_CODE = 4033
    VKFFT_ERROR_FAILED_TO_DESTROY_PROGRAM = 4034
    VKFFT_ERROR_FAILED_TO_LOAD_MODULE = 4035
    VKFFT_ERROR_FAILED_TO_GET_FUNCTION = 4036
    VKFFT_ERROR_FAILED_TO_SET_DYNAMIC_SHARED_MEMORY = 4037
    VKFFT_ERROR_FAILED_TO_MODULE_GET_GLOBAL = 4038
    VKFFT_ERROR_FAILED_TO_LAUNCH_KERNEL = 4039
    VKFFT_ERROR_FAILED_TO_EVENT_RECORD = 4040
    VKFFT_ERROR_FAILED_TO_ADD_NAME_EXPRESSION = 4041
    VKFFT_ERROR_FAILED_TO_INITIALIZE = 4042
    VKFFT_ERROR_FAILED_TO_SET_DEVICE_ID = 4043
    VKFFT_ERROR_FAILED_TO_GET_DEVICE = 4044
    VKFFT_ERROR_FAILED_TO_CREATE_CONTEXT = 4045
    VKFFT_ERROR_FAILED_TO_CREATE_PIPELINE = 4046
    VKFFT_ERROR_FAILED_TO_SET_KERNEL_ARG = 4047
    VKFFT_ERROR_FAILED_TO_CREATE_COMMAND_QUEUE = 4048
    VKFFT_ERROR_FAILED_TO_RELEASE_COMMAND_QUEUE = 4049
    VKFFT_ERROR_FAILED_TO_ENUMERATE_DEVICES = 4050
    VKFFT_ERROR_FAILED_TO_GET_ATTRIBUTE = 4051
    VKFFT_ERROR_FAILED_TO_CREATE_EVENT = 4052


def load_library(basename):
    if platform.system() == 'Windows':
        # We patched build_ext so the module is a .so and not a dll
        ext = '.so'
    else:
        ext = sysconfig.get_config_var('SO')
    return ctypes.cdll.LoadLibrary(os.path.join(os.path.dirname(__file__) or os.path.curdir, basename + ext))


def primes(n):
    """ Returns the prime decomposition of n as a list.
    This only remains as a useful function, but VkFFT
    allows any prime decomposition, even if performance
    can be better for prime numbers <=13.
    """
    v = [1]
    assert (n > 0)
    i = 2
    while i * i <= n:
        while n % i == 0:
            v.append(i)
            n //= i
        i += 1
    if n > 1:
        v.append(n)
    return v


def radix_gen(nmax, radix, even=False, exclude_one=True, inverted=False, nmin=None, max_pow=None):
    """
    Generate an array of integers which are only multiple of powers
    of base integers, e.g. 2**N1 * 3**N2 * 5**N3 etc...
    :param nmax: the maximum integer to return (included)
    :param radix: the list/tuple of base integers - which don't need
        to be primes
    :param even: if True, only return even numbers
    :param exclude_one: if True (the default), exclude 1
    :param inverted: if True, the returned array will only include
        integers which are NOT in the form 2**N1 * 3**N2 * 5**N3...
    :param nmin: if not None, the integer values returned will be >=nmin
    :param max_pow: if not None, the N1, N2, N3... powers (for sizes
        in the form 2**N1 * 3**N2 * 5**N3) will be at max equal to this
        value, which allows to reduce the number of generated sizes
        while testing all base radixes
    :return: the numpy array of integers, sorted
    """
    a = np.ones(1, dtype=np.int64)
    for i in range(len(radix)):
        if max_pow is None:
            tmp = np.arange(int(np.floor(np.log(nmax) / np.log(radix[i]))) + 1)
        else:
            tmp = np.arange(min(max_pow, int(np.floor(np.log(nmax) / np.log(radix[i])))) + 1)
        a = a * radix[i] ** tmp[:, np.newaxis]
        a = a.flatten()
        a = a[a <= nmax]
    if inverted:
        b = np.arange(nmax + 1)
        b[a] = 0
        a = b.take(np.nonzero(b)[0])
    if even:
        a = a[(a % 2) == 0]
    if nmin is not None:
        a = a[a >= nmin]
    a.sort()
    if len(a):
        if exclude_one and a[0] == 1:
            return a[1:]
    return a


def radix_gen_n(nmax, max_size, radix, ndim=None, even=False, exclude_one=True, inverted=False,
                nmin=None, max_pow=None, range_nd_narrow=None, min_size=0):
    """
    Generate a list of array shape with integers which are only multiple
    of powers of base integers, e.g. 2**N1 * 3**N2 * 5**N3 etc...,
    for each of the dimensions, and with a maximum size.
    Note that this can generate a large number of sizes.
    :param nmax: the maximum value for the length of each dimension (included)
    :param max_size: the maximum size (number of elements) for the array
    :param radix: the list/tuple of base integers - which don't need
        to be primes. If None, all sizes are allowed
    :param ndim: the number of dimensions allowed. If None, 1D, 2D and 3D
        shapes are mixed.
    :param even: if True, only return even numbers
    :param exclude_one: if True (the default), exclude 1
    :param inverted: if True, the returned array will only include
        integers which are NOT in the form 2**N1 * 3**N2 * 5**N3...
    :param nmin: if not None, the integer values returned will be >=nmin
    :param max_pow: if not None, the N1, N2, N3... powers (for sizes
        in the form 2**N1 * 3**N2 * 5**N3) will be at max equal to this
        value, which allows to reduce the number of generated sizes
        while testing all base radixes
    :param range_nd_narrow: if a tuple of values (drel, dabs) is given,
        with drel within [0;1], for dimensions>1,
        in an array of shape (s0, s1, s2), the difference of lengths
        with respect to the first dimension cannot be larger than
        min(drel * s0, dabs). This allows to reduce the number
        of shapes tested. With drel=dabs=0, all dimensions must
        have identical lengths.
    :param min_size: the minimum size (number of elements). This can be
        used to separate large array tests and use a larger number of
        parallel process for smaller ones.
    :return: the list of array shapes.
    """
    v = []
    if radix is None:
        if even:
            if nmin is None:
                n0 = np.arange(2, min(nmax, max_size), 2)
            else:
                n0 = np.arange(nmin + nmin % 2, min(nmax, max_size), 2)
        else:
            if nmin is None:
                n0 = np.arange(2, min(nmax, max_size))
            else:
                n0 = np.arange(nmin, min(nmax, max_size))
    else:
        n0 = radix_gen(nmax, radix, even=even, exclude_one=exclude_one, inverted=inverted, nmin=nmin, max_pow=max_pow)

    if ndim is None or ndim in [1, 12, 123]:
        idx = np.nonzero((n0 <= max_size) * (n0 >= min_size))[0]
        if len(idx):
            v += list(zip(n0.take(idx)))
    if ndim is None or ndim in [2, 12, 123]:
        vidx = list(range(0, len(n0), 1000))
        if vidx[-1] != len(n0):
            vidx.append(len(n0))
        for i1 in range(len(vidx) - 1):
            l01 = n0[vidx[i1]:vidx[i1 + 1]]
            for i2 in range(len(vidx) - 1):
                l2 = n0[vidx[i2]:vidx[i2 + 1]][:, np.newaxis]
                s = (l01 * l2).flatten()
                l1, l2 = (l01 + np.zeros_like(l2)).flatten(), (l2 + np.zeros_like(l01)).flatten()
                tmp = (s <= max_size) * (s >= min_size)
                if range_nd_narrow is not None:
                    drel, dabs = range_nd_narrow
                    m = np.maximum(dabs, l1 * drel)
                    tmp = np.logical_and(tmp, abs(l1 - l2) <= m)
                idx = np.nonzero(tmp)[0]
                if len(idx):
                    v += list(zip(l1.take(idx), l2.take(idx)))
    if ndim is None or ndim in [3, 123]:
        vidx = list(range(0, len(n0), 100))
        if vidx[-1] != len(n0):
            vidx.append(len(n0))
        for i1 in range(len(vidx) - 1):
            l01 = n0[vidx[i1]:vidx[i1 + 1]]
            for i2 in range(len(vidx) - 1):
                l02 = n0[vidx[i2]:vidx[i2 + 1], np.newaxis]
                for i3 in range(len(vidx) - 1):
                    l3 = n0[vidx[i3]:vidx[i3 + 1], np.newaxis, np.newaxis]
                    # print(i1, i2, i3, l1.shape, l2.shape, l3.shape)
                    s = (l01 * l02 * l3).flatten()
                    l1, l2, l3 = (l01 + np.zeros_like(l02) + np.zeros_like(l3)).flatten(), \
                                 (l02 + np.zeros_like(l01) + np.zeros_like(l3)).flatten(), \
                                 (l3 + np.zeros_like(l01) + np.zeros_like(l02)).flatten()
                    tmp = (s <= max_size) * (s >= min_size)
                    if range_nd_narrow is not None:
                        drel, dabs = range_nd_narrow
                        m = np.maximum(dabs, l1 * drel)
                        tmp = np.logical_and(tmp, (abs(l1 - l2) <= m)
                                             * (abs(l1 - l3) <= m))
                    idx = np.nonzero(tmp)[0]
                    if len(idx):
                        v += list(zip(l1.take(idx), l2.take(idx), l3.take(idx)))
    return v


def calc_transform_axes(shape, axes=None, ndim=None):
    """ Compute the final shape of the array to be passed
    to VkFFT, and the axes for which the transform should
    be skipped.
    By collapsing non-transformed consecutive axes and using batch transforms,
    it is possible to support dimensions>3. However after collapsing axes,
    transforms are only possible along the first 3 remaining dimensions.
    Example of possible transforms:
    - 3D array with ndim=1, 2 or 3 or any set of axes
    - n-D array with ndim=1, 2 or 3 with n arbitrary large (the dimensions
      above ndim will be collapsed in a batch transform)
    - shape=(4,5,6,7) and axes=(2,3): the first two axes will be collapsed
      to a (20,6,7) axis
    - shape=(4,5,6,7,8,9) and axes=(2,3): the first two axes will be collapsed
      to a (20,6,7) axis and a batch size of 8*9=81 will be used
    Examples of impossible transforms:
    - shape=(4,5,6,7) with ndim=4: only 3D transforms are allowed
    - shape=(4,5,6,7) with axes=(1,2,3): the index of the last transformed
        axis cannot be >2

    :param shape: the initial shape of the data array. Note that this shape
        should be in th usual numpy order, i.e. the fastest axis is
        listed last. e.g. (nz, ny, nx)
    :param axes: the axes to be transformed. if None, all axes
        are transformed, or up to ndim.
    :param ndim: the number of dimensions for the transform. If None,
        the number of axes is used
    :return: (shape, skip_axis, ndim) with the 4D shape after collapsing
        consecutive non-transformed axes (padded with ones if necessary,
        with the order adequate for VkFFT (nx, ny, nz, n_batch),
        the list of 3 booleans indicating if the (x, y, z) axes should
        be skipped, and the number of transform axes.
    """
    # reverse order to have list as (nx, ny, nz,...)
    shape1 = list(reversed(list(shape)))
    if np.isscalar(axes):
        axes = [axes]
    if ndim is None:
        if axes is None:
            ndim1 = len(shape)
            axes = list(range(ndim1))
    else:
        ndim1 = ndim
        if axes is None:
            axes = list(range(-1, -ndim - 1, -1))
        else:
            if ndim1 != len(axes):
                raise RuntimeError("The number of transform axes does not match ndim:", axes, ndim)
    # Collapse non-transform axes when possible
    skip_axis = [True for i in range(len(shape1))]
    for i in axes:
        skip_axis[i] = False
    skip_axis = list(reversed(skip_axis))  # numpy (z,y,x) to vkfft (x,y,z) order
    # print(shape1, skip_axis, axes)
    i = 0
    while i <= len(shape1) - 2:
        if skip_axis[i] and skip_axis[i + 1]:
            shape1[i] *= shape1[i + 1]
            shape1.pop(i + 1)
            skip_axis.pop(i + 1)
        else:
            i += 1
    # We can pass 3 dimensions to VkFFT (plus a batch dimension)
    if len(skip_axis) - list(reversed(skip_axis)).index(False) - 1 >= 3:
        raise RuntimeError("Unsupported VkFFT transform:", shape, axes, ndim, shape1, skip_axis)

    if len(shape1) < 4:
        shape1 += [1] * (4 - len(shape1))

    if len(skip_axis) < 3:
        skip_axis += [True] * (3 - len(skip_axis))
    skip_axis = skip_axis[:3]

    # Fix ndim so skipped axes are counted
    ndim1 = 3 - list(reversed(skip_axis)).index(False)

    # Axes beyond ndim are marked skipped
    for i in range(ndim1, 3):
        skip_axis[i] = False
    return shape1, skip_axis, ndim1


def check_vkfft_result(res, shape=None, dtype=None, ndim=None, inplace=None,
                       norm=None, r2c=None, dct=None, axes=None, backend=None):
    """
    Check VkFFTResult code.

    :param res: the result code from launching a transform.
    :param shape: shape of the array
    :param dtype: data type of the array
    :param ndim: number of transform dimensions
    :param inplace: True or False
    :param norm: 0 or1 or "ortho"
    :param r2c: True or False
    :param dct: False, 1, 2, 3 or 4
    :param axes: transform axes
    :param backend: the backend
    :raises RuntimeError: if res != 0
    """
    if isinstance(res, ctypes.c_int):
        res = res.value
    if res != 0:
        s = ""
        if r2c:
            s += "R2C "
        elif dct:
            s += "DCT%d " % dct
        else:
            s += "C2C "
        if r2c and inplace and shape is not None:
            tmp = list(shape)
            tmp[-1] -= 2
            shstr = str(tuple(tmp)).replace(" ", "")
            if ",)" in shstr:
                s += shstr.replace(",)", "+2)") + " "
            else:
                s += shstr.replace(")", "+2)") + " "
        else:
            s += str(shape).replace(" ", "") + " "
        if dtype is not None:
            s += str(dtype) + " "
        if axes is not None:
            s += str(axes).replace(" ", "") + " "
        if ndim is not None:
            s += "%dD " % ndim
        if inplace:
            s += "inplace "
        if norm:
            s += "norm=%s " % str(norm)
        if backend is not None:
            s += "[%s]" % backend
        try:
            r = VkFFTResult(res)
            raise RuntimeError("VkFFT error %d: %s %s" % (res, r.name, s))
        except ValueError:
            raise RuntimeError("VkFFT error %d (unknown) %s" % (res, s))


class VkFFTApp:
    """
    VkFFT application interface implementing a FFT plan, base implementation
    handling functions and paremeters common to the CUDA and OpenCL backends.
    """

    def __init__(self, shape, dtype: type, ndim=None, inplace=True, norm=1,
                 r2c=False, dct=False, axes=None, **kwargs):
        """
        Init function for the VkFFT application.

        :param shape: the shape of the array to be transformed. The number
            of dimensions of the array can be larger than the FFT dimensions.
        :param dtype: the numpy dtype of the source array (can be complex64 or complex128)
        :param ndim: the number of dimensions to use for the FFT. By default,
            uses the array dimensions. Can be smaller, e.g. ndim=2 for a 3D
            array to perform a batched 3D FFT on all the layers. The FFT
            is always performed along the last axes if the array's number
            of dimension is larger than ndim, i.e. on the x-axis for ndim=1,
            on the x and y axes for ndim=2, etc.. Unless axes are given.
        :param inplace: if True (the default), performs an inplace transform and
            the destination array should not be given in fft() and ifft().
        :param norm: if 0 (unnormalised), every transform multiplies the L2
            norm of the array by its size (or the size of the transformed
            array if ndim<d.ndim).
            if 1 (the default) or "backward", the inverse transform divides
            the L2 norm by the array size, so FFT+iFFT will keep the array norm.
            if "ortho", each transform will keep the L2 norm, but that will
            involve an extra read & write operation.
        :param r2c: if True, will perform a real->complex transform, where the
            complex destination is a half-hermitian array.
            For an inplace transform, if the input data shape is (...,nx), the input
            float array should have a shape of (..., nx+2), the last two columns
            being ignored in the input data, and the resulting
            complex array (using pycuda's GPUArray.view(dtype=np.complex64) to
            reinterpret the type) will have a shape (..., nx//2 + 1).
            For an out-of-place transform, if the input (real) shape is (..., nx),
            the output (complex) shape should be (..., nx//2+1).
            Note that for C2R transforms with ndim>=2, the source (complex) array
            is modified.
        :param dct: used to perform a Direct Cosine Transform (DCT) aka a R2R transform.
            An integer can be given to specify the type of DCT (1, 2, 3 or 4).
            if dct=True, the DCT type 2 will be performed, following scipy's convention.
        :param axes: a list or tuple of axes along which the transform should be made.
            if None, the transform is done along the ndim fastest axes, or all
            axes if ndim is None. Not allowed for R2C transforms
        :raises RuntimeError:  if the transform dimensions are not allowed by VkFFT.
        """
        self.app = None
        self.config = None
        if dct and r2c:
            raise RuntimeError("R2C and DCT cannot both be selected !")
        if (r2c or dct) and dtype not in [np.float16, np.float32, np.float64]:
            raise RuntimeError("R2C or DCT selected but input type is not real !")
        if r2c and axes is not None:
            raise RuntimeError("axes=... is not allowed for R2C transforms")
        # Get the final shape passed to VkFFT, collapsing non-transform axes
        # as necessary. The calculated shape has 4 dimensions (nx, ny, nz, n_batch)
        self.shape, self.skip_axis, self.ndim = calc_transform_axes(shape, axes, ndim)
        self.inplace = inplace
        self.r2c = r2c
        if dct is False:
            self.dct = 0
        elif dct is True:
            self.dct = 2
        else:
            self.dct = dct
        if dct and self.dct < 1 or dct > 4:
            raise RuntimeError("Only DCT of types 1, 2, 3 and 4 are allowed")
        # print("VkFFTApp:", shape, axes, ndim, "->", self.shape, self.skip_axis, self.ndim)

        # Experimental parameters. Not much difference is seen, so don't document this,
        # VkFFT default parameters seem fine.
        if "disableReorderFourStep" in kwargs:
            self.disableReorderFourStep = kwargs["disableReorderFourStep"]
        else:
            self.disableReorderFourStep = -1

        if "registerBoost" in kwargs:
            self.registerBoost = kwargs["registerBoost"]
        else:
            self.registerBoost = -1

        if "useLUT" in kwargs:
            # useLUT=1 may be beneficial on platforms which have a low accuracy for
            # the native sincos functions.
            if kwargs["useLUT"] is None:
                self.use_lut = -1
            else:
                self.use_lut = kwargs["useLUT"]
        elif USE_LUT is not None:
            self.use_lut = USE_LUT
        else:
            self.use_lut = -1

        if "keepShaderCode" in kwargs:
            # This will print the compiled code if equal to 1
            self.keepShaderCode = kwargs["keepShaderCode"]
        else:
            self.keepShaderCode = -1

        if norm == "backward":
            norm = 1
        self.norm = norm

        # Precision: number of bytes per float
        if dtype in [np.float16, complex32]:
            self.precision = 2
        elif dtype in [np.float32, np.complex64]:
            self.precision = 4
        elif dtype in [np.float64, np.complex128]:
            self.precision = 8

    def _get_fft_scale(self, norm):
        """Return the scale factor by which an array must be multiplied to keep its L2 norm
        after a forward FT
        :param norm: the norm option for which the scale is computed, either 0 or 1
        :return: the scale factor, as a numpy float with the precision used for the fft
        """
        dtype = np.float32
        if self.precision == 8:
            dtype = np.float64
        elif self.precision == 2:
            dtype = np.float16
        s = 1
        ndim_real = 0
        for i in range(self.ndim):
            if not self.skip_axis[i]:
                s *= self.shape[i]
                ndim_real += 1
        s = np.sqrt(s)
        if self.r2c and self.inplace:
            s *= np.sqrt((self.shape[0] - 2) / self.shape[0])
        if self.dct:
            s *= 2 ** (0.5 * ndim_real)
            if self.dct != 4:
                warnings.warn("A DCT type 2 or 3 cannot be strictly normalised, using approximation,"
                              " see https://en.wikipedia.org/wiki/Discrete_cosine_transform#DCT-II")
        if norm == 0 or norm == 1:
            return dtype(1 / s)
        elif norm == "ortho":
            return dtype(1)
        raise RuntimeError("Unknown norm choice !")

    def get_fft_scale(self):
        """Return the scale factor by which an array must be multiplied to keep its L2 norm
        after a forward FT
        """
        return self._get_fft_scale(self.norm)

    def _get_ifft_scale(self, norm):
        """Return the scale factor by which an array must be multiplied to keep its L2 norm
        after a backward FT
        :param norm: the norm option for which the scale is computed, either 0 or 1
        :return: the scale factor, as a numpy float with the precision used for the fft
        """
        dtype = np.float32
        if self.precision == 8:
            dtype = np.float64
        elif self.precision == 2:
            dtype = np.float16
        s = 1
        s_dct = 1
        for i in range(self.ndim):
            if not self.skip_axis[i]:
                s *= self.shape[i]
                if self.dct:
                    s_dct *= np.sqrt(2)
        s = np.sqrt(s)
        if self.r2c and self.inplace:
            s *= np.sqrt((self.shape[0] - 2) / self.shape[0])
        if self.dct and self.dct != 4:
            warnings.warn("A DCT type 2 or 3 cannot be strictly normalised, using approximation,"
                          " see https://en.wikipedia.org/wiki/Discrete_cosine_transform#DCT-II")
        if norm == 0:
            return dtype(1 / (s * s_dct))
        elif norm == 1:
            # Not sure why the difference in scale factors
            if self.dct == 2:
                s_dct = s_dct ** 1
            elif self.dct == 3:
                s_dct = s_dct ** 2
            elif self.dct == 4:
                s_dct = s_dct ** 3
            return dtype(s * s_dct)
        elif norm == "ortho":
            return dtype(1)
        raise RuntimeError("Unknown norm choice !")

    def get_ifft_scale(self):
        """Return the scale factor by which an array must be multiplied to keep its L2 norm
        after a backward FT
        """
        return self._get_ifft_scale(self.norm)
