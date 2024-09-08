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
from math import atan, pi, sqrt, cos, sin

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

POS_REF_LEN = 0.05


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

        # Reference
        body += bd.Pos(0, self.switchPitch / 2, -self.thickness - 0.5) * bd.Cylinder(
            POS_REF_LEN, POS_REF_LEN
        )

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
    column_width = Flange.width
    column_depth = Flange.length

    contact_width = 1
    contact_height = 3

    width = 3.6

    # TODO: Look into algorithm for calculating the number of supports
    postsForKeys = (0, 0, 1, 2, 1, 2, 3, 4)

    def __init__(self, plates: bd.Part, col: Column):
        self.plate = plates
        self.col = col

        screw_holes = (
            plates.edges()
            .filter_by(bd.GeomType.CIRCLE)
            .filter_by(lambda e: e.radius > POS_REF_LEN)  # Filter out references
            .sort_by(bd.Axis.Y)[0::2]
            .sort_by(bd.Axis.Z)
        )
        self.col_pos: Tuple[bd.Vector, ...] = tuple(
            (hole.position for hole in screw_holes)
        )

        ref_edges = (
            plates.edges()
            .filter_by(bd.GeomType.LINE)
            .filter_by(lambda e: e.length <= POS_REF_LEN)
            .sort_by(bd.Axis.Y)[0:-1]
        )

        supports = self.postsForKeys[col.keys]
        diff = (len(ref_edges) - supports) // 2
        if diff > 0:
            ref_edges = ref_edges[diff:-diff]

        if supports != len(ref_edges):
            raise ValueError(
                f"Number of supports({supports}) != number of references({len(ref_edges)})"
            )

        self.ref_pos = tuple((ref @ 0 for ref in ref_edges))

        def get_angle_ZY(edge: bd.Edge) -> float:
            """
            Calculate the angle between the Z and Y axis of an edge
            Returns the angle in degrees
            """
            start = edge @ 0
            end = edge @ 1
            z = end.Z - start.Z
            y = end.Y - start.Y
            return -atan(y / z) * (180 / pi)

        self.ref_angles = tuple(
            (get_angle_ZY(edge) + col.angle / 2 for edge in ref_edges)
        )

        if len(self.ref_angles) != len(self.ref_pos):
            raise ValueError(
                f"angles({len(self.ref_angles)}) != positions({len(self.ref_pos)})"
            )

        z_pos = tuple((*(c.Z for c in self.col_pos), *(r.Z for r in self.ref_pos)))
        bottom = min(z_pos)
        self.bottom = bottom

        self.col_h: Tuple[float, ...] = (
            10 + self.col_pos[0].Z - bottom,
            10 + self.col_pos[1].Z - bottom,
        )

    def create(self) -> bd.Part:
        body = bd.Part()
        # columns
        for i in range(len(self.col_pos)):
            pos = self.col_pos[i]
            height = self.col_h[i]
            body += bd.Pos(pos) * bd.Box(
                self.column_depth, self.column_width, height, align=TOP_REF
            )
        # supports
        for i in range(len(self.ref_pos)):
            pos = self.ref_pos[i]
            angle = self.ref_angles[i]
            contact = (
                bd.Pos(pos)
                * bd.Rot(angle)
                * bd.Box(
                    self.column_depth,
                    self.contact_width,
                    self.contact_height + self.contact_width,
                    align=TOP_REF,
                )
            )
            angle_rad = angle * pi / 180
            contact_end = (
                pos
                + bd.Vector(0, -sin(angle_rad), cos(angle_rad)) * -self.contact_height
            )
            support = bd.Pos(contact_end) * bd.Box(
                self.column_depth,
                self.width,
                10 + contact_end.Z - self.bottom,
                align=TOP_REF,
            )
            support += contact

            def fequal(a, b, tol=1e-6):
                return abs(a - b) < tol

            # Chamfers
            edges = (
                support.edges()
                .filter_by(bd.GeomType.LINE)
                .filter_by(bd.Axis.X)
                .sort_by(bd.Axis.Z)[2:-2]
                .sort_by(bd.Axis.Y)[1:-1]
            )
            for edge in edges:
                try:
                    support += bd.chamfer(edge, 1.0)
                except Exception as e:
                    print(f"Failed to chamfer: {e}")
            body += support

        # bottom plate
        base_length = abs(self.col_pos[0].Y - self.col_pos[1].Y) + Flange.width
        y_ref = min((p.Y for p in self.col_pos)) - Flange.width / 2
        REF = (bd.Align.CENTER, bd.Align.MIN, bd.Align.MAX)
        body += bd.Pos(0, y_ref, self.bottom - 10) * bd.Box(
            self.column_depth, base_length, 1, align=REF
        )

        return body


threadedInsertDiameter = 4.1
threadedInsertLength = 5.7

# plate = Plate().create()
# flange = Flange().create()
# column = Column(5, -50).create()
col = Column(6, 80, 2)
plate_col, *switches = col.create()
support = Support(plate_col, col).create()


# view.set_defaults(measure_tools=True)
if 1:
    view.set_colormap(view.ColorMap.seeded(colormap="rgb", alpha=1))
    view.show_all(reset_camera=view.Camera.KEEP, timeit=True)
