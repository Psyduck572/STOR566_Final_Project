# -*- coding: utf-8 -*-
"""CycleGAN and AttentionGAN Models.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/14Ydqj5_qC57eQCTTDw9LI1q4y0Z3C6ON
"""

!pip install git+https://www.github.com/keras-team/keras-contrib.git

from keras_contrib.layers.normalization.instancenormalization import InstanceNormalization
from keras.initializers import RandomNormal
import numpy as np
import keras
import tensorflow as tf
from keras.layers import Input,Conv2D,MaxPooling2D,Flatten,Activation,BatchNormalization,UpSampling2D 
from keras.layers import Dropout,GlobalAveragePooling2D,LeakyReLU,Dense,Reshape, concatenate,Conv2DTranspose
from keras.models import Model,load_model
import matplotlib.pyplot as plt
import keras.backend as K



import os
import time
from datetime import datetime


from keras.applications import InceptionResNetV2
from keras.callbacks import TensorBoard

from keras.optimizers import Adam
from keras.utils import to_categorical
from keras_preprocessing import image

from numpy import asarray
from numpy import vstack

from tensorflow.keras.utils import img_to_array

from keras.preprocessing.image import load_img
from numpy import savez_compressed


import pandas as pd

import os

from matplotlib import pyplot

from numpy import load

from random import random
from numpy import load
from numpy import zeros
from numpy import ones
from numpy import asarray
from numpy.random import randint
from keras.optimizers import Adam


def conv2d(input_, output_dim, ks=4, s=2, stddev=0.02, padding='SAME',name='c2d'):
  return Conv2D(output_dim,kernel_size=ks,strides=s,padding=padding,kernel_initializer=tf.truncated_normal_initializer(stddev=0.02),name=name)(input_)

def lrelu(input_,name='lr'):
  return LeakyReLU(alpha=0.2,name=name)(input_)

def iNorm(input_,name='iNorm'):
  return InstanceNormalization(axis=-1,name=name)(input_)

# discriminator model
def build_discriminator(image_shape):
  # weight initialization
	#init = RandomNormal(stddev=0.02)
	# source image input
	in_image = Input(shape=image_shape)
	#C1
	d1 = lrelu(conv2d(in_image,64,4,name='d_c1'),'lr1' )
	 
	# C2
	d2 = lrelu(iNorm(conv2d(d1,128,4,name='d_c2'),'iN2'),'lr2') 
	
	# C3
	d3 = lrelu(iNorm(conv2d(d1,256,4,name='d_c3'),'iN3'),'lr3')
	
	# C4
	d4 = lrelu(iNorm(conv2d(d3,512,4,name='d_c4'),'iN4'),'lr4')
	
	'''
	# second last output layer
	d = conv2d(in_image,128,3,1) 
	d = iNorm(d)  
	d = lrelu(d) 
	'''

	#  output

	d5 = conv2d(d4,1,4,1,name='d_c5')  #Conv2D(1, 4,1, padding='same', kernel_initializer=init)(d)
	# define model
	model = Model(in_image, d5)
	# compile model
	model.compile(loss='mse', optimizer=Adam(lr=0.0002, beta_1=0.5), loss_weights=[0.5])
	return model

disc=build_discriminator(dataB[0].shape)
disc.summary()

def padd3(input_):
  import tensorflow as tf
  return tf.pad(input_, [[0, 0], [3, 3], [3, 3], [0, 0]], "REFLECT")

def padd1(input_):
  import tensorflow as tf
  return tf.pad(input_, [[0, 0], [1, 1], [1, 1], [0, 0]], "REFLECT")  

from keras.layers import Add,Lambda
def res_block(input_,nf=64,ks=3,s=1,name='res_blk'):
  p=int((ks-1)/2)
  y=Lambda(padd1)(input_) #(tf.pad(input_,[[0,0],[p,p],[p,p],[0,0]],'REFLECT'))
  
  y=iNorm(conv2d(y,nf,ks,s,padding='VALID',name=name+'_c1'),name=name+'_iN1')
  
  y=Lambda(padd1)(y) #(tf.pad(tf.nn.relu(y),[[0,0],[p,p],[p,p],[0,0]],'REFLECT'))
  
  y=iNorm(conv2d(y,nf,ks,s,padding='VALID',name=name+'_c2'),name=name+'_iN2')
  
  
  y1=keras.layers.Add()([y,input_])
  
  return y1

