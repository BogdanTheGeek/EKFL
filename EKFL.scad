// EKFL keyboard

// Copyright (C) 2023 Bogdan Ionescu
// SPDX-License-Identifier: GPL-3.0-or-later

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program. If not, see <https://www.gnu.org/licenses/>.


showSwitches = true;
showKeys = true;
printView = false; // Set to true to quicky show only printable parts
threadedInserts = true;

// Spacing between columns (for split printing)
spacing = 0;

switchHoleWidth = 14;
switchHoleHeight = 5;
switchStemDiameter = 4;
switchStemHeight = switchHoleHeight + 3.5;
switchWidth = 15.5;
switchLipHeight = 0.75;
switchFaceWidth = 12;
switchFaceLength = 10;
switchFaceHeight = 6;
switchFaceOffset = 3.5;
switchActuatorWidth = 7.2;
switchActuatorLength = 5.5;
switchActuatorHeight = 10.5;

switchSpacing = 7;
columnSpacing = 5;
switchPitch = switchHoleWidth + switchSpacing;
columnPitch = switchHoleWidth + columnSpacing;

plateThickness = 1.5;

nozzleDiameter = 0.4;

locatorWidth = nozzleDiameter * 3;
locatorHeight = plateThickness;
locatorLength = columnPitch - 6;

mountingFlapWidth = 8;
mountingHoleDiameter = 3;

threadedInsertDiameter = 4.1;
threadedInsertLength = 5.7;


module switch()
{
   shw = switchHoleWidth;
   shh = switchHoleHeight;
   ssd = switchStemDiameter;
   ssh = switchStemHeight;
   sw  = switchWidth;
   slh = switchLipHeight;
   sfw = switchFaceWidth;
   sfl = switchFaceLength;
   sfh = switchFaceHeight;
   sfo = switchFaceOffset;
   saw = switchActuatorWidth;
   sal = switchActuatorLength;
   sah = switchActuatorHeight;

   color("purple", 0.7)
   union()
   {
      translate([-shw/2, -shw/2, -shh])
         cube([shw, shw, shh]);
      translate([0, 0, -ssh])
         cylinder(d=ssd, h=ssh, $fn=32);
      hull()
      {
         translate([-sw/2, -sw/2, 0])
            cube([sw, sw, slh]);
         translate([-sfw/2, -sfo, slh])
            cube([sfw, sfl, sfh]);
      }
      translate([-saw/2, -sal/2, 0])
         cube([saw, sal, sah]);
   }
}

module switch_plate(convex=0)
{
   shw = switchHoleWidth;
   spw = switchPitch;
   spt = plateThickness;

   lw = locatorWidth + (convex * 0.5);
   lh = locatorHeight;
   ll = locatorLength;

   cp = columnPitch;

   difference()
   {
      translate([-cp/2, -spw/2, -spt])
         cube([cp, spw, spt]);
      translate([-shw/2, -shw/2, -(spt+1)])
         cube([shw, shw, spt+2]);
   }
   translate([-ll/2, -(spw/2 - lw/2), -(spt+lh)])
      cube([ll, lw, spt]);
   translate([-ll/2, (spw/2 - 1.5*lw), -(spt+lh)])
      cube([ll, lw, spt]);
}

module flange()
{
   length = columnPitch;
   width = mountingFlapWidth;
   height = plateThickness;
   diameter = mountingHoleDiameter + 0.2;
   translate([-length/2, 0, 0])
   difference()
   {
      cube([length, width, height]);
      translate([length/2, width/2, -1])
         cylinder(d=diameter, h=height+2, $fn=32);
   }
}

module pillar(length, width, height, diameter=0, depth=0, offset=0)
{
   translate([-length/2, 0, 0])
   difference()
   {
      cube([length, width, height]);
      translate([length/2, width/2 + offset, height-depth])
      if (threadedInserts)
      {
         cylinder(d=diameter + 0.2, h=depth+1, $fn=32);
         translate([0, 0, depth-threadedInsertLength])
            cylinder(d=threadedInsertDiameter, h=threadedInsertLength+1, $fn=32);
      }
      else
      {
         cylinder(d=diameter, h=depth+1, $fn=32);
      }
   }
}

module column_plate(keys)
{
   sp = switchPitch - 0.01;
   cp = columnPitch;
   pt = plateThickness;

   difference()
   {
      union()
      {
         for (i=[0:keys-1])
         {
            translate([0, i * sp, 0])
               switch_plate();
         }

         // Mounting Flaps
         w = mountingFlapWidth;
         translate([-cp/2, -(w + sp/2), -pt])
            difference()
            {
               cube([cp, w, pt]);
               translate([cp/2, w/2, -1])
                  cylinder(d=mountingHoleDiameter + 0.2, h=pt+2, $fn=32);
            }
         translate([-cp/2, (keys - 0.5)*sp, -pt])
            difference()
            {
               cube([cp, w, pt]);
               translate([cp/2, w/2, -1])
                  cylinder(d=mountingHoleDiameter + 0.2, h=pt+2, $fn=32);
            }
      }
      // v-cut
      for (i=[0:keys])
      {
         translate([0, (i - 0.5) * sp, 0.4])
            rotate([0, 90, 0])
               cylinder(d=mountingHoleDiameter, h=sp+1, $fn=3, center=true);
      }
   }
}

