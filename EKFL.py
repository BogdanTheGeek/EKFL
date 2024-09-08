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

# Spacing between columns (for split printing)
spacing = 0

nozzleDiameter = 0.4
layerHeight = 0.2

threadedInsertDiameter = 4.1
threadedInsertLength = 5.7

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

    body = None  # Cache

    def create(self) -> bd.Part:
        if Switch.body:
            return Switch.body

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

        Switch.body = (body, bd.Pos(0, 0, self.stemHeight - 3) * cap.body)
        return Switch.body


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

    body = None  # Cache

    def __init__(self, convex=0):
        self.convex = convex
        self.locatorWidth = nozzleDiameter * 3 + (convex * 0.5)

    def create(self) -> bd.Part:
        if Plate.body:
            return Plate.body

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

        Plate.body = body
        return body


class Flange:
    length = Plate.columnPitch
    width = 8
    height = Plate.thickness
    diameter = 3
    clearance = 0.2

    body = None  # Cache

    def create(self) -> bd.Part:
        if Flange.body:
            return Flange.body

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

        Flange.body = body
        return body


class Board:
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

        if self.radius == 0:
            # Flat
            def move(i: int, b: bd.Part) -> bd.Part:
                return bd.Pos(0, i * Plate.switchPitch, 0) * b

            plates = tuple((move(i, Plate().create()) for i in range(self.keys)))
            switches = (
                move(i, b) for b in tuple(Switch().create()) for i in range(self.keys)
            )
        else:
            # Curved
            def move(i: int, b: bd.Part) -> bd.Part:
                return (
                    bd.Rot(
                        self.angle * (i - self.offset - centerOffset),
                        0,
                        0,
                    )
                    * bd.Pos(0, 0, -self.radius)
                    * b
                )

            plates = tuple((move(i, Plate().create()) for i in range(self.keys)))
            switches = (
                move(i, b) for b in tuple(Switch().create()) for i in range(self.keys)
            )

        # Flanges
        if self.radius == 0:
            flanges = (
                bd.Pos(0, -(Flange.width + Plate.switchPitch) / 2.0, 0)
                * Flange().create(),
                bd.Pos(0, (self.keys - 0.5) * Plate.switchPitch + Flange.width / 2.0, 0)
                * Flange().create(),
            )
        else:
            cornerRadius = sqrt(
                (self.radius + Plate.thickness) ** 2 + (Plate.switchPitch / 2.0) ** 2
            )
            if self.radius < 0:
                cornerRadius = -cornerRadius

            leftIndex = -self.offset - centerOffset - 0.5
            rightIndex = self.keys - self.offset - centerOffset - 0.5
            flanges = (
                bd.Rot(self.angle * leftIndex, 0, 0)
                * bd.Pos(0, 0, -cornerRadius)
                * bd.Rot(-self.angle * leftIndex, 0, 0)
                * bd.Pos(0, -Flange.width / 2, Flange.height)
                * Flange().create(),  # Left
                bd.Rot(self.angle * rightIndex, 0, 0)
                * bd.Pos(0, 0, -cornerRadius)
                * bd.Rot(-self.angle * rightIndex, 0, 0)
                * bd.Pos(0, Flange.width / 2, Flange.height)
                * Flange().create(),  # Right
            )

        board = bd.Part() + plates + flanges
        return (board, *switches)


