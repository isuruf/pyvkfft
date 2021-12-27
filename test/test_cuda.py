# -*- coding: utf-8 -*-

# PyVkFFT
#   (c) 2021- : ESRF-European Synchrotron Radiation Facility
#       authors:
#         Vincent Favre-Nicolin, favre@esrf.fr
#
#
# Unit tests for the cuda backends (pycuda, cupy).
# WARNING: these take a LONG time. There are few tests, but each has many sub-tests
# for the different backends, dimensions, transform type, accuracy and normalisation
# For example the C2C currently has 216 sub-tests per backend (so 432 for pycuda+cupy !)

import unittest
import numpy as np
from numpy.fft import fftn, ifftn, fftshift, rfftn, irfftn

try:
    from scipy.fft import dctn, idctn

    has_scipy_dct = True
except ImportError:
    has_scipy_dct = False
    print("Install scipy if you want to test dct transforms")

try:
    from scipy.misc import ascent
except ImportError:
    def ascent():
        return np.random.randint(0, 255, (512, 512))

try:
    from pyvkfft.cuda import VkFFTApp, primes, has_pycuda, has_cupy

    if has_pycuda:
        import pycuda.autoinit
        import pycuda.driver as cu_drv
        import pycuda.gpuarray as cua

    if has_cupy:
        import cupy as cp
except ImportError:
    has_cupy = False
    has_pycuda = False


