#!/usr/bin/env python3

# EKFL keyboard
#
# Copyright (C) 2023 Bogdan Ionescu
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import build123d as bd
import ocp_vscode as view
from math import atan, pi, sqrt

from typing import Tuple

showSwitches = True
showKeys = True
printView = False  # Set to true to quicky show only printable parts
threadedInserts = True

# Spacing between columns (for split printing)
spacing = 0

nozzleDiameter = 0.4
layerHeight = 0.2

TOP_REF = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX)
BOTTOM_REF = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)


class CapSTL:
    body = bd.import_stl("assets/DSA 1u LR.stl")


cap = CapSTL()


class Switch:
    holeWidth = 14.0
    holeHeight = 5.0
    stemDiameter = 4.0
    stemHeight = holeHeight + 3.5
    width = 15.5
    lipHeight = 0.75
    faceWidth = 12.0
    faceLength = 10.0
    faceHeight = 6.0
    faceOffset = 3.5 / 2
    actuatorWidth = 7.2
    actuatorLength = 5.5
    actuatorHeight = 10.5

    def create(self) -> bd.Part:
        # Base
        body = bd.Box(
            self.width,
            self.holeWidth,
            self.holeHeight,
            align=TOP_REF,
        )
        # Stem
        body += bd.Cylinder(
            self.stemDiameter / 2,
            self.stemHeight,
            align=TOP_REF,
        )
        # Actuator
        body += bd.Box(
            self.actuatorWidth,
            self.actuatorLength,
            self.actuatorHeight,
            align=BOTTOM_REF,
        )
        # Case
        lip = bd.Box(
            self.width,
            self.width,
            self.lipHeight,
            align=BOTTOM_REF,
        )
        body += lip

        bottom = lip.faces().sort_by(bd.Axis.Z)[-1]

        top = bd.Pos(
            0,
            self.faceOffset,
            self.faceHeight + self.lipHeight,
        ) * bd.Rectangle(
            self.faceWidth,
            self.faceLength,
        )
        body += bd.loft((top, bottom))

        return (body, bd.Pos(0, 0, self.stemHeight - 3) * cap.body)


class SwitchAssembly:
    bodies = Switch().create()


class Plate:
    convex = 0
    width = Switch.holeWidth
    thickness = 1.5

    switchSpacing = 7.0
    columnSpacing = 5.0

    switchPitch = Switch.holeWidth + switchSpacing
    columnPitch = Switch.holeWidth + columnSpacing

    locatorWidth = nozzleDiameter * 3 + (convex * 0.5)
    locatorHeight = thickness
    locatorLength = columnPitch - 6.0

    def __init__(self, convex=0):
        self.convex = convex
        self.locatorWidth = nozzleDiameter * 3 + (convex * 0.5)

    def create(self) -> bd.Part:
        # Plate

        cut_width = (self.thickness - layerHeight) / 2
        profile = (
            (-self.switchPitch / 2, 0),  # Bottom Left
            (self.switchPitch / 2, 0),  # Bottom Right
            (self.switchPitch / 2, layerHeight),  # Right V-Cut
            (self.switchPitch / 2 - cut_width, self.thickness),  # Top Right
            (-self.switchPitch / 2 + cut_width, self.thickness),  # Top Left
            (-self.switchPitch / 2, layerHeight),  # Left V-Cut
            (-self.switchPitch / 2, 0),  # Bottom Left
        )

        sketch = bd.make_face(bd.Plane.YZ * bd.Polyline(*profile))
        body = (
            bd.Pos(self.columnPitch / 2, 0, -self.thickness)
            * bd.extrude(sketch, -self.columnPitch).clean()
        )
        # Hole
        body -= bd.Box(
            self.width,
            self.width,
            self.thickness,
            align=TOP_REF,
        )
        # Legs
        legPos = (
            bd.Pos(
                0,
                -self.switchPitch / 2 + self.locatorWidth,
                -self.thickness,
            ),
            bd.Pos(
                0,
                self.switchPitch / 2 - self.locatorWidth,
                -self.thickness,
            ),
        )
        for pos in legPos:
            body += pos * bd.Box(
                self.locatorLength,
                self.locatorWidth,
                self.locatorHeight,
                align=TOP_REF,
            )

        # Reference edge
        body += bd.Pos(0, self.switchPitch / 2, -self.thickness - 0.5) * bd.Sphere(0.05)

        return body


class Flange:
    length = Plate.columnPitch
    width = 8
    height = Plate.thickness
    diameter = 3
    clearance = 0.2

    def create(self) -> bd.Part:
        cut_width = (self.height - layerHeight) / 2
        profile = (
            (-self.width / 2, 0),  # Bottom Left
            (self.width / 2, 0),  # Bottom Right
            (self.width / 2, layerHeight),  # Right V-Cut
            (self.width / 2 - cut_width, self.height),  # Top Right
            (-self.width / 2 + cut_width, self.height),  # Top Left
            (-self.width / 2, layerHeight),  # Left V-Cut
            (-self.width / 2, 0),  # Bottom Left
        )

        sketch = bd.make_face(bd.Plane.YZ * bd.Polyline(*profile))
        body = bd.Pos(self.length / 2, 0, -self.height) * bd.extrude(
            sketch, -self.length
        )
        body -= bd.Cylinder(
            self.diameter / 2 + self.clearance,
            self.height * 2,
        )

        return body


