import time
import numpy as np
import pandas as pd
from PIL import Image
import random
import matplotlib.pyplot as plt
import mlx
import mlx.nn as nn
import mlx.core as mx
from mlx.optimizers import SGD

from datasets import load_dataset

"""
Notes:
    * BatchNorm after each convolution and before activation
    * No dropout
    * Image is resized with its shorter size sampled in [256, 480] for scale augmentation 
    * Conv3-64 = 64 3x3 filters, resulting in 64 output features
    * SGD with batch size of 256
    * Works with Python 3.12 but not 3.9
Define:
    * No. layers: 34
    * Input size: 224x224 crop sampled from an image, per-pixel mean subtracted, color augementation
    * Output size: 
    * No. I/O features of each block: depends
    * Kernel size (convolution filter): usually depends, but all (3x3) for ResNet
    * Convolutional layer hyperparameters - filter (3x3), stride, ?
    * Weight decay: 1e-4
    * Momentum: 9e-1
    * Learning rate: starts at 0.1, divided by 10 as error plateaus 
"""

class ResBlock(nn.Module):
    """
    Take the input, normal forward, recast input onto original
    y = F(x) + x where F(x) is the mapping function (wx + b)
   """
    # i can write a block for each block, but the better option is to create layers based on the input parameters 
    # the no_blocks is variable but the interior structure of each layer is the same, except the no. channels
    # 
    expansion = 1 # Determines the ratio between IO channelsin a resblock, controls the dimesionality of the feature maps
    # only used if bottleneck is used; useless here

    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, downsample=None, groups=1, base_width=64, norm_layer=None): # Block as described in the paper
        super().__init__()
        """
        in_channels: int; add however many IO channels the block specifies (3, 64, 128, 256, 512) 
        out_channels: int; 
        """
        if norm_layer is None:
            self.norm_layer = nn.BatchNorm
        if groups != 1 or base_width != 64:
            raise ValueError('Block only supports groups=1 and base_width=64')

        self.conv1 = nn.Conv2d(in_channels=in_channels, out_channels=out_channels, kernel_size=kernel_size, stride=stride, bias=False, padding=1)
        self.bn1 = nn.BatchNorm(num_features=out_channels)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv2d(in_channels=out_channels, out_channels=out_channels, kernel_size=kernel_size, stride=stride, bias=False, padding=1)
        self.bn2 = nn.BatchNorm(num_features=out_channels)

        self.downsample = downsample
        self.stride = stride
    
    def __call__(self, x):
        cache = x

        # First layer
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        # print(f"First conv: {x.shape}")
       
        # Second layer 
        x = self.conv2(x)
        x = self.bn2(x)
        # print(f"Second conv: {x.shape}")

        # Downsample?
        if self.downsample is not None:
            cache = self.downsample(x)
            # print(f"Cache: {cache.shape}")

        x = mx.add(x, cache)
        out = self.relu(x)

        return out


class ResNet (nn.Module):
    def __init__(self, block, layers, num_classes=1000, zero_init_residual=False, groups=1, width_per_group=64, norm_layer=None):
        """
        block: ResBlock
        layers = list of how many blocks are in each layer [3, 4, 6, 3]
        num_classes: no. classes, for classification
        """
        super().__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm
        self._norm_layer = norm_layer

        self.in_channels = 64

        self.groups = groups
        self.base_width = width_per_group

        self.conv1 = nn.Conv2d(in_channels=3, out_channels=self.in_channels, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm(self.in_channels)
        self.relu = nn.ReLU()

        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)

        self.avgpool = nn.AvgPool2d((1, 1))
        self.fc = nn.Linear(input_dims=512*block.expansion, output_dims=1000)

    
    def _make_layer(self, block, out_channels, blocks, stride=1):
        norm_layer = self._norm_layer
        downsample = None

        if stride != 1 or self.in_channels != out_channels * block.expansion:
            downsample = nn.Sequential(
                    nn.Conv2d(in_channels=self.in_channels * stride, out_channels=out_channels * block.expansion, kernel_size=1, stride=1),  
                    nn.BatchNorm(out_channels * block.expansion)
            )

        layers = []
        layers.append(block(in_channels=self.in_channels, out_channels=out_channels, stride=stride, downsample=downsample))
        self.in_channels = out_channels * block.expansion # Update in_channels

        for _ in range(1, blocks):
            layers.append(block(in_channels=self.in_channels, out_channels=out_channels, groups=self.groups, base_width=self.base_width, norm_layer=norm_layer))  # Use self.in_channels instead of out_channels
        # print(layers)
        return nn.Sequential(*layers)


    def __call__(self, x): 
        x = mx.array(x)
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)

        x = self.maxpool(x)

        x = self.layer1(x)
        # print(f"Exiting layer 1: {x.shape}")
        x = self.layer2(x)
        # print(f"Exiting layer 2: {x.shape}")
        x = self.layer3(x)
        # print(f"Exiting layer 3: {x.shape}")
        x = self.layer4(x)
        # print(f"Exiting layer 4: {x.shape}")

        x = self.avgpool(x)
        # print(f"Shape after pooling: {x.shape}")
        out  = self.fc(x) 
        # print(f"final shape: {x.shape}")

        return out


