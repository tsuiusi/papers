# Papers
My implementations of the seminal papers of machine learning.

Implementation queue:
* 3DGS https://arxiv.org/pdf/2308.04079.pdf
* LSTM (from scratch?)

## LeNet-5
* MNIST recognition

## 3DGS
* 3D Gaussian splatting
* Goal 1 is to have a navigatable 3d model/scene locally
* Goal 2 is to upgrade it to 4d
* Goal 3 is to find a way to make it fast

### Further reading:
* https://arxiv.org/pdf/2403.10242.pdf
* https://arxiv.org/pdf/2312.09147.pdf
* https://zouzx.github.io/TriplaneGaussian/
* https://ericpenner.github.io/soft3d/
* https://arxiv.org/pdf/2109.08857.pdf
* https://arxiv.org/pdf/2310.08528.pdf

## ResNet
* Residual network
* Very vertical

![ResBlock](/images/resblock.png)

Devlog/improvements:
* change line 273 to mx.array, changing the effects afterward

Bug log:
* the input channel issue: an extra reshape inside the ``__call__`` messed the reshaping up
* residual operation shape issue bug: the stride was wrong, downsampled a bit too much
* hard coded the batch\_size and matrix reshaping; changed it to the variable names and was fixed