class Column:
    def __init__(self, keys: int, radius=0, offset=2):
        self.keys = keys
        self.radius = radius
        self.offset = offset
        self.angle = (
            2.0
            * atan((Plate.switchPitch / 2.0) / (self.radius + Plate.thickness))
            * (180 / pi)
        )

        totalAngle = self.angle * keys

        if -165 > totalAngle > 265:
            raise ValueError(
                "Radius too small for the number of keys, flanges will collide with pillar locks"
            )

    def create(self) -> Tuple[bd.Part, ...]:
        centerOffset = 0.5 if self.keys % 2 == 0 else 0

        body = bd.Part()

        switches = []

        for i in range(self.keys):
            if self.radius == 0:
                # Flat
                pos = bd.Pos(0, i * Plate.switchPitch, 0)
                body += pos * Plate().create()
                for b in SwitchAssembly.bodies:
                    switches.append(pos * bd.copy.copy(b))
            else:
                transformation = bd.Rot(
                    self.angle * (i - self.offset - centerOffset),
                    0,
                    0,
                ) * bd.Pos(0, 0, -self.radius)
                plate = transformation * Plate().create()
                body += plate
                for b in SwitchAssembly.bodies:
                    switches.append(transformation * bd.copy.copy(b))
        # Flanges
        if self.radius == 0:
            body += (
                bd.Pos(0, -(Flange.width + Plate.switchPitch) / 2.0, 0)
                * Flange().create()
            )
            body += (
                bd.Pos(0, (self.keys - 0.5) * Plate.switchPitch + Flange.width / 2.0, 0)
                * Flange().create()
            )
        else:
            cornerRadius = sqrt(
                (self.radius + Plate.thickness) ** 2 + (Plate.switchPitch / 2.0) ** 2
            )
            if self.radius < 0:
                cornerRadius = -cornerRadius

            leftIndex = -self.offset - centerOffset - 0.5
            body += (
                bd.Rot(self.angle * leftIndex, 0, 0)
                * bd.Pos(0, 0, -cornerRadius)
                * bd.Rot(-self.angle * leftIndex, 0, 0)
                * bd.Pos(0, -Flange.width / 2, Flange.height)
                * Flange().create()
            )
            rightIndex = self.keys - self.offset - centerOffset - 0.5
            body += (
                bd.Rot(self.angle * rightIndex, 0, 0)
                * bd.Pos(0, 0, -cornerRadius)
                * bd.Rot(-self.angle * rightIndex, 0, 0)
                * bd.Pos(0, Flange.width / 2, Flange.height)
                * Flange().create()
            )

        return (body, *switches)


class Support:
    width = Flange.width
    length = Flange.length

    def __init__(self, plate: bd.Part):
        self.plate = plate

        screw_holes = (
            plate.edges()
            .filter_by(bd.GeomType.CIRCLE)
            .filter_by(lambda e: e.radius > 0.5)  # Filter out reference spheres
            .sort_by(bd.Axis.Y)[0::2]
            .sort_by(bd.Axis.Z)
        )
        self.col_pos: Tuple[bd.Vector, ...] = tuple(
            (hole.position for hole in screw_holes)
        )

        refs = (
            plate.edges()
            .filter_by(bd.GeomType.CIRCLE)
            .filter_by(lambda e: e.radius < 0.5)  # Filter for reference spheres
            .sort_by(bd.Axis.Y)[:-1]
        )
        self.ref_pos: Tuple[bd.Vector, ...] = tuple((ref.position for ref in refs))

        z_pos = tuple((*(c.Z for c in self.col_pos), *(r.Z for r in self.ref_pos)))
        bottom = min(z_pos)
        self.bottom = bottom

        self.col_h: Tuple[float, ...] = (
            10 + self.col_pos[0].Z - bottom,
            10 + self.col_pos[1].Z - bottom,
        )
        self.ref_h: Tuple[float, ...] = tuple((10 + r.Z - bottom for r in self.ref_pos))

    def create(self) -> bd.Part:
        body = bd.Part()
        # columns
        for i in range(len(self.col_pos)):
            pos = self.col_pos[i]
            height = self.col_h[i]
            body += bd.Pos(pos) * bd.Box(self.length, self.width, height, align=TOP_REF)
        # supports
        for i in range(len(self.ref_pos)):
            pos = self.ref_pos[i]
            height = self.ref_h[i]
            body += bd.Pos(pos) * bd.Box(self.length, 1, height, align=TOP_REF)
        # TODO: angle supports and add base

        # bottom plate
        width = abs(self.col_pos[0].Y - self.col_pos[1].Y) + Flange.width
        y_ref = self.col_pos[0].Y - Flange.width / 2
        REF = (bd.Align.CENTER, bd.Align.MIN, bd.Align.MAX)
        body += bd.Pos(0, y_ref, self.bottom - 10) * bd.Box(
            self.length, width, 1, align=REF
        )

        return body


threadedInsertDiameter = 4.1
threadedInsertLength = 5.7

# plate = Plate().create()
# flange = Flange().create()
# column = Column(5, -50).create()
plate, *switches = Column(5, 80, 0).create()
support = Support(plate).create()


# view.set_defaults(measure_tools=True)
if 1:
    view.set_colormap(view.ColorMap.seeded(colormap="rgb", alpha=1))
    view.show_all(reset_camera=view.Camera.KEEP, timeit=True)
