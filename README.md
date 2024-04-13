# neodenCircuitStudio

neodenCircuitStudio is a Python3 script for converting Circuit Studio pick and place file output into a NeoDen 3V / 4 machine compatible file.

## Installation

Use python script near your csv file output / or wherever is convenient --its a single file.


## Usage

Generate your Pick and place file from either Circuit Studio or Altium.  Select CSV, metric output.

Load your PCB on the PNP.  Move nozzle/camera x,y to first component listed in your CSV file, write down those coordinates.

```console

python neodenCStudio.py yourpnpoutputfile.csv

The script will ask for the x,y coordinates for the first component listed
then it will generate a *-NEODEN.csv file to take to the PNP machine

```

For using neoden3vAltium - read help topic first (-h or --help). 
1) generate config files from your .CSV file using -fp and -cl flags
2) change *FOOTPRINT.csv file for correct angle between lib and position in component tape
3) change *PARTS.csv file for config groups component type - feeder - nozzle
4) make Neoden3V compatible file using previous files using -cf and -feed flags
4.1) use -flip flag while generating for flip coordinates on the bottom side

## Contributing
This was derived from work done by Michael Moskie 2018--I merely altered it for CS pnpfiles and updated a couple of python 3 commands
Updated for NeoDen3V and tested for operation by Georgy Evdokimov in the summer of 2023