class Support:
    columnWidth = Flange.width
    columnDepth = Flange.length

    contactWidth = 1
    contactHeight = 3

    width = 3.6
    depth = columnDepth - 4

    # TODO: Look into algorithm for calculating the number of supports
    postsForKeys = (0, 0, 1, 2, 1, 2, 3, 4)

    def __init__(self, plates: bd.Part, board: Board):
        self.plate = plates
        self.board = board

        screwHoles = (
            plates.edges()
            .filter_by(bd.GeomType.CIRCLE)
            .filter_by(lambda e: e.radius > POS_REF_LEN)  # Filter out references
            .sort_by(bd.Axis.Y)[0::2]
            .sort_by(bd.Axis.Z)
        )
        self.colPos: Tuple[bd.Vector, ...] = tuple(
            (hole.position for hole in screwHoles)
        )

        refEdges = (
            plates.edges()
            .filter_by(bd.GeomType.LINE)
            .filter_by(lambda e: e.length <= POS_REF_LEN)
            .sort_by(bd.Axis.Y)[0:-1]
        )

        print(f"Creating supports for {board.keys} keys")

        supports = self.postsForKeys[board.keys]
        diff = (len(refEdges) - supports) // 2
        if diff > 0:
            refEdges = refEdges[diff:-diff]

        if supports != len(refEdges):
            raise ValueError(
                f"Number of supports({supports}) != number of references({len(refEdges)})"
            )

        self.refPos = tuple((ref @ 0 for ref in refEdges))

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

        self.refAngles = tuple(
            (get_angle_ZY(edge) + board.angle / 2 for edge in refEdges)
        )

        if len(self.refAngles) != len(self.refPos):
            raise ValueError(
                f"angles({len(self.refAngles)}) != positions({len(self.refPos)})"
            )

        zPos = tuple((*(c.Z for c in self.colPos), *(r.Z for r in self.refPos)))
        bottom = min(zPos)
        self.bottom = bottom

        self.colHeight: Tuple[float, ...] = (
            10 + self.colPos[0].Z - bottom,
            10 + self.colPos[1].Z - bottom,
        )

    def create(self) -> bd.Part:
        body = bd.Part()
        # columns
        for i in range(len(self.colPos)):
            pos = self.colPos[i]
            height = self.colHeight[i]
            body += bd.Pos(pos) * (
                bd.Box(
                    self.columnDepth,
                    self.columnWidth,
                    height,
                    align=TOP_REF,
                )
                - bd.Cylinder(
                    threadedInsertDiameter / 2,
                    threadedInsertLength,
                    align=TOP_REF,
                )
            )
        # supports
        for i in range(len(self.refPos)):
            pos = self.refPos[i]
            angle = self.refAngles[i]
            contact = (
                bd.Pos(pos)
                * bd.Rot(angle)
                * bd.Box(
                    self.depth,
                    self.contactWidth,
                    self.contactHeight + self.contactWidth,
                    align=TOP_REF,
                )
            )
            angleRad = angle * pi / 180
            contactEnd = (
                pos + bd.Vector(0, -sin(angleRad), cos(angleRad)) * -self.contactHeight
            )
            support = bd.Pos(contactEnd) * bd.Box(
                self.depth,
                self.width,
                10 + contactEnd.Z - self.bottom,
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
        baseLength = abs(self.colPos[0].Y - self.colPos[1].Y) + Flange.width
        yRef = min((p.Y for p in self.colPos)) - Flange.width / 2
        REF = (bd.Align.CENTER, bd.Align.MIN, bd.Align.MAX)
        body += bd.Pos(0, yRef, self.bottom - 10) * bd.Box(
            self.columnDepth, baseLength, 1, align=REF
        )

        return body


class Keypad:
    def __init__(self):
        pinky = 0
        ring = 1
        middle = 2
        index = 3

        fingerLength = (45, 50, 55, 48, 35)
        fingerLenghtOffset = (0, 15, 21, 15, -25)
        baseRadius = 23
        columnOffsetFactor = 0.3

        self.fingerRadius = tuple(
            (baseRadius + fingerLength[i] + fingerLenghtOffset[i] for i in range(5))
        )

        self.columnOffset = tuple(
            (self.fingerRadius[i] * columnOffsetFactor for i in range(5))
        )

        self.columns = (pinky, pinky, ring, middle, index, index)
        self.keys = (4, 4, 5, 5, 4, 4)
        self.keysOffset = (1, 1, 2.5, 2.5, 1, 1)

        assert len(self.columns) == len(self.keys) == len(self.keysOffset)

    def create(self) -> Tuple[bd.Part, ...]:
        columns = []
        for i in range(len(self.columns)):
            keys = self.keys[i]
            keysOffset = self.keysOffset[i]
            finger = self.columns[i]
            radius = self.fingerRadius[finger]

            brd = Board(keys, radius, keysOffset)
            board, *switches = brd.create()
            support = Support(board, brd).create()

            bottom = min((p.Z for p in support.vertices()))
            columnOffset = self.columnOffset[finger]

            pos = (i * (Plate.columnPitch + spacing), columnOffset, -bottom)

            column = [
                (bd.Pos(pos) * support),
                (bd.Pos(pos) * board),
                tuple((bd.Pos(pos) * s for s in switches)),
            ]

            columns.append(column)

        return columns


class Module:
    keypad = Keypad().create()


print("Unpacking keypad")

supports = tuple((column[0] for column in Module.keypad))
columns = tuple((column[1] for column in Module.keypad))
switches = tuple((column[2] for column in Module.keypad))

print("Done")


# view.set_defaults(measure_tools=True)
if 1:
    view.set_colormap(view.ColorMap.seeded(colormap="rgb", alpha=1))
    view.show_all(reset_camera=view.Camera.KEEP, timeit=True)
