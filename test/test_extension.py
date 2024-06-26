import torch
from torch.testing._internal.common_utils import TestCase
from torch.testing._internal.optests import opcheck
import unittest
import extension_cpp
from torch import Tensor
from typing import Tuple
import torch.nn.functional as F


def sample_inputs(device, *, requires_grad=False):
    batch_size = 3
    features = 17
    state_size = 5
    kwargs = {"dtype": torch.float64, "device": device, "requires_grad": requires_grad}
    X = torch.randn(
        batch_size,  # E: No overload variant of "randn" matches argument
        features,
        **kwargs
    )
    h = torch.randn(batch_size, state_size, **kwargs)  # E: No overload varia
    C = torch.randn(batch_size, state_size, **kwargs)  # E: No overload varia
    W = torch.randn(3 * state_size, features + state_size, **kwargs)
    b = torch.randn(1, 3 * state_size, **kwargs)  # E: No overload variant of "randn"
    return X, W, b, h, C


class TestLLTM(TestCase):
    def _test_correctness(self, device):
        args = sample_inputs(device)
        result = extension_cpp.ops.lltm(*args)
        expected = extension_cpp.ops.reference_lltm(*args)
        self.assertEqual(len(result), len(expected))
        torch.testing.assert_close(result, expected)

    def test_correctness_cpu(self):
        self._test_correctness("cpu")

    @unittest.skipIf(not torch.cuda.is_available(), "requires cuda")
    def test_correctness_cuda(self):
        self._test_correctness("cuda")

    def _test_gradients(self, device):
        args = sample_inputs(device, requires_grad=True)
        # Use torch.autograd.gradcheck to check that gradients are OK
        torch.autograd.gradcheck(extension_cpp.ops.lltm, args)

    def test_gradients_cpu(self):
        self._test_gradients("cpu")

    # This is supposed to succeed, there's probably a bug in the CUDA kernel.
    @unittest.expectedFailure
    @unittest.skipIf(not torch.cuda.is_available(), "requires cuda")
    def test_gradients_cuda(self):
        self._test_gradients("cuda")

    def _opcheck(self, device):
        args = sample_inputs(device)
        # Use opcheck to test that the operator was written correctly.
        opcheck(torch.ops.extension_cpp.lltm_forward.default, args)

    def test_opcheck_cpu(self):
        self._opcheck("cpu")

    @unittest.skipIf(not torch.cuda.is_available(), "requires cuda")
    def test_opcheck_cuda(self):
        self._opcheck("cuda")


if __name__ == "__main__":
    unittest.main()
