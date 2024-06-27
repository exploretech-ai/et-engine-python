#!/usr/bin/env python3
import yaml
import os
import aws_cdk as cdk

from et_engine_api.et_engine_api_stack import ETEngine

app = cdk.App()

env = app.node.try_get_context("env")
config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), f'env/{env}.yml')
with open(config_file_path) as stream:
    config = yaml.safe_load(stream)

ETEngine(app, "ETEngine", config)
app.synth()