# Data preparation
# If the dataset is gated/private, make sure you have run huggingface-cli login
sample_size = 100
train_set = load_dataset("imagenet-1k", split=f'train[:{sample_size}]')

train_images = train_set['image']
train_labels = train_set['label']

test_set = load_dataset("imagenet-1k", split=f'test[:{sample_size}]')

test_images = test_set['image']
test_labels = test_set['label']

def preprocess(image):
    # Resize the image to the target size
    target_size = (224, 224)
    image = image.resize(target_size)

    # Convert the image to a NumPy array
    image_array = np.array(image)

    # Check the number of channels
    if image_array.ndim == 2:
        image_array = np.repeat(image_array[..., np.newaxis], 3, axis=-1) # turn grayscale -> RGB
    elif image_array.ndim == 3 and image_array.shape[-1] == 1:
        image_array = np.repeat(image_array, 3, axis=-1) # make the last dim 3
    elif image_array.ndim == 3 and image_array.shape[-1] != 3:
        if image_array.shape[-1] > 3:
            image_array = image_array[..., :3]
        else:
            image_array = np.pad(image_array, ((0, 0), (0, 0), (0, 3 - image_array.shape[-1])), mode='constant')

    # Normalize the pixel values
    normalized_image = (image_array - np.mean(image_array)) / np.std(image_array)

    return normalized_image

#Hyperparameters
lr = 1e-1 # Learning rate
momentum = 9e-1
dr = 1e-4 # Decay rate 
no_epochs = 100
batch_size = 256
layers = [3, 4, 6, 3]


# Initialize network
resnet34 = ResNet(ResBlock, layers) 
mx.eval(resnet34.parameters())


# Optimizers, functions
def loss_fn(model, X, y, batch_size):
    logits = model(X).reshape(batch_size, 1000) 
    y = mx.array(np.eye(1000)[y])
    return mx.mean(nn.losses.cross_entropy(logits, y))

def eval_fn(model, X, y, sample_size):
    logits = model(X).reshape(sample_size, 1000)
    return mx.mean(mx.argmax(logits, axis=1) == y)

loss_and_grad_fn = nn.value_and_grad(resnet34, loss_fn)
optimizer = SGD(lr, momentum, dr) 

def predict(model, image):
    image = mx.array(image)
    image = image.reshape(1, -1)
    predictions = model(image)
    predicted_class = mx.argmax(predictions, axis=1)
    return predicted_class.item()

def batch_iterate(batch_size, X, y):
    assert len(X) == len(y)
    no_batches = len(X) // batch_size

    for i in range(no_batches):
        start = i * batch_size
        end = start + batch_size
        ids = np.arange(start, end) # ids is a list of indices
        yield np.asarray([X[i] for i in ids]), np.array([y[i] for i in ids]), batch_size # Yield so it returns X, y but keeps looping

    if len(X) % batch_size != 0:
        start = no_batches * batch_size
        ids = np.arange(start, len(X))
        yield np.asarray([X[i] for i in ids]), np.array([y[i] for i in ids]), len(X) - start # can probably change this to mx.array later

        
# Training loop
for i in range(no_epochs):
    tic = time.perf_counter()
    
    # Preprocess training images (List of 2D arrays (224, 224, 3))
    # (sample_size, 224, 224, 3)
    preprocessed_train_images = np.stack([preprocess(image) for image in train_images])

    for X, y, b_size in batch_iterate(batch_size, preprocessed_train_images, train_labels):
        y = mx.array(y)
        loss, grads = loss_and_grad_fn(resnet34, X, y, b_size)
        optimizer.update(resnet34, grads)
        mx.eval(resnet34.parameters(), optimizer.state)

    # Preprocess test images
    preprocessed_test_images = np.stack([preprocess(image) for image in test_images])

    accuracy = eval_fn(resnet34, preprocessed_test_images, mx.array(test_labels), sample_size)
    toc = time.perf_counter()

    print(
		f"Epoch {i}: Test accuracy {accuracy.item():.3f},"
		f" Time {toc - tic:.3f} (s)"
	)

resnet34.save_weights('resnet34.npz') 

