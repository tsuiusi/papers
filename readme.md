# Papers
My implementations of the seminal papers of machine learning.

Inspired (to start) by https://github.com/hitorilabs/papers.

Will work through this while going through PRML.

This repo also serves as a devlog and notes.

**Table of Contents:**
1. [Initialization](#initialization) 
2. [ResNet](#resnet)
3. [Random Forest](#random-forest)
4. [Perceptron](#perceptron)

## Initialization
> pip install numpy mlx torch pandas matplotlib-pyplot 


## ResNet
* Residual network
* Very vertical

![ResBlock](resblock.png)

devlog:
* errors in resnet class witht the inputs; input channels is weird and also wrong
* current shape is 100, 224, 224, 3; it expects (64, 7, 7, 64) with O being at the end and I being the front

bugs:
* an extra reshape inside the ``__call__`` messed the reshaping up
