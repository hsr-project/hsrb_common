#!/usr/bin/env python
# Copyright (c) 2026 TOYOTA MOTOR CORPORATION
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted (subject to the limitations in the disclaimer
# below) provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the copyright holder nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY THIS
# LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
# vim: fileencoding=utf-8 :
import glob
import os
import subprocess
import tempfile
import unittest


try:
    import xml.etree.cElementTree as etree
except Exception:
    import xml.etree.ElementTree as etree


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROBOTS_DIR = os.path.join(PACKAGE_DIR, 'robots')
URDF_DIR = os.path.join(PACKAGE_DIR, 'urdf')


class UrdfTestCase(unittest.TestCase):
    def test_generator_robot_urdf(self):
        def test_robot_urdf(path):
            u"""Test to verify if it can be correctly read as URDF after being converted with XACRO"""
            with tempfile.NamedTemporaryFile() as f:
                args = ['ros2', 'run', 'xacro', 'xacro', source]
                self.assertEqual(subprocess.call(args, stdout=f), 0)
                args = ['check_urdf', f.name]
                subprocess.check_output(args)

        matched = glob.glob(ROBOTS_DIR + '/*.urdf.xacro')
        sources = [os.path.abspath(path) for path in matched]
        for source in sources:
            test_robot_urdf(source)

    def test_generator_integrity(self):
        def check_integrity(source):
            args = ['ros2', 'run', 'xacro', 'xacro', source]
            urdf = subprocess.check_output(args)
            root = etree.fromstring(urdf)

            links = []
            for link in root.findall('link'):
                name = link.get('name')
                self.assertIsNotNone(name, 'link({0})'.format(name))
                links.append(name)

            joints = []
            for joint in root.findall('joint'):
                name = joint.get('name')
                self.assertIsNotNone(name, 'joint({0})'.format(name))
                joints.append(name)
                parent = joint.find('parent')
                self.assertIn(parent.get('link'), links, 'joint({0})'.format(name))
                child = joint.find('child')
                self.assertIn(child.get('link'), links, 'joint({0})'.format(name))

            for trans in root.findall('transmission'):
                name = trans.get('name')
                joint = trans.find('joint')
                self.assertIn(joint.get('name'), joints, 'transmission({0})'.format(name))

            for gazebo in root.findall('gazebo'):
                ref = gazebo.get('reference')
                if ref is None:
                    # When reference is None, <gazebo> tag is added to <robot>.
                    continue
                self.assertIn(ref, links + joints,
                              "Unresolvable reference '{0}':\n{1}".format(ref, etree.tostring(gazebo)))

        matched = glob.glob(ROBOTS_DIR + '/*.urdf.xacro')
        sources = [os.path.abspath(path) for path in matched]
        for source in sources:
            check_integrity(source)
