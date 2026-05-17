import numpy as np
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
from trn.terrain_matching import sample_terrain_path, simulate_sensor_profile, compare_profiles, estimate_position_from_terrain
from tabulate import tabulate


# --------------------------------
# FOR TESTING PURPOSES
# --------------------------------

x_i = 0
v_i = 250
dt = 1      #timestamp (every second)
a = 0       #(for the sake of MVP) assume flight is cruising


# ---------------------
# SET UP SENSOR STATES
# ---------------------

# The possible sensor classifications
    # in_kf                 no issues, sensor is used in kalman filter's estimation of the plane's state
    # standby               inital state of TRN
    # flagged               sensor is flagged for suspicious behaviour, still used in kf, but is monitored for changes
    # eliminated            severe anomaly is detected, sensor eliminated from use, ATC notified (depending on spoofing/other issues)

# Inital values of sensor states
gps_state = "IN_KF"
irs_state = "IN_KF"
trn_state = "STANDBY"

# -----------------------------------
# INITIALIZE SENSOR POSITION READINGS
# -----------------------------------
irs_x = 0.0
gps_x = 0.0
trn_x = 0.0

sensor_x = gps_x

# -----------------------------------
# INITIALIZE FLIGHT PATH DATA
# -----------------------------------
start_lat = 24.4667
start_lon = 54.3667
end_lat = 25.1221
end_lon = 56.3345

#how many seconds worth of data do you need?            *** value can be altered ***
seconds = 10 #45 mins total flight time

#how the terrain looks for the entire flight path
expected_terrain_map = sample_terrain_path(
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    seconds
)

#how the terrain looks over a period of time
terrain_signature = []

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
baseline_trn_uncertainty = 2**2
terrain_style = 1.0 #0.5 = accurate (extremely rocky), 1.0 = normal (mixed terrain), 2/3 = unreliable (flatlands/ocean)
baseline_external_acceleration_uncertainty = 0.3**2

#update this based on external factors later            *** values can be altered ***
gps_uncertainty = baseline_gps_uncertainty
trn_uncertainty = baseline_trn_uncertainty * terrain_style
external_acceleration_uncertainty = baseline_external_acceleration_uncertainty

#set up State Covariance Matrix (P) - kalman filter's estimate’s unreliability (position and velocity)
#[position uncertaintiy, position/velocity relationship], [velocity/position relationship, velocity uncertainty]
#stnd deviation = sqrt(uncertainty)
kf.P = np.array([[position_uncertainty, 0.],
                [0., velocity_uncertainty]])

#set up Measurement Noise Covarience (R) - unreliability of GPS position readings compared to true position
sensor_uncertainty = gps_uncertainty
kf.R = np.array([[sensor_uncertainty]])

#set up Process Uncertainty (Q) - unreliability of state predictions (position and velocity) overtime due to unmodeled acceleration noise
kf.Q = Q_discrete_white_noise(2, dt, external_acceleration_uncertainty)

#set up State Transition Matrix (F) - determines next state given current state
kf.F = np.array([[1., dt],
                [0., 1.]])

#set up Measurement  (H) - the part of the state the given sensor actually observes
kf.H = np.array([[1., 0.]])

#prior_innovation_covarience = kf.S

timestep_data_collection = []

