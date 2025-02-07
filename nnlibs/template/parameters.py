# EpyNN/nnlibs/template/parameters.py


def template_compute_shapes(layer, A):
    """Compute forward shapes and dimensions from input for layer.
    """
    X = A    # Input of current layer

    layer.fs['X'] = X.shape    # (m, .. )

    layer.d['m'] = layer.fs['X'][0]          # Number of samples (m)
    layer.d['n'] = X.size // layer.d['m']    # Number of features (n)

    return None


def template_initialize_parameters(layer):
    """Initialize parameters from shapes for layer.
    """
    # No parameters to initialize for Template layer

    return None


def template_compute_gradients(layer):
    """Compute gradients with respect to weight and bias for layer.
    """
    # No gradients to compute for Template layer

    return None


def template_update_parameters(layer):
    """Update parameters from gradients for layer.
    """
    # No parameters to update for Template layer

    return None
