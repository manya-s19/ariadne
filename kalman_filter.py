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



# ---------------------
# SET UP KALMAN FILTER
# ---------------------

#there are two pieces of data being estimated by the filter (position and velocity) based on one sensor input (x-position)
kf = KalmanFilter(dim_x = 2, dim_z = 1) 

#setting up values of position and velocity
kf.x = np.array([[0.], 
                 [0.]])



# -----------------------------
# SET UP KALMAN FILTER MATRICES
# -----------------------------

#set up variences for standard deviations               *** values can be altered ***
position_uncertainty = 10**2        
velocity_uncertainty = 100**2
baseline_gps_uncertainty = 5**2
baseline_external_acceleration_uncertainty = 0.3**2

#update this based on external factors later            *** values can be altered ***
gps_uncertainty = baseline_gps_uncertainty
external_acceleration_uncertainty = baseline_external_acceleration_uncertainty

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

#prior_innovation_covarience = kf.S

#how many seconds worth of data do you need?            *** value can be altered ***
seconds = 10


for i in range(seconds):
    print("\n--- TimeStep ", i , " ---\n")

    #UPDATE SENSOR DATA FOR EACH TIMESTEP


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
    trn_x = real_x + np.random.normal(0,2)    #trn_noise is much more stable than gps_noise
    
    #yay it works
    if(i == 6):
        gps_x += 500
    else:
        gps_x = real_x + np.random.normal(0,5)   #gps_noise is randomized, can be unpredictable (for the sake of the MVP)
 


    kf.z = np.array([[gps_x]])



    #UPDATE KALMAN FILTER POSITION ESTIMATE FOR EACH TIMESTEP


    # --------------------------------
    # Position Estimate (Kinematics)
    # --------------------------------

    # PREDICT FUNCTION (bayesian prior)
    # Predicts the current position of the plane based on previous state and motion of the plane
        #(no sensor data, no corrections, just motion propogation)

    kf.predict(None, None, kf.F, kf.Q)
    print("Predicted Velocity:", kf.x[1])
    print("Predicted Position:", kf.x[0])


    # --------------------------------
    # Kalman Filter Position Update
    # --------------------------------

    # UPDATE FUNCTION (bayesian prior)
    # Updates the predicted position of the plane (from predict function above) based on sensor input
        #(uses sensor data, residuals, uncertaintiy, and kalman gain)

    kf.update(kf.z, kf.R, kf.H)
    print("Updated Velocity:", kf.x[1])
    print("Updated Position:", kf.x[0])


    # --------------------------------
    # CALCULATIONS (ANOMALY DETECTION)
    # --------------------------------

    #residual before update (assume kf is actively using GPS readings)
    residual = kf.y
    transpose_residual = kf.y.T
    print("Position Residual: ", residual)

    # compute innovation covariance (S)
    innovation_covarience = kf.S
    print("Innovation Covariance: ", innovation_covarience)

    # compute mahanalobis using residual and innovation covariance
    inverse_innovation_covarience = np.linalg.inv(innovation_covarience)
    mahanalobis = np.sqrt(residual*inverse_innovation_covarience*transpose_residual)
    print("Mahanalobis: ", mahanalobis)


    #UPDATE VARIABLES FOR THE NEXT TIMESTEP



    # -------------------------
    # UPDATES FOR NEXT TIMESTEP
    # -------------------------

    x_i = real_x
    v_i = real_v
    #prior_innovation_covarience = innovation_covarience
    #timestep remains the same, acceleration remains 0 for MVP as of May 10, 2026
    #dt = 1
    #a = 0

