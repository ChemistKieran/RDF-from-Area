from matplotlib import pyplot
import concurrent.futures
from shapely.geometry import Point
from shapely.geometry import box
from shapely.ops import cascaded_union
from descartes import PolygonPatch
from figures import SIZE, BLUE, GRAY, RED, set_limits
import json
import numpy as np
from timeit import default_timer as timer

def rdf(i):
    global bounding_box
    global bin_width
    global bins
    global no_bins
    previous_outer_intersection = Point(0,0).buffer(0)
    for j in range(no_bins):
        outer_rad_intersection = (Point(i[0], i[1]).buffer(j*bin_width).intersection(bounding_box))
        bin_shape = outer_rad_intersection.difference(previous_outer_intersection)
        previous_outer_intersection = outer_rad_intersection
        bin_intersection = (particle_map.intersection(bin_shape))
        bins[j-1][0] += bin_intersection.area
        bins[j-1][1] += bin_shape.area
    return bins

fig = pyplot.figure(1, dpi=90)
#import json file
filename = "list1converted.json"
with open(filename) as json_file:
    data = json.load(json_file)
#convert to numpy array
data = np.array(data)

#convert np array to shapely shapes and join into one shape
shapely_shapes = []
for i in data:
    shapely_shapes.append(Point(i[0], i[1]).buffer(i[2]))
particle_map = cascaded_union(shapely_shapes)

#setup bounding_box
box_xmin = 1000
box_xmax = 2000
box_ymin = 1000
box_ymax = 2500
bounding_box = box(box_xmin,box_ymin,box_xmax,box_ymax)

#setup bins
rdf_max = (box_xmax + box_ymax) /4
no_bins = 20
bin_width = rdf_max/no_bins
bins = np.zeros((no_bins, 2))

'''testing
test_bin = 30
outer_rad = Point(data[1][0], data[1][1]).buffer(test_bin*bin_width)
inner_rad = Point(data[1][0], data[1][1]).buffer((test_bin-1)*bin_width)
outer_pmap_intersect = (particle_map.intersection(outer_rad)).intersection(bounding_box)
inner_pmap_intersect = (particle_map.intersection(inner_rad)).intersection(bounding_box)
#bins[10][1] += outer_pmap_intersect.area - inner_pmap_intersect.area
print("diff is", outer_pmap_intersect.area - inner_pmap_intersect.area)
temp_ints_map = outer_pmap_intersect.difference(inner_pmap_intersect)
'''

#set up multiprocessing to use rdf on each particle
print("please wait ...")
start = timer()
with concurrent.futures.ProcessPoolExecutor() as executor:
    binsin = executor.map(rdf, data)

#sum together all rdf values and normalisations for all particles
bins = np.sum(np.array(list(binsin)),axis=0)
#apply normalisations
normalised_bins = bins[:,0]/(bins[:,1])

end = timer()
print(end - start)
#plot setup
ax = fig.add_subplot(121)
ax2 = fig.add_subplot(122)

draw_particle_map = PolygonPatch(particle_map, fc=GRAY, ec=GRAY, alpha=0.2, zorder=1)
ax2.add_patch(draw_particle_map)
draw_bounding_box = PolygonPatch(bounding_box, fc=BLUE, ec=GRAY, alpha=0.2, zorder=1)
ax2.add_patch(draw_bounding_box)
ax2.autoscale_view()


x_axis = np.linspace(0.0, rdf_max, no_bins)
print(x_axis)
ax.plot(x_axis, normalised_bins)


pyplot.show()