def deconv2d(input_, output_dim, ks=4, s=2, stddev=0.02, padding='SAME',name='dc2d'):
  #Conv2DTranspose(64, (3,3), strides=(2,2), padding='same', kernel_initializer=init)(g)
  
  dcv=Conv2DTranspose(output_dim,(ks,ks),strides=(s,s),padding=padding,kernel_initializer=tf.truncated_normal_initializer(stddev=0.02),name=name)(input_)
  
  return dcv

from keras.layers import Lambda,Conv2DTranspose

def build_generator(image_shape):
  nf=64 # num filters for first layer 
  input_=Input(shape=(128,128,3))
  c0 = Lambda(padd3)(input_)
  
  c1 = Activation('relu')(iNorm(conv2d(c0, nf, 7, 1, padding='VALID', name='g_e1_c'), 'g_e1_bn'))
  c2 = Activation('relu')(iNorm(conv2d(c1, nf*2, 3, 2, name='g_e2_c'), 'g_e2_bn'))
  c3 = Activation('relu')(iNorm(conv2d(c2, nf*4 , 3, 2, name='g_e3_c'), 'g_e3_bn'))

  r1 = res_block(c3, nf*4, name='g_r1')
  r2 = res_block(r1, nf*4, name='g_r2')
  r3 = res_block(r2, nf*4, name='g_r3')
  r4 = res_block(r3, nf*4, name='g_r4')
  r5 = res_block(r4, nf*4, name='g_r5')
  r6 = res_block(r5, nf*4, name='g_r6')
  r7 = res_block(r6, nf*4, name='g_r7')
  r8 = res_block(r7, nf*4, name='g_r8')
  r9 = res_block(r8, nf*4, name='g_r9')
  
  
  d1=Conv2DTranspose(nf*2, (3,3), strides=(2,2), padding='same', kernel_initializer=tf.truncated_normal_initializer(stddev=0.02),name='g_d1_dc')(r9)
  
  d1=Activation('relu')(iNorm(d1,name='g_d1_bn'))

  d2=Conv2DTranspose(nf, (3,3), strides=(2,2), padding='same', kernel_initializer=tf.truncated_normal_initializer(stddev=0.02),name='g_d2_dc')(d1)
  

  d2=Activation('relu')(iNorm(d2,name='g_d2_bn'))

  d2 = Lambda(padd3)(d2)#(tf.pad(d2, [[0, 0], [3, 3], [3, 3], [0, 0]], "REFLECT"))

  

  d3=conv2d(d2, 3 , 7, 1, padding='VALID', name='g_pred_c')

  

  pred=Activation('tanh')(d3)

  model=Model(input_,pred)
  

  return model


gen=build_generator(dataA[0].shape)
gen.summary()

def build_composite_model(g_model_1, d_model, g_model_2, image_shape):
	# ensure the model we're updating is trainable
	g_model_1.trainable = True
	# mark discriminator as not trainable
	d_model.trainable = False
	# mark other generator model as not trainable
	g_model_2.trainable = False
	# discriminator element
	input_gen = Input(shape=image_shape)
	gen1_out = g_model_1(input_gen)
	output_d = d_model(gen1_out)
	# identity element
	input_id = Input(shape=image_shape)
	output_id = g_model_1(input_id)
	# forward cycle
	output_f = g_model_2(gen1_out)
	# backward cycle
	gen2_out = g_model_2(input_id)
	output_b = g_model_1(gen2_out)
	# define model graph
	model = Model([input_gen, input_id], [output_d, output_id, output_f, output_b])
	# define optimization algorithm configuration
	opt = Adam(lr=0.0002, beta_1=0.5)
	# compile model with weighting of least squares loss and L1 loss
	model.compile(loss=['mse', 'mae', 'mae', 'mae'], loss_weights=[1, 5, 10, 10], optimizer=opt)
	return model

def get_subsample(dataset):

    t1=np.random.randint(900)
    t2=np.random.randint(1200,2000)
    t3=np.random.randint(2500,2800)
    return np.vstack((dataset[0][t1:t1+300],dataset[0][t2:t2+400],dataset[0][t3:t3+300])),np.vstack((dataset[1][t1:t1+300], dataset[1][t2:t2+400],dataset[1][t3:t3+300]))
 
 
