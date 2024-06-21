# FDS Python SDK

This package contains the Python Software Development Kit (SDK) of space**tower**™.

space**tower**™ is Exotrail's Flight Dynamics System (FDS). It covers all the needs of the flight dynamics engineer, including but not limited to :
- Orbit Determination using PV (Position-Velocity) or GPS NMEA measurements;
- Measurement Generation;
- Event prediction e.g. station passes;
- Generation and simulation of maneuvers e.g. for orbit raising;
- Uncertainties evaluation for all of these cases.

The Python SDK brings these features to you through a set of Python modules directly callable in your scripts. These modules interacts with the public Application Programming Interface (API) of space**tower**™ available online.


## Contents

- [Installation instructions](#installation-instructions)
    - [Prerequisites](#prerequisites)
    - [Step-by-step installation](#step-by-step-installation)
- [Features overview](#features-overview)
    - [Orbit Extrapolation](#orbit-extrapolation)
    - [Orbit Determination](#orbit-determination)
    - [Maneuver Generation](#maneuver-generation)
- [Documentation](#documentation)
- [Dependencies](#dependencies)
- [Contact](#contact)
- [License](#license)
- [Version history](#version-history)


## Installation instructions

### Prerequisites

In order to use the Python SDK of space**tower**™, you need to have Python 3.11 or higher installed, with a package manager like pip or poetry. 

The procedure described hereafter also requires the use of a Command Line Interface (CLI).

API credentials are required to call the space**tower**™ API. If you do not have credentials yet, please register at https://portal.exotrail.space.

### Step-by-step installation

It is recommended to use a virtual environment to install the SDK.
This will prevent conflicts with other Python packages that may be installed on the system.

To create a virtual environment:
```bash
$ python -m venv venv
```
Based on your operating system, you will have to activate the virtual environment differently. For Windows, you can use the following command :
```bash 
$ .\.venv\Scripts\activate
``` 
or if you want to use the Powershell script:
```bash 
$ .\.venv\Scripts\Activate.ps1
``` 
For Unix-based systems, you can use : 
```bash 
$ source .venv/bin/activate
```

To install the SDK :
```bash
$ pip install spacetower-fds-sdk
```

This will install the SDK and its dependencies into the virtual environment.

To set up the API credentials, you can use the following command:
```python
from fds.config import set_client_id, set_client_secret
set_client_id("your_client_id")
set_client_secret("your_client_secret")
```

## Features Overview

### Orbit extrapolation

In its simplest use, given an initial state and a target time, the SDK can call the API points of space**tower**™ exposed online to request the propagation of the state to the target time.

Additional parameters can be passed to the `OrbitExtrapolation` class to perform more complex operations, such as:

- Find orbital events (e.g. eclipse entry/exit, ascending and descending nodes, etc.)
- Find station visibility windows (e.g. when a ground station, defined by the user, can see the satellite)
- Find events related to sensors (e.g. find windows where the Sun is in the field of view of a camera)
- Generate simulated measurements (e.g. GPS NMEA, position and velocity, radar, etc.)
- Generate output ephemerides of various types (e.g. Cartesian, Keplerian, attitude, etc.). Cartesian ephemerides can be also produced in the Orbit Ephemerides Message (OEM) format.
- Propagate the state covariance matrix
- Simulate attitude and/or trajectory changes through maneuver roadmaps.

### Orbit determination

The SDK of space**tower**™ can perform orbit determination by calling the API points to request the estimation of the state of the satellite, given an initial state, a set of measurements and configuration parameters. An Unscented Kalman Filter (UKF) is used to perform the estimation.
The class `OrbitDetermination` provides a simple interface to the API.

Additionally, users can add model parameters to the estimation, i.e. the drag coefficient, the reflectivity coefficient and the thrust scale factors. Providing a maneuver roadmap will also allow the SDK to characterise the maneuvers that have been performed (in terms of mean variations of the state and thrust magnitude and direction).

### Maneuver generation

The maneuver generation functionality allows users to generate a maneuver roadmap that can be used in the orbit extrapolation and orbit determination functionalities. Several parameters can be passed to the `ManeuverGeneration` class to generate the roadmap, definining the desired strategy and constraints (through the `ManeuverStrategy` object) and targets (e.g. change of semi-major axis, inclination, etc.).

### Additional features

The SDK also provides additional functionalities in support of the main operations, such as:

- Two-line element (TLE) handling
- NMEA sentences parsing
- Vector operations
- Frame transformations
- Quaternion operations
- Orbital mechanics calculations

## Documentation

An online documentation of the Python SDK of space**tower**™ can be accessed at : https://docs.spacetower.exotrail.space/python-sdk/index.html

It includes docstrings description of the various modules of the SDK, to which you can refer to when using space**tower**™ in your projects.

Furthermore, a set of demonstration notebooks using *Jupyter* are available here: https://github.com/exotrail/spacetower-notebooks 

These notebooks aim at being resources for new users to understand how the SDK is built, as well as showcasing the performances of space**tower**™. They cover the most frequent use cases of an FDS.

An online version of the notebooks can be found on our customer portal: https://portal.exotrail.space

## Dependencies

As mentioned in the Getting started section, this demonstration package is written using Python 3.11, and relies on pip for installing dependencies. Said dependencies can be found in the *pyproject.toml* file of this package.

## Contact

To get in touch with us, please send a mail to the Flight Dynamics Support service at 
fds-support@exotrailspace.onmicrosoft.com

 ## License

This package is distributed under the MIT License. You are free to use, modify, and distribute the software as you see fit, provided that the original copyright notice and this permission notice are included in all copies or substantial portions of the software. The software is provided "as is," without warranty of any kind, express or implied. For more details, please refer to the LICENSE file included in this repository.

## Version history

**[1.1.0]** 2024-06-21
- Added firing constraints to the `ManeuverGeneration` class

**[1.0.0]** 2024-05-31
- Initial release
    - Coverage of the main use cases og space**tower**™ API: Orbit Extrapolation, Orbit Determination, Maneuver Generation
