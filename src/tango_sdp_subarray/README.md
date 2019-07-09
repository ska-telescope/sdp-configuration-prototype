# SDPSubarray

## Requirement

- PyTango >= 8.1.6
- devicetest (for using tests)
- sphinx (for building sphinx documentation)

## Installation

Run python setup.py install

If you want to build sphinx documentation,
run python setup.py build_sphinx

If you want to pass the tests, 
run python setup.py test

## Usage

Now you can start your device server in any
Terminal or console by calling it :

SDPSubarray instance_name

## WIP: Quick start

### Run tests

```bash
make test
```

### Build the image

```bash
make build
```

### Test interactively with a Tango facility

- Start the tangods and databaseds containers.
- This can be done by using the command `make up` in the `deploy/docker-compose`
- Register devices with the database using `make register <N>` where `<N>` is
  the number of devices to register
- Start the SDPSubarray devices using `make start`
- Start a iTango container with `make start itango` from the
  `deploy/docker-compose` folder
- Obtain an itango prompt with `docker exec -it itango itango3` from the
  `deploy/docker-compose` folder
- check the device list with `lsdev`
- get a device handle with `d = DeviceProxy('mid_sdp/elt/subarray_00')`
- check the device state with `d.state()`... this should be `DevState.OFF`
- check the obsState with `d.obsState`
- assign resources with `d.AssignResources('')`
- reinitialise `d.Init()`   
 