def get_subsample2(dataset):
  t0=np.random.randint(250)
  t1=np.random.randint(300)
  t2=np.random.randint(1200,2000)
  t3=np.random.randint(2500,2800)
  return np.vstack((dataset[0][t1:t1+800],dataset[0][t2:t2+200])),np.vstack((dataset[1][t1:t1+100], dataset[2][t0:t0+900]))


import torch
import itertools
from util.image_pool import ImagePool
from .base_model import BaseModel
from . import networks


class AttentionGANModel(BaseModel):
    @staticmethod
    def modify_commandline_options(parser, is_train=True):
        parser.set_defaults(no_dropout=True)  # default CycleGAN did not use dropout
        if is_train:
            parser.add_argument('--lambda_A', type=float, default=10.0, help='weight for cycle loss (A -> B -> A)')
            parser.add_argument('--lambda_B', type=float, default=10.0, help='weight for cycle loss (B -> A -> B)')
            parser.add_argument('--lambda_identity', type=float, default=0.5, help='use identity mapping. Setting lambda_identity other than 0 has an effect of scaling the weight of the identity mapping loss. For example, if the weight of the identity loss should be 10 times smaller than the weight of the reconstruction loss, please set lambda_identity = 0.1')

        return parser

    def __init__(self, opt):
        """Initialize the CycleGAN class.
        Parameters:
            opt (Option class)-- stores all the experiment flags; needs to be a subclass of BaseOptions
        """
        BaseModel.__init__(self, opt)
        # specify the training losses you want to print out. The training/test scripts will call <BaseModel.get_current_losses>
        self.loss_names = ['D_A', 'G_A', 'cycle_A', 'idt_A', 'D_B', 'G_B', 'cycle_B', 'idt_B']
        # specify the images you want to save/display. The training/test scripts will call <BaseModel.get_current_visuals>
        visual_names_A = ['real_A', 'fake_B', 'rec_A', 'o1_b', 'o2_b', 'o3_b', 'o4_b', 'o5_b', 'o6_b', 'o7_b', 'o8_b', 'o9_b', 'o10_b',
        'a1_b', 'a2_b', 'a3_b', 'a4_b', 'a5_b', 'a6_b', 'a7_b', 'a8_b', 'a9_b', 'a10_b', 'i1_b', 'i2_b', 'i3_b', 'i4_b', 'i5_b', 
        'i6_b', 'i7_b', 'i8_b', 'i9_b', 'i10_b']
        visual_names_B = ['real_B', 'fake_A', 'rec_B', 'o1_a', 'o2_a', 'o3_a', 'o4_a', 'o5_a', 'o6_a', 'o7_a', 'o8_a', 'o9_a', 'o10_a', 
        'a1_a', 'a2_a', 'a3_a', 'a4_a', 'a5_a', 'a6_a', 'a7_a', 'a8_a', 'a9_a', 'a10_a', 'i1_a', 'i2_a', 'i3_a', 'i4_a', 'i5_a', 
        'i6_a', 'i7_a', 'i8_a', 'i9_a', 'i10_a']
        if self.isTrain and self.opt.lambda_identity > 0.0:  # if identity loss is used, we also visualize idt_B=G_A(B) ad idt_A=G_A(B)
            visual_names_A.append('idt_B')
            visual_names_B.append('idt_A')

        if self.opt.saveDisk:
            self.visual_names = ['real_A', 'fake_B', 'a10_b', 'real_B','fake_A', 'a10_a']
        else:
            self.visual_names = visual_names_A + visual_names_B  # combine visualizations for A and B
        # specify the models you want to save to the disk. The training/test scripts will call <BaseModel.save_networks> and <BaseModel.load_networks>.
        if self.isTrain:
            self.model_names = ['G_A', 'G_B', 'D_A', 'D_B']
        else:  # during test time, only load Gs
            self.model_names = ['G_A', 'G_B']

        # define networks (both Generators and discriminators)
        # The naming is different from those used in the paper.
        # Code (vs. paper): G_A (G), G_B (F), D_A (D_Y), D_B (D_X)
        self.netG_A = networks.define_G(opt.input_nc, opt.output_nc, opt.ngf, 'our', opt.norm,
                                        not opt.no_dropout, opt.init_type, opt.init_gain, self.gpu_ids)
        self.netG_B = networks.define_G(opt.output_nc, opt.input_nc, opt.ngf, 'our', opt.norm,
                                        not opt.no_dropout, opt.init_type, opt.init_gain, self.gpu_ids)

        if self.isTrain:  # define discriminators
            self.netD_A = networks.define_D(opt.output_nc, opt.ndf, opt.netD,
                                            opt.n_layers_D, opt.norm, opt.init_type, opt.init_gain, self.gpu_ids)
            self.netD_B = networks.define_D(opt.input_nc, opt.ndf, opt.netD,
                                            opt.n_layers_D, opt.norm, opt.init_type, opt.init_gain, self.gpu_ids)

        if self.isTrain:
            if opt.lambda_identity > 0.0:  # only works when input and output images have the same number of channels
                assert(opt.input_nc == opt.output_nc)
            self.fake_A_pool = ImagePool(opt.pool_size)  # create image buffer to store previously generated images
            self.fake_B_pool = ImagePool(opt.pool_size)  # create image buffer to store previously generated images
            # define loss functions
            self.criterionGAN = networks.GANLoss(opt.gan_mode).to(self.device)  # define GAN loss.
            self.criterionCycle = torch.nn.L1Loss()
            self.criterionIdt = torch.nn.L1Loss()
            # initialize optimizers; schedulers will be automatically created by function <BaseModel.setup>.
            self.optimizer_G = torch.optim.Adam(itertools.chain(self.netG_A.parameters(), self.netG_B.parameters()), lr=opt.lr, betas=(opt.beta1, 0.999))
            self.optimizer_D = torch.optim.Adam(itertools.chain(self.netD_A.parameters(), self.netD_B.parameters()), lr=opt.lr, betas=(opt.beta1, 0.999))
            self.optimizers.append(self.optimizer_G)
            self.optimizers.append(self.optimizer_D)

    def set_input(self, input):
        """Unpack input data from the dataloader and perform necessary pre-processing steps.
        Parameters:
            input (dict): include the data itself and its metadata information.
        The option 'direction' can be used to swap domain A and domain B.
        """
        AtoB = self.opt.direction == 'AtoB'
        self.real_A = input['A' if AtoB else 'B'].to(self.device)
        self.real_B = input['B' if AtoB else 'A'].to(self.device)
        self.image_paths = input['A_paths' if AtoB else 'B_paths']

    def forward(self):
        """Run forward pass; called by both functions <optimize_parameters> and <test>."""
        self.fake_B, \
        self.o1_b, self.o2_b, self.o3_b, self.o4_b, self.o5_b, self.o6_b, self.o7_b, self.o8_b, self.o9_b, self.o10_b, \
        self.a1_b, self.a2_b, self.a3_b, self.a4_b, self.a5_b, self.a6_b, self.a7_b, self.a8_b, self.a9_b, self.a10_b, \
        self.i1_b, self.i2_b, self.i3_b, self.i4_b, self.i5_b, self.i6_b, self.i7_b, self.i8_b, self.i9_b, self.i10_b = self.netG_A(self.real_A)  # G_A(A)
        self.rec_A, _, _, _, _, _, _, _, _, _, _, \
        _, _, _, _, _, _, _, _, _, _, \
        _, _, _, _, _, _, _, _, _, _ = self.netG_B(self.fake_B)   # G_B(G_A(A))
        self.fake_A, \
        self.o1_a, self.o2_a, self.o3_a, self.o4_a, self.o5_a, self.o6_a, self.o7_a, self.o8_a, self.o9_a, self.o10_a, \
        self.a1_a, self.a2_a, self.a3_a, self.a4_a, self.a5_a, self.a6_a, self.a7_a, self.a8_a, self.a9_a, self.a10_a, \
        self.i1_a, self.i2_a, self.i3_a, self.i4_a, self.i5_a, self.i6_a, self.i7_a, self.i8_a, self.i9_a, self.i10_a = self.netG_B(self.real_B)  # G_B(B)
        self.rec_B, _, _, _, _, _, _, _, _, _, _, \
        _, _, _, _, _, _, _, _, _, _, \
        _, _, _, _, _, _, _, _, _, _ = self.netG_A(self.fake_A)   # G_A(G_B(B))

    def backward_D_basic(self, netD, real, fake):
        """Calculate GAN loss for the discriminator
        Parameters:
            netD (network)      -- the discriminator D
            real (tensor array) -- real images
            fake (tensor array) -- images generated by a generator
        Return the discriminator loss.
        We also call loss_D.backward() to calculate the gradients.
        """
        # Real
        pred_real = netD(real)
        loss_D_real = self.criterionGAN(pred_real, True)
        # Fake
        pred_fake = netD(fake.detach())
        loss_D_fake = self.criterionGAN(pred_fake, False)
        # Combined loss and calculate gradients
        loss_D = (loss_D_real + loss_D_fake) * 0.5
        loss_D.backward()
        return loss_D

    def backward_D_A(self):
        """Calculate GAN loss for discriminator D_A"""
        fake_B = self.fake_B_pool.query(self.fake_B)
        self.loss_D_A = self.backward_D_basic(self.netD_A, self.real_B, fake_B)

    def backward_D_B(self):
        """Calculate GAN loss for discriminator D_B"""
        fake_A = self.fake_A_pool.query(self.fake_A)
        self.loss_D_B = self.backward_D_basic(self.netD_B, self.real_A, fake_A)

    def backward_G(self):
        """Calculate the loss for generators G_A and G_B"""
        lambda_idt = self.opt.lambda_identity
        lambda_A = self.opt.lambda_A
        lambda_B = self.opt.lambda_B
        # Identity loss
        if lambda_idt > 0:
            # G_A should be identity if real_B is fed: ||G_A(B) - B||
            self.idt_A, _, _, _, _, _, _, _, _, _, _, \
            _, _, _, _, _, _, _, _, _, _, \
            _, _, _, _, _, _, _, _, _, _ = self.netG_A(self.real_B)
            self.loss_idt_A = self.criterionIdt(self.idt_A, self.real_B) * lambda_B * lambda_idt
            # G_B should be identity if real_A is fed: ||G_B(A) - A||
            self.idt_B, _, _, _, _, _, _, _, _, _, _, \
            _, _, _, _, _, _, _, _, _, _, \
            _, _, _, _, _, _, _, _, _, _ = self.netG_B(self.real_A)
            self.loss_idt_B = self.criterionIdt(self.idt_B, self.real_A) * lambda_A * lambda_idt
        else:
            self.loss_idt_A = 0
            self.loss_idt_B = 0

        # GAN loss D_A(G_A(A))
        self.loss_G_A = self.criterionGAN(self.netD_A(self.fake_B), True)
        # GAN loss D_B(G_B(B))
        self.loss_G_B = self.criterionGAN(self.netD_B(self.fake_A), True)
        # Forward cycle loss || G_B(G_A(A)) - A||
        self.loss_cycle_A = self.criterionCycle(self.rec_A, self.real_A) * lambda_A
        # Backward cycle loss || G_A(G_B(B)) - B||
        self.loss_cycle_B = self.criterionCycle(self.rec_B, self.real_B) * lambda_B
        # combined loss and calculate gradients
        self.loss_G = self.loss_G_A + self.loss_G_B + self.loss_cycle_A + self.loss_cycle_B + self.loss_idt_A + self.loss_idt_B
        self.loss_G.backward()

    def optimize_parameters(self):
        """Calculate losses, gradients, and update network weights; called in every training iteration"""
        # forward
        self.forward()      # compute fake images and reconstruction images.
        # G_A and G_B
        self.set_requires_grad([self.netD_A, self.netD_B], False)  # Ds require no gradients when optimizing Gs
        self.optimizer_G.zero_grad()  # set G_A and G_B's gradients to zero
        self.backward_G()             # calculate gradients for G_A and G_B
        self.optimizer_G.step()       # update G_A and G_B's weights
        # D_A and D_B
        self.set_requires_grad([self.netD_A, self.netD_B], True)
        self.optimizer_D.zero_grad()   # set D_A and D_B's gradients to zero
        self.backward_D_A()      # calculate gradients for D_A
        self.backward_D_B()      # calculate graidents for D_B
        self.optimizer_D.step()  # update D_A and D_B's weights