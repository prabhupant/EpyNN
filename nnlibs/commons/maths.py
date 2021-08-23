# EpyNN/nnlibs/commons/maths.py
# Related third party imports
import numpy as np


# To prevent from divide floatting points errors
E_SAFE = 1e-16


def activation_tune(se_hPars):
    """Set layer's hyperparameters as globals.

    For each forward and backward pass the function is called from within the layer.

    :param se_hPars: Local hyperparameters for layers.
    :type se_hPars: dict[str, str or float]
    """
    # Declare global
    global layer_hPars
    # Set global
    layer_hPars = se_hPars

    return None


### Activation functions and derivatives

# Identity function

def identity(x, deriv=False):
    """Compute identity activation or derivative.

    Note this is for testing purpose, can not be used with backpropagation.

    :param x: Input array to pass in function.
    :type x: class:`numpy.ndarray`

    :param deriv: To compute derivative, defaults to False.
    :type deriv: bool, optional

    :return: Output array passed in function.
    :rtype: class:`numpy.ndarray`
    """
    if not deriv:
        pass

    else:
        x = np.ones_like(x)

    return x


# Rectifier Linear Unit (ReLU)

def relu(x, deriv=False):
    """Compute ReLU activation or derivative.

    :param x: Input array to pass in function.
    :type x: class:`numpy.ndarray`

    :param deriv: To compute derivative, defaults to False.
    :type deriv: bool, optional

    :return: Output array passed in function.
    :rtype: class:`numpy.ndarray`
    """
    if not deriv:
        x = np.maximum(0, x)

    elif deriv:
        x = np.greater(x, 0).astype(int)

    return x


# Leaky Rectifier Linear Unit (LReLU)

def lrelu(x, deriv=False):
    """Compute LReLU activation or derivative.

    :param x: Input array to pass in function.
    :type x: class:`numpy.ndarray`

    :param deriv: To compute derivative, defaults to False.
    :type deriv: bool, optional

    :return: Output array passed in function.
    :rtype: class:`numpy.ndarray`
    """
    # Retrieve alpha from layers hyperparameters (temporary globals)
    a = layer_hPars['LRELU_alpha']

    if not deriv:
        x = np.maximum(a * x, x)

    elif deriv:
        x = np.where(x > 0, 1, a)

    return x


# Exponential Linear Unit (ELU)

def elu(x, deriv=False):
    """Compute ELU activation or derivative.

    :param x: Input array to pass in function.
    :type x: class:`numpy.ndarray`

    :param deriv: To compute derivative, defaults to False.
    :type deriv: bool, optional

    :return: Output array passed in function.
    :rtype: class:`numpy.ndarray`
    """
    # Retrieve alpha from layers hyperparameters (temporary globals)
    a = layer_hPars['ELU_alpha']

    if not deriv:
        x = np.where(x > 0, x, a * (np.exp(x, where=x<=0)-1))

    elif deriv:
        x = np.where(x > 0, 1, elu(x) + a)

    return x


# Sigmoid (σ)

def sigmoid(x, linear=True, deriv=False):
    """Compute Sigmoid activation or derivative.

    :param x: Input array to pass in function.
    :type x: class:`numpy.ndarray`

    :param deriv: To compute derivative, defaults to False.
    :type deriv: bool, optional

    :return: Output array passed in function.
    :rtype: class:`numpy.ndarray`
    """
    if linear:
        # Numerically stable version of sigmoid function
        x = np.where(
                    x >= 0, # condition
                    1 / (1+np.exp(-x)), # For positive values
                    np.exp(x) / (1+np.exp(x)) # For negative values
                    )

    if deriv:
        x = x * (1-x)

    return x


# Hyperbolic tangent (tanh)

def tanh(x, linear=True, deriv=False):
    """Compute tanh activation or derivative.

    :param x: Input array to pass in function.
    :type x: class:`numpy.ndarray`

    :param deriv: To compute derivative, defaults to False.
    :type deriv: bool, optional

    :return: Output array passed in function.
    :rtype: class:`numpy.ndarray`
    """
    if linear:
        x = (np.exp(x)-np.exp(-x)) / (np.exp(x)+np.exp(-x))

    if deriv:
        x = 1 - x**2

    return x


# Softmax

def softmax(x, linear=True, deriv=False):
    """Compute softmax activation or derivative.

    :param x: Input array to pass in function.
    :type x: class:`numpy.ndarray`

    :param deriv: To compute derivative, defaults to False.
    :type deriv: bool, optional

    :return: Output array passed in function.
    :rtype: class:`numpy.ndarray`
    """
    # Retrieve temperature from layers hyperparameters (temporary globals)
    T = layer_hPars['softmax_temperature']

    if linear:
        # Numerically stable version of softmax function
        x_safe = x - np.max(x, axis=1, keepdims=True)

        x_exp = np.exp(x_safe / T)
        x_sum = np.sum(x_exp, axis=1, keepdims=True)

        x = x_exp / x_sum

    if deriv:
        x = x * (1-x)

    return x


### Weight initialization


# Xavier

def xavier(shape, rng=np.random):
    """Xavier Normal Distribution initialization for weight array.

    :param shape: Shape of weight array.
    :type shape: tuple[int]

    :param rng: Pseudo-random number generator, defaults to `np.random`.
    :type rng: :class:`numpy.random`

    :return: Initialized weight array.
    :rtype: class:`numpy.ndarray`
    """
    W = rng.standard_normal(shape)        # Normal distribution, zero-centered
    W *= np.sqrt(2 / sum(list(shape)))    # Scale

    return W


# Orthogonal

def orthogonal(shape, rng=np.random):
    """Orthogonal initialization for weight array.

    :param shape: Shape of weight array.
    :type shape: tuple[int]

    :param rng: Pseudo-random number generator, defaults to `np.random`.
    :type rng: :class:`numpy.random`

    :return: Initialized weight array.
    :rtype: class:`numpy.ndarray`
    """
    W = rng.standard_normal(shape)

    W = W.T if shape[0] < shape[1] else W

    # Compute QR factorization
    q, r = np.linalg.qr(W)

    # Make Q uniform according
    d = np.diag(r, 0)
    ph = np.sign(d)
    q *= ph

    W = q.T if shape[0] < shape[1] else q

    return W


### Gradients clipping


def clip_gradient(layer, max_norm=0.25):
    """Clip to avoid vanishing or exploding gradients.

    :param layer: An instance of trainable layer.
    :type layer: Object

    :param max_norm: Maximal clipping coefficient allowed, defaults to 0.25.
    :type max_norm: float, optional
    """
    total_norm = 0

    # Compute L2 norm squared for each gradient
    for grad in layer.g.values():
        grad_norm = np.sum(np.power(grad + E_SAFE, 2))
        total_norm += grad_norm    # Add to total norm

    total_norm = np.sqrt(total_norm)

    # Compute clipping coeficient
    clip_coef = max_norm / (total_norm+E_SAFE)

    # Clip the gradient if norm is greater than max norm
    if clip_coef < 1:
        for g in layer.g.keys():
            layer.g[g] *= clip_coef

    return None
