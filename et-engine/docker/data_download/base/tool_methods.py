from flask import Blueprint, Response
import os
from . import EFS_MOUNT_POINT, LOGGER

tools = Blueprint('tools', __name__)


@tools.route('/tools', methods=['GET'])
def list_tools():
    pass


@tools.route('/tools', methods=['POST'])
def create_tool():
    pass


@tools.route('/tools', methods=['DELETE'])
def delete_tool():
    pass


@tools.route('/tools/<toolID>', methods=['GET'])
def describe_tool():
    pass


@tools.route('/tools/<toolID>', methods=['POST'])
def execute_tool():
    pass


@tools.route('/tools/<toolID>', methods=['PUT'])
def build_tool():
    pass


@tools.route('/tools/<toolID>/share', methods=['POST'])
def share_tool():
    pass


