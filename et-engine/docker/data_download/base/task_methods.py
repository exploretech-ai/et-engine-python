from flask import Blueprint, Response
import os
from . import EFS_MOUNT_POINT, LOGGER

tasks = Blueprint('tasks', __name__)


@tasks.route('/tasks', methods=['GET'])
def list_tasks():
    pass


@tasks.route('/tasks', methods=['POST'])
def create_task():
    pass


@tasks.route('/tasks', methods=['DELETE'])
def clear_tasks():
    pass


@tasks.route('/tasks/<taskID>', methods=['GET'])
def describe_task(taskID):
    pass