module column(keys, radius, keyOffset=2)
{
   sp = switchPitch;
   cp = columnPitch;
   pt = plateThickness;

   convex = radius < 0 ? 1 : 0;
   concave = radius > 0 ? 1 : 0;

   angle = 2*atan(sp/2 / (radius + pt));

   centerOffset =  keys % 2 == 0 ? 0.5 : 0;

   for (i=[0:keys-1])
   {
      rotate([angle * (i - keyOffset - centerOffset), 0, 0])
         translate([0, 0, -radius])
         {
            switch_plate(convex);
            if (showSwitches)
               switch();
            if (showKeys)
               translate([0, 0, 5])
                  color("white", 1)
                     import("assets/DSA 1u LR.stl", convexity=3);
                     //import("assets/XDA 1u LR.stl", convexity=3);
         }
   }

   // Mounting Flaps
   cornerRadius = sqrt((radius + pt)^2 + (sp/2)^2) * (radius < 0 ? -1 : 1);

   indexBottom = (-keyOffset - 0.5 - centerOffset);
   rotate([angle * indexBottom, 0, 0])
   translate([0, 0, -cornerRadius])
   rotate([-angle * indexBottom, 0, 0])
   mirror([0, 1, 0])
   flange();

   indexTop = (keys - keyOffset - 0.5 - centerOffset);
   rotate([angle * indexTop, 0, 0])
   translate([0, 0, -cornerRadius])
   rotate([-angle * indexTop, 0, 0])
   flange();


}

module column_support(keys, radius, keyOffset=2, postsHeight=0)
{
   ll = locatorLength;
   lw = locatorWidth;
   sp = switchPitch;
   cp = columnPitch;
   pt = plateThickness;

   angle = 2*atan(sp/2 / (radius + pt));

   centerOffset =  keys % 2 == 0 ? 0.5 : 0;

   postsForKeys = [ 0, 0, 1, 2, 1, 2, 3, 4 ];
   posts = postsForKeys[keys];

   convex = radius < 0 ? 1 : 0;
   concave = radius > 0 ? 1 : 0;

   linkClearnace = 0.2;

   cornerRadius = sqrt((radius + pt)^2 + (sp/2)^2) * (radius < 0 ? -1 : 1);

   if (posts)
   {
      for (i=[0:posts-1])
      {
         k = ((keys / 2) - keyOffset - 1) + i - (keys == 6 ? 1 : 0);
         l = cornerRadius * (1 - cos(angle * k)) + postsHeight - 3 - linkClearnace;

         rotate([angle * k, 0, 0])
            translate([0, 0, -(radius + 3 + (concave*pt) + linkClearnace)])
            {
               translate([-ll/2, -lw/2, 0])
                  cube([ll, lw, 2]);
               hull()
               {
                  translate([-ll/2, -lw/2, -linkClearnace])
                     cube([ll, lw, 1]);
                  rotate([-angle * k, 0, 0])
                     translate([0, 0, -3])
                        cube([ll, lw*3, 1], center=true);
               }
               rotate([-angle * k, 0, 0])
                  translate([-ll/2, -(lw * 3)/2, -(l + 3.5)])
                     cube([ll, lw * 3, l]);
            }
      }
   }

   // Mounting posts
   flapOffset = 1;
   w = mountingFlapWidth - flapOffset;
   depth = 10;

   indexBottom = (-keyOffset - 0.5 - centerOffset); 
   heightBottom = cornerRadius * (1 - cos(angle * indexBottom)) + postsHeight + 5 - pt;

   translate([0, -flapOffset, -heightBottom])
   rotate([angle * indexBottom, 0, 0])
   translate([0, 0, -cornerRadius])
   rotate([-angle * indexBottom, 0, 0])
   mirror([0, 1, 0])
   pillar(cp, w, heightBottom, mountingHoleDiameter, depth, -flapOffset/2);

   indexTop = (keys - keyOffset - 0.5 - centerOffset); 
   heightTop = cornerRadius * (1 - cos(angle * indexTop)) + postsHeight + 5 - pt;

   translate([0, flapOffset, -heightTop])
   rotate([angle * indexTop, 0, 0])
   translate([0, 0, -cornerRadius])
   rotate([-angle * indexTop, 0, 0])
   pillar(cp, w, heightTop, mountingHoleDiameter, depth, -flapOffset/2);
}

module base(keys, radius, keyOffset=2, postsHeight=0)
{
   ll = locatorLength;
   lw = locatorWidth;
   sp = switchPitch;
   cp = columnPitch;
   pt = plateThickness;

   angle = 2*atan(sp/2 / (radius + pt));

   centerOffset =  keys % 2 == 0 ? 0.5 : 0;
   linkClearnace = 0.2;

   // Mounting posts
   flapOffset = 1;
   w = mountingFlapWidth - flapOffset;
   depth = 10;

