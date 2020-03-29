thickness = 3;
slice_size = 20;
image_size = 17;
slice_radius = 1.0;
image_radius = 1.0;
slice_gap = 3.0;
tile_radius = 1.0;
tile_gap = 5.0;
lock_fudge = 0.01;

tile_size = slice_size * 2 * cos(30) + slice_gap*cos(30)*1.2 + tile_gap;
slice_offset = slice_gap * cos(30) + slice_size;

$tile();

$placed();
slice();
$for (k=[0:60:359]){
    rotate([0,0,k]){
        translate([0,-tile_size * cos(30) * 2,0]){
            placed();
        }
    }
}

module placed(){
    for(i=[0:60:359]){
        rotate([0,0,i]){
            for(j=[0:1:i/60]){
                translate([0, -slice_offset, thickness*j]){
                    %slice();
                }
            }
        }
    }
    tile();
}

module round_corners (radius){
    offset(r=-radius, $fn=20){
        offset(r=radius*2, $fn=20){
            offset(r=-radius, $fn=20){
                children();
            }
        }
    } 
}

module tile(){
    difference(){
    //linear_extrude(thickness){
        round_corners(tile_radius){
            difference(){
                circle(r=tile_size ,$fn=6);
                for(i=[0:60:359]){
                    rotate([0,0,i]){
                        intersection(){
                            translate([0, tile_size/2 * cos(30) + lock_fudge, 0]){
                                circle(r=tile_size/2,$fn=6);
                            }
                            translate([0, tile_size * cos(30) - tile_gap+ slice_gap/2, 0]){
                                square([tile_size/2,10]);
                            }
                        }
                    }
                }
            }
            for(i=[0:60:359]){
                rotate([0,0,i]){
                    translate([0,-tile_size*2*cos(30),0]){
                        scale([1,1,1]){
                            intersection(){
                                translate([0, tile_size/2 * cos(30) + lock_fudge, 0]){
                                    circle(r=tile_size/2,$fn=6);
                                }
                                translate([0, tile_size * cos(30) - tile_gap+ slice_gap/2, 0]){
                                    square([tile_size/2,10]);
                                }
                            }
                        }
                    }
                }
            }
        }
    //}
    for(i=[0:60:359]){
        rotate([0,0,i + 30]){
            translate([-slice_offset,0,thickness]){
                //linear_extrude(thickness){
                    image_shape();
                //}
            }
        }
    }
    }
}

module slice(){
    rotate([0,0,90]){
        $translate([0,0,2*thickness]){
            //linear_extrude(thickness){
                offset(r=slice_radius, $fn=20){
                    offset(r=-slice_radius, $fn=20){
                        circle(r=slice_size,$fn=3);
                    }
                }
            //}
        }
        $translate([0,0,3*thickness]){
            //linear_extrude(thickness){
                image_shape();
            //}
        }
        translate([0,0,thickness]){
            //linear_extrude(thickness){
                difference(){
                    offset(r=slice_radius, $fn=20){
                        offset(r=-slice_radius, $fn=20){
                            circle(r=slice_size,$fn=3);
                        }
                    }
                    image_shape();
                }
            //}
        }
    }
}

module image_shape(){
    offset(r=image_radius, $fn=20){
        offset(r=-image_radius, $fn=20){
            circle(r=image_size,$fn=3);
        }
    }
}
    