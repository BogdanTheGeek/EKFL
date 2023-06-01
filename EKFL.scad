/*
 *  EKFL keyboard
 *  Copyright Bogdan Ionescu 2023
 *  LICENCE under GNU GPL v3
 */


showSwitches = true;
showKeys = true;
printView = false;

// spacing between columns (for split printing)
spacing = 0.1;

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


module mount(l, w, t, d)
{
   translate([-l/2, 0, 0])
   difference()
   {
      cube([l, w, t]);
      translate([l/2, w/2, -1])
         cylinder(d=d + 0.2, h=t+2, $fn=32);
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
                     import("DSA 1u LR.stl", convexity=3);
                     //import("XDA 1u LR.stl", convexity=3);
         }
   }

   // Mounting Flaps
   w = mountingFlapWidth;
   cornerRadius = sqrt((radius + pt)*(radius + pt) + (sp/2)*(sp/2)) * (radius < 0 ? -1 : 1);

   indexBottom = (-keyOffset - 0.5 - centerOffset); 
   rotate([angle * indexBottom, 0, 0])
   translate([0, 0, -cornerRadius])
   rotate([-angle * indexBottom, 0, 0])
   mirror([0, 1, 0])
   mount(cp, w, pt, mountingHoleDiameter);

   indexTop = (keys - keyOffset - 0.5 - centerOffset); 
   rotate([angle * indexTop, 0, 0])
   translate([0, 0, -cornerRadius])
   rotate([-angle * indexTop, 0, 0])
   mount(cp, w, pt, mountingHoleDiameter);


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

   if (posts)
   {
      for (i=[0:posts-1])
      {
         k = ((keys / 2) - keyOffset - 1) + i - (keys == 6 ? 1 : 0);
         l = radius * (1 - cos(angle * k)) + postsHeight - 3 - linkClearnace;

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

   cornerRadius = sqrt((radius + pt)*(radius + pt) + (sp/2)*(sp/2)) * (radius < 0 ? -1 : 1);

   indexBottom = (-keyOffset - 0.5 - centerOffset); 

   heightBottom = radius * (1 - cos(angle * indexBottom)) + postsHeight + 5 - pt;

   translate([0, -flapOffset, -heightBottom])
   rotate([angle * indexBottom, 0, 0])
   translate([0, 0, -cornerRadius])
   rotate([-angle * indexBottom, 0, 0])
   mirror([0, 1, 0])
   mount(cp, w, heightBottom, mountingHoleDiameter);

   indexTop = (keys - keyOffset - 0.5 - centerOffset); 

   heightTop = radius * (1 - cos(angle * indexTop)) + postsHeight + 5 - pt;

   translate([0, flapOffset, -heightTop])
   rotate([angle * indexTop, 0, 0])
   translate([0, 0, -cornerRadius])
   rotate([-angle * indexTop, 0, 0])
   mount(cp, w, heightTop, mountingHoleDiameter);
}

module base(keys, radius, keyOffset=2, postsHeight=0, top=true, bottom=true)
{
   ll = locatorLength;
   lw = locatorWidth;
   sp = switchPitch;
   cp = columnPitch;
   pt = plateThickness;

   angle = 2*atan(sp/2 / (radius + pt));

   centerOffset =  keys % 2 == 0 ? 0.5 : 0;

   // Mounting posts
   flapOffset = 1;
   w = mountingFlapWidth - flapOffset;
   depth = 10;

   k1 = keys - keyOffset - centerOffset - 1 + 0.5;
   a1 = angle * k1;
   h1 = radius * (1 - cos(a1)) + postsHeight + 7.5 - pt;

   k2 = keyOffset + centerOffset + 0.5;
   a2 = angle * k2;
   h2 = radius * (1 - cos(a2)) + postsHeight + 7.5 - pt;

   // Plate
   hull()
   {
      if (top)
      {
         rotate([a1, 0, 0])
            translate([0, 0, -radius-pt])
            rotate([-a1, 0, 0])
               translate([-cp/2, 1, -h1 - pt/2])
                  cube([cp, w, pt]);
      }
      if (bottom)
      {
         rotate([-a2, 0, 0])
            translate([0, 0, -radius-pt])
            rotate([180 + a2, 0, 0])
               translate([-cp/2, 1, h2 - pt/2])
                  cube([cp, w, pt]);
      }
   }
}


module key_cluster()
{
   pinky = 0;
   ring = 1;
   middle = 2;
   index = 3;
   thumb = 4;

   fingerLength = [ 45, 50, 55, 48, 35 ];
   fingerLenghtOffset = [ 0, 15, 21, 15, -25 ];
   baseRadius = 22;
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
            if (!printView)
            {
               column(rows[i], fingerRadius[columns[i]], rowsOffset[i]);
            }
            postHeight =  baseRadius - (fr[columns[i]] - fh[columns[i]]);
            column_support(rows[i], fingerRadius[columns[i]], rowsOffset[i], postHeight);
            //base(rows[i], fingerRadius[columns[i]], rowsOffset[i], postHeight);
         }
      }
   }
}

module thumb_cluster()
{
   thumbRadius = 80;
   thumbKeys = 3;
   thumbKeysOffset = 0;
   thumbHeight = 10;

   translate([0, 0, thumbRadius + 8 + thumbHeight])
   {
      if (!printView)
      {
         column(thumbKeys, thumbRadius, thumbKeysOffset);
      }
      column_support(thumbKeys, thumbRadius, thumbKeysOffset, thumbHeight);
      //base(thumbKeys, thumbRadius, thumbKeysOffset, thumbHeight);
   }

   translate([0, 0, thumbRadius + 8 + thumbHeight])
   {
      translate([columnPitch + spacing, 0, 0])
      {
         if (!printView)
         {
            column(thumbKeys, thumbRadius, thumbKeysOffset);
         }
         column_support(thumbKeys, thumbRadius, thumbKeysOffset, thumbHeight);
         //base(thumbKeys, thumbRadius, thumbKeysOffset, thumbHeight);
      }
   }
}




/////////////////////////////////////////////
/////////////     Keyboard     //////////////
/////////////////////////////////////////////

elbowAngle = 10;
thumbAngle = 70;
thubOffset = [125, -95, 0];

translate([-170, 0, 0])
rotate([0, 0, -elbowAngle])
{
key_cluster();
translate(thubOffset)
   rotate([0, 0, thumbAngle])
      thumb_cluster();
}
mirror([1, 0, 0])
translate([-170, 0, 0])
rotate([0, 0, -elbowAngle])
{
key_cluster();
translate(thubOffset)
   rotate([0, 0, thumbAngle])
      thumb_cluster();
}

translate([2*(columnPitch + spacing), -switchPitch*2, 0])
{
translate([-(columnPitch + spacing), 0, 0])
   column_plate(5);
translate([-2*(columnPitch + spacing), 0, 0])
   column_plate(4);
translate([-3*(columnPitch + spacing), 0, 0])
   column_plate(3);
}

// testing column
*translate([0, 0, 0])
{
   keys = 4;
   radius = 80;
   keyOffset = 0;
   postsHeight = 10;

   translate([0, 0, radius + 6 + postsHeight])
   {
   column(keys, radius, keyOffset);
   column_support(keys, radius, keyOffset, postsHeight);
   }
}

// TODO: fix bottom not quite flat
// TODO: fix convex support height