for i in range(seconds):
    print("\n--- TimeStep ", i , " ---\n")

    #UPDATE SENSOR DATA FOR EACH TIMESTEP


    # --------------------------------
    # FOR REAL DATA TRACKING PURPOSES
    # --------------------------------

    # velocity = acceleration * time (updates every timestep)
    real_v = v_i + a * dt


    #kinematics eqn (updates every timestep)
    real_x = x_i + 0.5*(v_i + real_v)*dt

    measured_elevation = simulate_sensor_profile(
        [expected_terrain_map[i]]
    )[0]
    terrain_signature.append(measured_elevation)

    if len(terrain_signature) > 15:
        terrain_signature.pop(0)

    #sensor data (updates every timestep)
    irs_bias = np.random.normal(0,0.01)#random (small bias)
    irs_x = real_x + irs_bias
    #trn_x = + np.random.normal(0,2)    #trn_noise is much more stable than gps_noise

    distance_per_step = (seconds * v_i) / len(expected_terrain_map)

    predicted_index = int(kf.x[0][0] / distance_per_step)

    trn_index, terrain_error = estimate_position_from_terrain(
        expected_terrain_map,
        terrain_signature,
        predicted_index=predicted_index,
        search_radius=5
    )

    trn_x = trn_index * distance_per_step


    #INJECT SPOOFING SCENARIO #1
    if(i == 6):
        gps_x = real_x + 500
    else:
        gps_x = real_x + np.random.normal(0,5)   #gps_noise is randomized, can be unpredictable (for the sake of the MVP)



    if gps_state == "IN_KF" and trn_state == "STANDBY":
        sensor_x = gps_x
        sensor_uncertainty = gps_uncertainty
    elif gps_state == "ELIMINATED" and trn_state == "IN_KF":
        print("\t\t\t\t\t***Switched to TRN, Eliminated GPS\n\n")
        sensor_x = trn_x
        sensor_uncertainty = trn_uncertainty
    elif gps_state == "ELIMINATED" and trn_state == "ELIMINATED":
        pass
    else:
        pass
 
    #Update matrices depending on sensor in use
    kf.z = np.array([[sensor_x]])
    kf.R = np.array([[sensor_uncertainty]])


    #UPDATE KALMAN FILTER POSITION ESTIMATE FOR EACH TIMESTEP


    # --------------------------------
    # Position Estimate (Kinematics)
    # --------------------------------

    # PREDICT FUNCTION (bayesian prior)
    # Predicts the current position of the plane based on previous state and motion of the plane
        #(no sensor data, no corrections, just motion propogation)

    kf.predict()
    predicted_position = kf.x[0][0]
    predicted_velocity = kf.x[1][0]


    # --------------------------------
    # Kalman Filter Position Update
    # --------------------------------

    # UPDATE FUNCTION (bayesian prior)
    # Updates the predicted position of the plane (from predict function above) based on sensor input
        #(uses sensor data, residuals, uncertaintiy, and kalman gain)

    kf.update(kf.z)
    updated_position = kf.x[0][0]
    updated_velocity = kf.x[1][0]


    # --------------------------------
    # CALCULATIONS (ANOMALY DETECTION)
    # --------------------------------

    #residual before update (assume kf is actively using GPS readings)
    residual = kf.y
    transpose_residual = kf.y.T

    # compute innovation covariance (S)
        # what should the residual statistically be given the plane's previous states?
    innovation_covarience = kf.S

    # compute mahanalobis using residual and innovation covariance
        #how abnormal is the noise given the sensor data, state of the plane, kalman gain, residual, and the innovation covarience?
    inverse_innovation_covarience = np.linalg.inv(innovation_covarience)
    mahanalobis = np.sqrt(residual*inverse_innovation_covarience*transpose_residual)



    #UPDATE ANOMALY DETECTION AND SENSOR CLASSIFICATION LOGIC



    # ----------------------
    # SENSOR CLASSIFICATION         # only flags GPS rn, trn usage in kalman filter is not implemented as of May 11, 2026
    # ----------------------

    if mahanalobis < 3: #normal enough, can use GPS
        gps_state = "IN_KF"
        trn_state = "STANDBY"
    elif mahanalobis >= 3 and mahanalobis <= 5: #use GPS in kalman filter, but monitor it for further anomalies
        gps_state = "FLAGGED"
        trn_state = "STANDBY"
    else:
        if terrain_error < 500:   # confidence threshold
            gps_state = "ELIMINATED"
            trn_state = "IN_KF"
        else:
            gps_state = "FLAGGED"


    print("Predicted Terrain Index:\t", predicted_index)
    print("Matched Terrain Index:\t\t", trn_index)
    print("Terrain Error:\t\t\t", terrain_error)
    print("TRN Position:\t\t\t", trn_x)
    print("")


    #UPDATE VARIABLES FOR THE NEXT TIMESTEP



    # -------------------------
    # UPDATES FOR NEXT TIMESTEP
    # -------------------------

    x_i = real_x
    v_i = real_v

    timestep_data = {
        "Real Position": real_x, #real position of the plane (kinematics)
        "Real Velocity": real_v, #real velocity of the plane (kinematics)
        "Measured Elevation": measured_elevation, #current elevation at timestep x
        "Expected Elevation": expected_terrain_map[i], #expected elevation at timestep x
        "GPS Position": gps_x, #GPS reading
        "TRN Position": trn_x, #TRN reading
        "Predicted Position": predicted_position, #IRS position is the predicted positon (uses physics)
        "Predicted Velocity": predicted_velocity,
        "Updated Position": updated_position, #Uses sensor data + IRS data to estimate positon of plane (aka. kalman filter position estimate)
        "Updated Velocity": updated_velocity,
        "Position Residual": residual[0][0], #difference between predicted position (IRS positon) and sensor position
        "Innovation Covariance": innovation_covarience[0][0], #what the residual should statistically be given the state of the plane
        "Mahanalobis": mahanalobis[0][0], #how alarming the anomaly is (basically tells us if there's anything sus with the GPS or sensors)
        "GPS State": gps_state,
        "TRN State": trn_state
    }
    timestep_data_collection.append(timestep_data)
    print(tabulate(timestep_data.items(), headers=["Variable", "Value"]))



def return_timestep_data():
    return timestep_data_collection