   cornerRadius = sqrt((radius + pt)^2 + (sp/2)^2) * (radius < 0 ? -1 : 1);

   hull()
   {
      indexBottom = (-keyOffset - 0.5 - centerOffset); 
      heightBottom = cornerRadius * (1 - cos(angle * indexBottom)) + postsHeight + 5 - pt;

      translate([0, -flapOffset, -heightBottom])
      rotate([angle * indexBottom, 0, 0])
      translate([0, 0, -cornerRadius])
      rotate([-angle * indexBottom, 0, 0])
      mirror([0, 1, 0])
      pillar(cp, w, pt);

      indexTop = (keys - keyOffset - 0.5 - centerOffset); 
      heightTop = cornerRadius * (1 - cos(angle * indexTop)) + postsHeight + 5 - pt;

      translate([0, flapOffset, -heightTop])
      rotate([angle * indexTop, 0, 0])
      translate([0, 0, -cornerRadius])
      rotate([-angle * indexTop, 0, 0])
      pillar(cp, w, pt);
   }
}

module key_cluster(printableOnly=false)
{
   pinky = 0;
   ring = 1;
   middle = 2;
   index = 3;
   thumb = 4;

   fingerLength = [ 45, 50, 55, 48, 35 ];
   fingerLenghtOffset = [ 0, 15, 21, 15, -25 ];
   baseRadius = 23;
   fingerOffsetFactor = 0.8;
   columnOffsetFactor = 0.3;

   fl = fingerLength;
   flo = fingerLenghtOffset;

   fingerRadius = [ for (i=[0:4]) baseRadius + fl[i] + flo[i] ];
   fr = fingerRadius;

   fingerHeight = [ for (i=[0:4]) fr[i] * fingerOffsetFactor ];
   fh = fingerHeight;

   columnOffset = [ for (i=[0:4]) fr[i] * columnOffsetFactor ];
   cho = columnOffset;

   columns    = [ pinky, pinky, ring, middle, index, index ];
   rows       = [ 4, 4, 5, 5, 4, 4 ];
   rowsOffset = [ 1, 1, 2.5, 2.5, 1, 1 ];

   translate([0, -20, baseRadius + 8])
   {
      for (i=[0:5])
      {
         translate([(i + 0.5) * (columnPitch + spacing), cho[columns[i]], fh[columns[i]]])
         {
            if (!printableOnly && !printView)
            {
               column(rows[i], fingerRadius[columns[i]], rowsOffset[i]);
            }
            postHeight =  baseRadius - (fr[columns[i]] - fh[columns[i]]);
            column_support(rows[i], fingerRadius[columns[i]], rowsOffset[i], postHeight);
            base(rows[i], fingerRadius[columns[i]], rowsOffset[i], postHeight);
         }
      }
   }
}

module thumb_cluster(printableOnly=false)
{
   thumbRadi = [ -60, -60 ];
   thumbKeys = [ 3, 2 ];
   thumbKeysOffsets = [ 2, 1 ];
   thumbHeights = [ 25, 20 ];
   xOffset = [ 0, 0 ];
   yOffset = [ 0, 0 ];

   for (i=[0:len(thumbRadi)-1])
   {
      translate([-i*columnPitch + xOffset[i], yOffset[i], thumbRadi[i] + 6.7 + thumbHeights[i]])
      {
         if (!printableOnly && !printView)
         {
            column(thumbKeys[i], thumbRadi[i], thumbKeysOffsets[i]);
         }
         column_support(thumbKeys[i], thumbRadi[i], thumbKeysOffsets[i], thumbHeights[i]);
         base(thumbKeys[i], thumbRadi[i], thumbKeysOffsets[i], thumbHeights[i]);
      }
   }
}




/////////////////////////////////////////////
/////////////     Keyboard     //////////////
/////////////////////////////////////////////

elbowAngle = 10;
thumbAngle = 70;
thubOffset = [105, -60, 0];

// Left hand
translate([-170, 0, 0])
rotate([0, 0, -elbowAngle])
{
key_cluster();
translate(thubOffset)
   rotate([0, 0, thumbAngle])
      thumb_cluster();
}

// Right hand
mirror([1, 0, 0])
translate([-170, 0, 0])
rotate([0, 0, -elbowAngle])
{
key_cluster();
translate(thubOffset)
   rotate([0, 0, thumbAngle])
      thumb_cluster();
}

// Column plates
*translate([2*(columnPitch + 1), -switchPitch*2, 0])
{
translate([-(columnPitch + 1), 0, 0])
   column_plate(5);
translate([-2*(columnPitch + 1), 0, 0])
   column_plate(4);
translate([-3*(columnPitch + 1), 0, 0])
   column_plate(3);
}

// Testing column
*translate([0, 0, 0])
{
   keys = 5;
   radius = 80;
   keyOffset = 0.5;
   postsHeight = 10;

   translate([0, 0, radius + 6 + postsHeight])
   {
   column(keys, radius, keyOffset);
   column_support(keys, radius, keyOffset, postsHeight);
   base(keys, radius, keyOffset, postsHeight);
   }
}

// TODO: Add microcontroller holder and port
// TODO: Add side covers