class TestVkFFTCUDA(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.dtype_float_v = [np.float32, np.float64]
        cls.dtype_complex_v = [np.complex64, np.complex128]
        cls.backend = []
        cls.vn = [30, 34, 606]
        if has_pycuda:
            cls.backend.append("pycuda")
        if has_cupy:
            cls.backend.append("cupy")
            # TODO: The following somehow helps initialising cupy, not sure why it's useful.
            #  (some context auto-init...). Otherwise a cuLaunchKernel error occurs with
            #  the first transform.
            cupy_a = cp.array(ascent())
            cupy_a.sum()

    @unittest.skipIf(has_pycuda is False and has_cupy, "pycuda is not available, but cupy is")
    def test_pycuda(self):
        """Test if pycuda is available (may not matter if cupy or pyopencl is used instead)"""
        self.assertTrue(has_pycuda, "pycuda is not available")

    @unittest.skipIf(has_cupy is False and has_pycuda, "cupy is not available, but pycuda is")
    def test_cupy(self):
        """Test if cupy is available (may not matter if pycuda or pyopencl is used instead)"""
        self.assertTrue(has_cupy, "cupy is not available")

    @unittest.skipIf(not has_pycuda and not has_cupy, "pycuda and cupy are not available")
    def test_c2c(self):
        """
        Test inplace C2C transforms [240 sub-tests per backend]
        """
        ct = 0
        for backend in self.backend:
            if backend == "pycuda":
                to_gpu = cua.to_gpu
            else:
                to_gpu = cp.array
            for n in self.vn:  # test both radix-2 and Bluestein algorithms
                max_dim = 4
                if n > 64:
                    # Only test 1D and 2D for large sizes
                    max_dim = 2
                for dims in range(1, max_dim + 1):
                    for ndim0 in range(1, min(dims, 3) + 1):
                        # Setup use of either ndim or axes, also test skipping dimensions
                        ndim_axes = [(ndim0, None)]
                        for i in range(1, 2 ** (ndim0 - 1)):
                            axes = []
                            for ii in range(ndim0):
                                if not (i & 2 ** ii):
                                    axes.append(-ii - 1)
                            ndim_axes.append((None, axes))
                        for ndim, axes in ndim_axes:
                            for dtype in self.dtype_complex_v:
                                for norm in [0, 1, "ortho"]:
                                    with self.subTest(backend=backend, n=n, dims=dims, ndim=ndim,
                                                      axes=axes, dtype=dtype, norm=norm):
                                        ct += 1
                                        if dtype == np.complex64:
                                            rtol = 1e-6
                                        else:
                                            rtol = 1e-12
                                        if max(primes(n)) > 13:
                                            # Lower accuracy for Bluestein algorithm.
                                            rtol *= 4
                                            if n > 100 and dtype == np.complex128:
                                                rtol *= 10

                                        d = np.random.uniform(0, 1, [n] * dims).astype(dtype)
                                        # A pure random array may not be a very good test (too random),
                                        # so add a Gaussian
                                        xx = [np.fft.fftshift(np.fft.fftfreq(n))] * dims
                                        v = np.zeros_like(d)
                                        for x in np.meshgrid(*xx, indexing='ij'):
                                            v += x ** 2
                                        d += 10 * np.exp(-v * 2)
                                        n0 = (abs(d) ** 2).sum()
                                        d_gpu = to_gpu(d)
                                        app = VkFFTApp(d.shape, d.dtype, ndim=ndim, norm=norm, axes=axes)
                                        if axes is None:
                                            axes = list(range(dims))[-ndim:]  # For numpy
                                        # base FFT scale for numpy
                                        s = np.sqrt(np.prod([d.shape[i] for i in axes]))

                                        d = fftn(d, axes=axes) / s
                                        d_gpu = app.fft(d_gpu) * app.get_fft_scale()
                                        self.assertTrue(
                                            np.allclose(d, d_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))

                                        d = ifftn(d, axes=axes) * s
                                        d_gpu = app.ifft(d_gpu) * app.get_ifft_scale()
                                        self.assertTrue(
                                            np.allclose(d, d_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))
                                        n1 = (abs(d_gpu.get()) ** 2).sum()
                                        self.assertTrue(np.isclose(n0, n1, rtol=rtol))
        # print("Finished C2C tests with %d subtests" % ct)

    @unittest.skipIf(not has_pycuda and not has_cupy, "pycuda and cupy are not available")
    def test_c2c_outofplace(self):
        """
        Test out-of-place C2C transforms [240 sub-tests per backend]
        """
        for backend in self.backend:
            if backend == "pycuda":
                to_gpu = cua.to_gpu
                gpu_empty_like = cua.empty_like
            else:
                to_gpu = cp.array
                gpu_empty_like = cp.empty_like
            for n in [32, 17, 808]:  # test both radix-2 and Bluestein algorithms
                max_dim = 4
                if n > 100:
                    # Only test 1D and 2D for large sizes
                    max_dim = 2
                for dims in range(1, max_dim + 1):
                    for ndim0 in range(1, min(dims, 3) + 1):
                        # Setup use of either ndim or axes, also test skipping dimensions
                        ndim_axes = [(ndim0, None)]
                        for i in range(1, 2 ** (ndim0 - 1)):
                            axes = []
                            for ii in range(ndim0):
                                if not (i & 2 ** ii):
                                    axes.append(-ii - 1)
                            ndim_axes.append((None, axes))
                        for ndim, axes in ndim_axes:
                            for dtype in self.dtype_complex_v:
                                for norm in [0, 1, "ortho"]:
                                    with self.subTest(backend=backend, n=n, dims=dims, ndim=ndim,
                                                      axes=axes, dtype=dtype, norm=norm):
                                        if dtype == np.complex64:
                                            rtol = 1e-6
                                        else:
                                            rtol = 1e-12
                                        if max(primes(n)) > 13:
                                            # Lower accuracy for Bluestein algorithm.
                                            rtol *= 4
                                            if n > 100 and dtype == np.complex128:
                                                rtol *= 10

                                        d = np.random.uniform(0, 1, [n] * dims).astype(dtype)
                                        # A pure random array may not be a very good test (too random),
                                        # so add a Gaussian
                                        xx = [np.fft.fftshift(np.fft.fftfreq(n))] * dims
                                        v = np.zeros_like(d)
                                        for x in np.meshgrid(*xx, indexing='ij'):
                                            v += x ** 2
                                        d += 10 * np.exp(-v * 2)
                                        n0 = (abs(d) ** 2).sum()
                                        d_gpu = to_gpu(d)
                                        d1_gpu = gpu_empty_like(d_gpu)
                                        app = VkFFTApp(d.shape, d.dtype, ndim=ndim, norm=norm, axes=axes, inplace=False)
                                        if axes is None:
                                            axes = list(range(dims))[-ndim:]  # For numpy
                                        # base FFT scale for numpy
                                        s = np.sqrt(np.prod([d.shape[i] for i in axes]))

                                        d = fftn(d, axes=axes) / s
                                        d1_gpu = app.fft(d_gpu, d1_gpu) * app.get_fft_scale()
                                        self.assertTrue(
                                            np.allclose(d, d1_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))

                                        d = ifftn(d, axes=axes) * s
                                        d_gpu = app.ifft(d1_gpu, d_gpu) * app.get_ifft_scale()
                                        self.assertTrue(
                                            np.allclose(d, d_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))
                                        n1 = (abs(d_gpu.get()) ** 2).sum()
                                        self.assertTrue(np.isclose(n0, n1, rtol=rtol))

    @unittest.skipIf(not has_pycuda and not has_cupy, "pycuda and cupy are not available")
    def test_r2c(self):
        """
        Test inplace R2C transforms
        """
        for backend in self.backend:
            if backend == "pycuda":
                to_gpu = cua.to_gpu
            else:
                to_gpu = cp.array
            for n in self.vn:
                # test both radix-2 and Bluestein algorithms.
                # We need a multiple of 2 for the first axis of an inplace R2C transform
                max_dim = 4
                if n > 64:
                    # Only test 1D and 2D for large sizes
                    max_dim = 2
                for dims in range(1, max_dim + 1):
                    for ndim in range(1, min(dims, 3) + 1):
                        for dtype in self.dtype_float_v:
                            for norm in [0, 1, "ortho"]:
                                with self.subTest(backend=backend, n=n, dims=dims, ndim=ndim, dtype=dtype, norm=norm):
                                    if dtype == np.float32:
                                        rtol = 1e-6
                                    else:
                                        rtol = 1e-12
                                    if max(primes(n)) > 13:
                                        rtol *= 4  # Lower accuracy for Bluestein algorithm

                                    sh = [n] * dims
                                    sh[-1] += 2
                                    shc = [n] * dims
                                    shc[-1] = n // 2 + 1

                                    d = np.random.uniform(0, 1, sh).astype(dtype)
                                    # A pure random array may not be a very good test (too random),
                                    # so add a Gaussian
                                    xx = [np.fft.fftshift(np.fft.fftfreq(nn)) for nn in sh]
                                    v = np.zeros_like(d)
                                    for x in np.meshgrid(*xx, indexing='ij'):
                                        v += x ** 2
                                    d += 10 * np.exp(-v * 2)
                                    n0 = (abs(d[..., :-2]) ** 2).sum()
                                    d_gpu = to_gpu(d)
                                    app = VkFFTApp(d.shape, d.dtype, ndim=ndim, norm=norm, r2c=True)
                                    # base FFT scale
                                    s = np.sqrt(n ** ndim)

                                    d = rfftn(d[..., :-2], axes=list(range(dims))[-ndim:]) / s
                                    d_gpu = app.fft(d_gpu) * app.get_fft_scale()
                                    self.assertTrue(d_gpu.shape == tuple(shc))

                                    if dtype == np.float32:
                                        self.assertTrue(d_gpu.dtype == np.complex64)
                                    elif dtype == np.float64:
                                        self.assertTrue(d_gpu.dtype == np.complex128)

                                    self.assertTrue(np.allclose(d, d_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))

                                    d = irfftn(d, axes=list(range(dims))[-ndim:]) * s
                                    d_gpu = app.ifft(d_gpu) * app.get_ifft_scale()
                                    self.assertTrue(d_gpu.shape == tuple(sh))

                                    self.assertTrue(np.allclose(d, d_gpu.get()[..., :-2], rtol=rtol,
                                                                atol=abs(d).max() * rtol))
                                    n1 = (abs(d_gpu.get()[..., :-2]) ** 2).sum()
                                    self.assertTrue(np.isclose(n0, n1, rtol=rtol))

    @unittest.skipIf(not has_pycuda and not has_cupy, "pycuda and cupy are not available")
    def test_r2c_outofplace(self):
        """
        Test out-of-place R2C transforms
        """
        for backend in self.backend:
            if backend == "pycuda":
                to_gpu = cua.to_gpu
                gpu_empty = cua.empty
            else:
                to_gpu = cp.array
                gpu_empty = cp.empty
            for n in self.vn:  # test both radix-2 and Bluestein algorithms.
                max_dim = 4
                if n > 64:
                    # Only test 1D and 2D for large sizes
                    max_dim = 2
                for dims in range(1, max_dim + 1):
                    for ndim in range(1, min(dims, 3) + 1):
                        for dtype in self.dtype_float_v:
                            for norm in [0, 1, "ortho"]:
                                with self.subTest(backend=backend, n=n, dims=dims, ndim=ndim, dtype=dtype, norm=norm):
                                    if dtype == np.float32:
                                        rtol = 1e-6
                                    else:
                                        rtol = 1e-12
                                    if max(primes(n)) > 13:
                                        rtol *= 4  # Lower accuracy for Bluestein algorithm

                                    if dtype == np.float32:
                                        dtype_c = np.complex64
                                    elif dtype == np.float64:
                                        dtype_c = np.complex128

                                    sh = [n] * dims
                                    sh = tuple(sh)
                                    shc = [n] * dims
                                    shc[-1] = n // 2 + 1
                                    shc = tuple(shc)

                                    d = np.random.uniform(0, 1, sh).astype(dtype)
                                    # A pure random array may not be a very good test (too random),
                                    # so add a Gaussian
                                    xx = [np.fft.fftshift(np.fft.fftfreq(nn)) for nn in sh]
                                    v = np.zeros_like(d)
                                    for x in np.meshgrid(*xx, indexing='ij'):
                                        v += x ** 2
                                    d += 10 * np.exp(-v * 2)
                                    n0 = (abs(d) ** 2).sum()
                                    d_gpu = to_gpu(d)
                                    d1_gpu = gpu_empty(shc, dtype=dtype_c)

                                    app = VkFFTApp(d.shape, d.dtype, ndim=ndim, norm=norm, r2c=True, inplace=False)
                                    # base FFT scale
                                    s = np.sqrt(np.prod(d.shape[-ndim:]))

                                    d = rfftn(d, axes=list(range(dims))[-ndim:]) / s
                                    d1_gpu = app.fft(d_gpu, d1_gpu) * app.get_fft_scale()
                                    self.assertTrue(d1_gpu.shape == tuple(shc))
                                    self.assertTrue(d1_gpu.dtype == dtype_c)

                                    self.assertTrue(np.allclose(d, d1_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))

                                    # The shape of the transformed axes must be supplied for scipy.fft.irfftn
                                    axes = list(range(dims))[-ndim:]
                                    d = irfftn(d, [sh[i] for i in axes], axes=axes) * s
                                    d_gpu = app.ifft(d1_gpu, d_gpu) * app.get_ifft_scale()
                                    self.assertTrue(d_gpu.shape == tuple(sh))

                                    self.assertTrue(np.allclose(d, d_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))
                                    n1 = (abs(d_gpu.get()) ** 2).sum()
                                    self.assertTrue(np.isclose(n0, n1, rtol=rtol))

    @unittest.skipIf(not has_pycuda and not has_cupy, "pycuda and cupy are not available")
    @unittest.skipIf(not has_scipy_dct, "scipy.fft.dctn is not available")
    def test_dct(self):
        """
        Test inplace DCT transforms
        """
        for n in self.vn:
            # test both radix-2 and Bluestein algorithms.
            max_dim = 4
            if n > 64:
                # Only test 1D and 2D for large sizes
                max_dim = 2
            for dims in range(1, max_dim + 1):
                for ndim in range(1, min(dims, 3) + 1):
                    sh = [n] * dims
                    for i in range(ndim, dims):
                        # Smaller array on non-transformed axes
                        sh[-i - 1] = 2
                    d0 = np.random.uniform(0, 1, sh)
                    # A pure random array may not be a very good test (too random),
                    # so add a Gaussian
                    xx = [np.fft.fftshift(np.fft.fftfreq(nn)) for nn in sh]
                    v = np.zeros_like(d0)
                    for x in np.meshgrid(*xx, indexing='ij'):
                        v += x ** 2
                    d0 += 10 * np.exp(-v * 2)
                    for dtype in self.dtype_float_v:
                        for dct in range(1, 4 + 1):
                            if dct == 1 and n > 750 * 4 // np.dtype(dtype).itemsize:
                                # Not sure where this limitation comes from
                                # limit is n > 757 for float64, 1532 for float32 on a GTX 1080
                                continue
                            elif n > 2000 * 4 // np.dtype(dtype).itemsize:
                                # limit is n > 2002 for float64, 4004 for float32 on a GTX 1080
                                continue
                            # for norm in [0, 1, "ortho"] # TODO : test all norms
                            norm = 1  # Same default norm as scipy
                            with self.subTest(n=n, dims=dims, ndim=ndim, dtype=dtype, dct=dct, norm=norm):
                                if dtype == np.float32:
                                    rtol = 1e-4
                                else:
                                    rtol = 1e-8
                                if max(primes(n)) > 13 or dct != 2:
                                    # Lower accuracy for Bluestein transforms
                                    # Why is it necessary for DCT types != 2 ?
                                    rtol *= 8

                                d = d0.astype(dtype).copy()

                                d_gpu = cua.to_gpu(d)
                                app = VkFFTApp(d.shape, d.dtype, ndim=ndim, norm=norm, dct=dct)

                                d = dctn(d, axes=list(range(dims))[-ndim:], type=dct)
                                d_gpu = app.fft(d_gpu)
                                self.assertTrue(np.allclose(d, d_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))

                                d = idctn(d, axes=list(range(dims))[-ndim:], type=dct)
                                d_gpu = app.ifft(d_gpu)

                                self.assertTrue(np.allclose(d, d_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))
                                self.assertTrue(np.allclose(d0, d_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))

    @unittest.skipIf(not has_pycuda and not has_cupy, "pycuda and cupy are not available")
    @unittest.skipIf(not has_scipy_dct, "scipy.fft.dctn is not available")
    def test_dct_outofplace(self):
        """
        Test out-of-place DCT transforms
        """
        for n in self.vn:
            # test both radix-2 and Bluestein algorithms.
            max_dim = 4
            if n > 64:
                # Only test 1D and 2D for large sizes
                max_dim = 2
            for dims in range(1, max_dim + 1):
                for ndim in range(1, min(dims, 3) + 1):
                    sh = [n] * dims
                    for i in range(ndim, dims):
                        # Smaller array on non-transformed axes
                        sh[-i - 1] = 2
                    d0 = np.random.uniform(0, 1, sh)
                    # A pure random array may not be a very good test (too random),
                    # so add a Gaussian
                    xx = [np.fft.fftshift(np.fft.fftfreq(nn)) for nn in sh]
                    v = np.zeros_like(d0)
                    for x in np.meshgrid(*xx, indexing='ij'):
                        v += x ** 2
                    d0 += 10 * np.exp(-v * 2)
                    for dtype in self.dtype_float_v:
                        for dct in range(1, 4 + 1):
                            if dct == 1 and n > 750 * 4 // np.dtype(dtype).itemsize:
                                # Not sure where this limitation comes from
                                # limit is n > 757 for float64, 1532 for float32 on a GTX 1080
                                continue
                            elif n > 2000 * 4 // np.dtype(dtype).itemsize:
                                # limit is n > 2002 for float64, 4004 for float32 on a GTX 1080
                                continue
                            # for norm in [0, 1, "ortho"] # TODO : test all norms
                            norm = 1  # Same default norm as scipy
                            with self.subTest(n=n, dims=dims, ndim=ndim, dtype=dtype, dct=dct, norm=norm):
                                if dtype == np.float32:
                                    rtol = 1e-4
                                else:
                                    rtol = 1e-8
                                if max(primes(n)) > 13 or dct != 2:
                                    # Lower accuracy for Bluestein transforms
                                    # Why is it necessary for DCT types != 2 ?
                                    rtol *= 8

                                d = d0.astype(dtype).copy()

                                d_gpu = cua.to_gpu(d)
                                d1_gpu = cua.empty_like(d_gpu)
                                app = VkFFTApp(d.shape, d.dtype, ndim=ndim, norm=norm,
                                               dct=dct, inplace=False)

                                d = dctn(d, axes=list(range(dims))[-ndim:], type=dct)
                                d1_gpu = app.fft(d_gpu, d1_gpu)
                                self.assertTrue(np.allclose(d0, d_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))
                                self.assertTrue(np.allclose(d, d1_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))

                                d = idctn(d, axes=list(range(dims))[-ndim:], type=dct)
                                d_gpu = app.ifft(d1_gpu, d_gpu)

                                self.assertTrue(np.allclose(d, d_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))
                                self.assertTrue(np.allclose(d0, d_gpu.get(), rtol=rtol, atol=abs(d).max() * rtol))

    @unittest.skipIf(not has_pycuda and not has_cupy, "pycuda and cupy are not available")
    def test_streams(self):
        """
        Test multiple FFT in // with different streams.
        :return:
        """
        for backend in self.backend:
            if backend == "pycuda":
                to_gpu = cua.to_gpu
            else:
                to_gpu = cp.array
            for dtype in self.dtype_complex_v:
                with self.subTest(backend=backend, dtype=dtype):
                    if dtype == np.complex64:
                        rtol = 1e-6
                    else:
                        rtol = 1e-12
                    d = ascent().astype(dtype)
                    n_streams = 5
                    vd = []
                    vapp = []
                    for i in range(n_streams):
                        vd.append(to_gpu(np.roll(d, i * 7, axis=1)))
                        vapp.append(VkFFTApp(d.shape, d.dtype, ndim=2, norm=1, stream=cu_drv.Stream()))

                    for i in range(n_streams):
                        vapp[i].fft(vd[i])
                    for i in range(n_streams):
                        dn = fftn(np.roll(d, i * 7, axis=1))
                        self.assertTrue(np.allclose(dn, vd[i].get(), rtol=rtol, atol=abs(dn).max() * rtol))

                    for i in range(n_streams):
                        vapp[i].ifft(vd[i])
                    for i in range(n_streams):
                        dn = np.roll(d, i * 7, axis=1)
                        self.assertTrue(np.allclose(dn, vd[i].get(), rtol=rtol, atol=abs(dn).max() * rtol))


def suite():
    test_suite = unittest.TestSuite()
    load_tests = unittest.defaultTestLoader.loadTestsFromTestCase
    test_suite.addTest(load_tests(TestVkFFTCUDA))
    return test_suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite', verbosity=2)
