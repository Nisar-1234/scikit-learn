"""
=============================================================
Gaussian process regression (GPR) with noise-level estimation
=============================================================

This example shows the ability of the
:class:`~sklearn.gaussian_process.kernels.WhiteKernel` to estimate the noise
level in the data. Moreover, we show the importance of kernel hyperparameters
initialization.
"""
print(__doc__)

# Authors: Jan Hendrik Metzen <jhm@informatik.uni-bremen.de>
#          Guillaume Lemaitre <guillaume.lemaitre@inria.fr>
# License: BSD 3 clause

# %%
# Data generation
# ---------------
#
# We will work in a setting where `X` will be a single feature. We create a
# function that will generate a the target to be predicted. We will add an
# option to add some noise to the generated target.
import numpy as np


def target_generator(X, add_noise=False):
    target = 0.5 + np.sin(3 * X)
    if add_noise:
        rng = np.random.RandomState(1)
        target += rng.normal(0, 0.3, size=target.shape)
    return target.squeeze()


# %%
# Let's have a look to the target generator where we will not add any noise to
# observe the signal that we would like to predict.
X = np.linspace(0, 5, num=30).reshape(-1, 1)
y = target_generator(X, add_noise=False)

# %%
import matplotlib.pyplot as plt

plt.plot(X, y, label="Perfect generator")
plt.legend()
plt.xlabel("X")
_ = plt.ylabel("y")

# %%
# The target is transforming the input `X` using a sine function. Now, we will
# generate few noisy training samples. To illustrate the noise level, we will
# plot the true signal together with the noisy training samples.
rng = np.random.RandomState(0)
X_train = rng.uniform(0, 5, size=20).reshape(-1, 1)
y_train = target_generator(X_train, add_noise=True)

# %%
plt.plot(X, y, label="Perfect generator")
plt.scatter(
    x=X_train[:, 0], y=y_train, color="tab:orange",
    label="Noisy training samples",
)
plt.legend()
plt.xlabel("X")
_ = plt.ylabel("y")

# %%
# Optimisation of kernel hyperparameters in GPR
# ---------------------------------------------
#
# Now, we will create a GPR using an additive kernel using a
# :class:`~sklearn.gaussian_process.kernels.RBF` and
# :class:`~sklearn.gaussian_process.kernels.WhiteKernel` kernels.
# The :class:`~sklearn.gaussian_process.kernels.WhiteKernel` is a kernel that
# will able to estimate the amount of noise present in the data while the
# :class:`~sklearn.gaussian_process.kernels.RBF` will serve at fitting the
# non-linearity between the data and the target.
#
# However, we will show that the hyperparameter space contains several local
# minima. It will highlight the importance of initial hyperparameter values.
#
# We will create a model using a kernel with a high noise level and a large
# length scale, which explains all variations in the data by noise.
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel

kernel = (
    1.0 * RBF(length_scale=1e1, length_scale_bounds=(1e-2, 1e3)) +
    WhiteKernel(noise_level=1, noise_level_bounds=(1e-5, 1e1))
)
gpr = GaussianProcessRegressor(kernel=kernel, alpha=0.0)
gpr.fit(X_train, y_train)
y_mean, y_std = gpr.predict(X, return_std=True)

# %%
plt.plot(X, y, label="Perfect generator")
plt.scatter(
    x=X_train[:, 0], y=y_train, color="tab:orange", label="Noisy measurement"
)
plt.errorbar(X, y_mean, y_std)
plt.legend()
plt.xlabel("X")
plt.ylabel("y")
_ = plt.title(
    f"Initial: {kernel}\nOptimum: {gpr.kernel_}\nLog-Marginal-Likelihood: "
    f"{gpr.log_marginal_likelihood(gpr.kernel_.theta)}"
)
# %%
# We see that the optimum kernel found still have a high noise level and
# and an even larger length scale. However, we see that the model does not
# provide satisfactory predictions.
#
# Now, we will initialize the hyperparameter with a lower noise level and
# length scale.
kernel = (
    1.0 * RBF(length_scale=1e-1, length_scale_bounds=(1e-2, 1e3)) +
    WhiteKernel(noise_level=1e-2, noise_level_bounds=(1e-10, 1e1))
)
gpr = GaussianProcessRegressor(kernel=kernel, alpha=0.0)
gpr.fit(X_train, y_train)
y_mean, y_std = gpr.predict(X, return_std=True)

# %%
plt.plot(X, y, label="Perfect generator")
plt.scatter(
    x=X_train[:, 0], y=y_train, color="tab:orange", label="Noisy measurement"
)
plt.errorbar(X, y_mean, y_std)
plt.legend()
plt.xlabel("X")
plt.ylabel("y")
_ = plt.title(
    f"Initial: {kernel}\nOptimum: {gpr.kernel_}\nLog-Marginal-Likelihood: "
    f"{gpr.log_marginal_likelihood(gpr.kernel_.theta)}"
)

# %%
# First, we see that the model is more satisfactory than the previous one
# regarding the predictions. It is able to estimate the noise-free functional
# relationship.
#
# Looking at the kernel hyperparameters, we see that the best combination found
# as a smaller noise level and shorter length scale than the first model.
#
# We can have a look at the Log-Marginal-Likelihood (LML) of GPR for different
# hyperparameters to have an idea of the minima.
from matplotlib.colors import LogNorm

length_scale = np.logspace(-2, 4, num=50)
noise_level = np.logspace(-2, 1, num=50)
length_scale_grid, noise_level_grid = np.meshgrid(length_scale, noise_level)

log_marginal_likelihood = [
    gpr.log_marginal_likelihood(np.log([0.36, scale, noise]))
    for scale, noise in zip(length_scale_grid.ravel(),
                            noise_level_grid.ravel())
]
log_marginal_likelihood = np.reshape(
    log_marginal_likelihood, newshape=noise_level_grid.shape
)

# %%
vmin, vmax = (-log_marginal_likelihood).min(), 50
level = np.around(
    np.logspace(np.log10(vmin), np.log10(vmax), num=50), decimals=1
)
plt.contour(
    length_scale_grid, noise_level_grid, -log_marginal_likelihood,
    levels=level, norm=LogNorm(vmin=vmin, vmax=vmax),
)
plt.colorbar()
plt.xscale("log")
plt.yscale("log")
plt.xlabel("Length-scale")
plt.ylabel("Noise-level")
plt.title("Log-marginal-likelihood")
plt.show()

# %%
# We see that there are two local minima that correspond to the combination
# of hyperparameters previously found. Depending on the initial value for the
# hyperparameters, the gradient-based optimization might converge whether or
# not to the best model. It is thus important to repeat the optimization
# several times for different initializations.
