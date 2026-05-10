import numpy as np
#import filterpy
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

# --------------------------------
# FOR TESTING PURPOSES
# --------------------------------

x_i = 0
v_i = 250
dt = 1      #timestamp (every second)
a = 0       #(for the sake of MVP) assume flight is cruising


# --------------------------------
# FOR REAL DATA TRACKING PURPOSES
# --------------------------------

# velocity = acceleration * time (updates every timestep)
real_v = v_i + a * dt
print("Real Velocity:", real_v)


#kinematics eqn (updates every timestep)
real_x = x_i + 0.5*(v_i + real_v)*dt
print("Real Position:", real_x)

#sensor data (updates every timestep)
irs_bias = np.random.normal(0,0.01)#random (small bias)
irs_x = real_x + irs_bias
gps_x = real_x + np.random.normal(0,5)   #gps_noise is randomized, can be unpredictable (for the sake of the MVP)
trn_x = real_x + np.random.normal(0,2)    #trn_noise is much more stable than gps_noise



# ---------------------
# SET UP KALMAN FILTER
# ---------------------

#there are two pieces of data being estimated by the filter (position and velocity) based on one sensor input (x-position)
kf = KalmanFilter(dim_x = 2, dim_z = 1) 

#setting up values of position and velocity
kf.x = np.array([[0.], 
                 [0.]])
kf.z = gps_x


#set up variences for standard deviations       *** values can be altered ***
position_uncertainty = 10**2        
velocity_uncertainty = 100**2
gps_uncertainty = 5**2
external_acceleration_uncertainty = 0.3**2

#set up State Covariance Matrix (P) - kalman filter's estimate’s unreliability (position and velocity)
#[position uncertaintiy, position/velocity relationship], [velocity/position relationship, velocity uncertainty]
#stnd deviation = sqrt(uncertainty)
kf.P = np.array([[position_uncertainty, 0.],
                 [0., velocity_uncertainty]])

#set up Measurement Noise Covarience (R) - unreliability of GPS position readings compared to true position
kf.R = np.array([[gps_uncertainty]])

#set up Process Uncertainty (Q) - unreliability of state predictions (position and velocity) overtime due to unmodeled acceleration noise
kf.Q = Q_discrete_white_noise(2, dt, external_acceleration_uncertainty)

#set up State Transition Matrix (F) - determines next state given current state
kf.F = np.array([[1., dt],
                 [0., 1.]])

#set up Measurement  (H) - the part of the state the given sensor actually observes
kf.H = np.array([[1., 0.]])


# --------------------------------
# Kalman Filter Position Estimate
# --------------------------------

# PREDICT FUNCTION (bayesian prior)
# Predicts the current position of the plane

kf.predict(None, None, kf.F, kf.Q)
print("Current Velocity:", kf.x[1])
print("Current Position:", kf.x[0])


# --------------------------------
# Kalman Filter Position Update
# --------------------------------

# PREDICT FUNCTION (bayesian prior)
# Predicts the current position of the plane
kf.update(kf.z, kf.R, kf.H)
print("Updated Velocity:", kf.x[1])
print("Updated Prediction:", kf.x[0])


# ---------------------
# Outputs
# ---------------------

#residual before update (assume kf is actively using GPS readings)
residual = kf.y
print("Position Residual: ", residual)

# compute innovation covariance (S)

# computer mahanalobis using residual and innovation covariance


current_estimated_position = kf.x[0]
current_estimated_velocity = kf.x[1]

