#EpyNN/nnlibs/gru/parameters.py
import nnlibs.commons.maths as cm

import nnlibs.meta.parameters as mp

import numpy as np


def set_activation(layer):

    args = layer.activation
    layer.activate_update, layer.derivative_update = args[0], cm.get_derivative(args[0])
    layer.activate_reset, layer.derivative_reset = args[1], cm.get_derivative(args[1])
    layer.activate_input, layer.derivative_input = args[2], cm.get_derivative(args[2])
    layer.activate_output, layer.derivative_output = args[3], cm.get_derivative(args[3])

    return None


def init_shapes(layer,hidden_size,runData):
    ### Set layer dictionaries values
    ## Dimensions
    # Hidden size
    layer.d['h'] = hidden_size
    # Vocab size
    layer.d['v'] = runData.e['v']
    # Output size
    if layer.binary == False:
        output_size = layer.d['v']
    else:
        output_size = 2

    layer.d['o'] = output_size

    ## Forward pass shapes
    hv = ( layer.d['h'], layer.d['v'] )
    hh = ( layer.d['h'], layer.d['h'] )
    h1 = ( layer.d['h'], 1 )
    oh = ( layer.d['o'], layer.d['h'] )
    o1 = ( layer.d['o'], 1 )

    # W, U, b - z gate
    layer.fs['Wz'], layer.fs['Uz'], layer.fs['bz'] = hv, hh, h1
    # W, U, b - Reset gate
    layer.fs['Wr'], layer.fs['Ur'], layer.fs['br'] = hv, hh, h1
    # W, U, b - h gate
    layer.fs['Wh'], layer.fs['Uh'], layer.fs['bh'] = hv, hh, h1
    # W, b - Output gate
    layer.fs['Wy'], layer.fs['by'] = oh, o1

    return None

def init_params(layer):

    # Init W, b - Forget gate
    layer.p['Wz'] = layer.initialization(layer.fs['Wz'])
    layer.p['Uz'] = layer.initialization(layer.fs['Uz'])
    layer.p['bz'] = np.zeros(layer.fs['bz'])
    # Init W, b - Forget gate
    layer.p['Wr'] = layer.initialization(layer.fs['Wr'])
    layer.p['Ur'] = layer.initialization(layer.fs['Ur'])
    layer.p['br'] = np.zeros(layer.fs['br'])
    # Init W, b - Forget gate
    layer.p['Wh'] = layer.initialization(layer.fs['Wh'])
    layer.p['Uh'] = layer.initialization(layer.fs['Uh'])
    layer.p['bh'] = np.zeros(layer.fs['bh'])
    # Init W, b - Forget gate
    layer.p['Wy'] = layer.initialization(layer.fs['Wy'])
    layer.p['by'] = np.zeros(layer.fs['by'])

    # Set init to False
    layer.init = False

    return None


def init_forward(layer,A):

    # Cache X (current) from A (prev)
    X = layer.fc['X'] = A
    layer.fs['X'] = X.shape

    # Init cache shapes
    layer.ts = layer.fs['X'][1]

    for c in ['z','r','h','hp','A']:
        layer.fc[c] = [0] * layer.ts

    # Init h shape
    layer.fs['h'] = ( layer.d['h'],layer.fs['X'][-1] )
    # Init h
    h = np.zeros(layer.fs['h'])

    return X, h


def end_forward(layer):

    layer.fc = { k:np.array(v) for k,v in layer.fc.items() }

    A = layer.fc['A']

    if layer.binary == True:
        A = layer.fc['A'] = A[-1]

    return A


def init_backward(layer,dA):

    # Cache X (current) from A (prev)
    dX = layer.bc['dX'] = dA
    # Init dh_next (dhn)
    dhn = layer.bc['dh_n'] = np.zeros_like(layer.fc['h'][0])

    # Cache dXt (dX at current t) from dX
    dXt = layer.bc['dXt'] = dX
    # Cache dh (current) from dXt (prev), dhn, z (current) and h (current)
    dh = np.dot( layer.p['Wy'].T, dXt ) + dhn
    dh = np.multiply( dh, (1-layer.fc['z'][-1]) )
    dh = layer.bc['dh'] = layer.derivative_input(dh,layer.fc['h'][-1])

    return dX, dhn, dXt, dh



def update_gradients(layer,t):
    # Number of sample
    m = layer.m = layer.fs['X'][-1]
    # Retrieve h (current t)
    h = layer.fc['h'][t]
    hp = layer.fc['h'][t-1]
    # Retrieve Xt
    Xt = layer.fc['X'][:,t]

    # Retrieve dv and update dWv and dbv
    dXt = layer.bc['dXt']
    layer.g['dWy'] += 1./ m * np.dot( dXt, h.T )
    layer.g['dby'] += 1./ m * np.sum( dXt,axis=1,keepdims=True)

    # Retrieve dv and update dWv and dbv
    dh = layer.bc['dh']
    layer.g['dWh'] += 1./ m * np.dot( dh, Xt.T )
    layer.g['dUh'] += 1./ m * np.dot( dh, np.multiply(layer.fc['r'][t], hp).T)
    layer.g['dbh'] += 1./ m * np.sum( dh,axis=1,keepdims=True)
    # Retrieve dv and update dWv and dbv
    dr = layer.bc['dr']
    layer.g['dWr'] += 1./ m * np.dot( dr, Xt.T )
    layer.g['dUr'] += 1./ m * np.dot( dr, hp.T )
    layer.g['dbr'] += 1./ m * np.sum( dr,axis=1,keepdims=True)
    # Retrieve dv and update dWv and dbv
    dz = layer.bc['dz']
    layer.g['dWz'] += 1./ m * np.dot( dz, Xt.T )
    layer.g['dUz'] += 1./ m * np.dot( dz, hp.T )
    layer.g['dbz'] += 1./ m * np.sum( dz,axis=1,keepdims=True)

    return None
