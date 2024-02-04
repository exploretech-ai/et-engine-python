# ET-Engine

The main API for developing and running probabilistic computing algorithms

## Installation:

```
conda create -n et-engine python=3.8
conda activate et-engine
pip install -e et-engine
```

Run the dev script with:

```
python et-engine/dev.py
```

## Deploying infra

Make sure you have the aws cdk installed
```
cd et-engine-api
cdk synth
cdk deploy
```

Test updates with the dev script

```
python ../et-engine/dev.py
```
