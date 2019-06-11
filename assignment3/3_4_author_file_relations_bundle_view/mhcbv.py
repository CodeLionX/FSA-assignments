#!/usr/bin/env python3

import sys
import math

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.path as mpath
from matplotlib import cm


class Node:
    def __init__(self, name, parent, weight = 0.0, color = 0.0):
        # topology
        self.name = name
        self.parent = parent
        self.children = []
        self.relations = []
        # data
        self.weight = 0.0
        self.color = color
        # layout
        self.center = ( 0.0, 0.0 )
        self.angle_range = ( 0.0, 2 * math.pi )
        self.radius_range = ( 0.0, 1.0 )
        self.control_point_radius = 0.0
        
        self.updateWeight(weight)
    
    def root(self):
        if self.parent is not None:
            return self.parent.root()
        
        return self
    
    def updateWeight(self, weight):
        if self.parent:
            self.parent.updateWeight(weight)
        self.weight += weight
    
    def insert(self, path, weight, color):
        if len(path) == 0:
            return
        
        child = next((node for node in self.children if node.name == path[0]), None)
        
        if len(path) == 1:
            if child is not None:
                print("Warning: child %s already added" % (path[0]))
            else:
                child = Node(path[0], self, weight, color)
                self.children.append(child)
            return child
        else:
            if child is None:
                child = Node(path[0], self)
                self.children.append(child)
            
            return child.insert(path[1:], weight, color)
    
    def find(self, path):
        if len(path) == 0:
            return self
        
        child = next((node for node in self.children if node.name == path[0]), None)
        
        if child is not None:
            return child.find(path[1:])
        else:
            return None
    
    def set_center(self, x, y):
        self.center = ( x, y )
        for child in self.children:
            child.set_center(x, y)
    
    def set_angle_range(self, start, end):
        self.angle_range = ( start, end )
        length = end - start
        child_start = start
        for child in self.children:
            child_end = child_start + length * child.weight / self.weight
            child.set_angle_range(child_start, child_end)
            child_start = child_end
    
    def set_radius_range(self, start, width, control_start = 0.0):
        self.radius_range = (start - width, start)
        self.control_point_radius = control_start
        for child in self.children:
            child.set_radius_range(start - width, width, control_start + width)
    
    def anchor(self):
        return (
            self.center[0] + math.cos((self.angle_range[0] + self.angle_range[1]) / 2.0) * self.radius_range[0],
            self.center[1] + math.sin((self.angle_range[0] + self.angle_range[1]) / 2.0) * self.radius_range[0]
        )
    
    def control_point(self):
        return (
            self.center[0] + math.cos((self.angle_range[0] + self.angle_range[1]) / 2.0) * self.control_point_radius,
            self.center[1] + math.sin((self.angle_range[0] + self.angle_range[1]) / 2.0) * self.control_point_radius
        )
    
    def path(self):
        if self.parent is not None:
            return self.parent.path() + [ self ]
        
        return [ self ]
    
    def depth(self):
        return len(self.path())
    
    def path_to(self, other):
        path1 = self.path()
        path2 = other.path()
        
        last_removed = None
        while len(path1) > 0 and len(path2) > 0 and path1[0] == path2[0]:
            last_removed = path1[0]
            path1 = path1[1:]
            path2 = path2[1:]
        
        if last_removed:
            return path1[::-1] + [ last_removed ] + path2
        return path1[::-1] + path2
    
    def is_leaf(self):
        return len(self.children) == 0
    
    def render(self, parent_patches, parent_colors, leaf_patches, leaf_colors):
        if self.is_leaf():
            leaf_patches.append(
                matplotlib.patches.Wedge(self.center, # center
                    self.radius_range[1], # radius
                    self.angle_range[0] * 180 / math.pi, # start angle
                    self.angle_range[1] * 180 / math.pi, # end angle
                    width=self.radius_range[1] - self.radius_range[0] # width from outer side
                )
            )
            leaf_colors.append(self.color)
        else:
            parent_patches.append(
                matplotlib.patches.Wedge(self.center, # center
                    self.radius_range[1], # radius
                    self.angle_range[0] * 180 / math.pi, # start angle
                    self.angle_range[1] * 180 / math.pi, # end angle
                    width=self.radius_range[1] - self.radius_range[0] # width from outer side
                )
            )
            parent_colors.append(self.depth())
        
        for child in self.children:
            child.render(parent_patches, parent_colors, leaf_patches, leaf_colors)
    
    def render_relations(self, patches, colors):
        for target in self.relations:
            source_to_target_path = source.path_to(target)
            target_to_source_path = source_to_target_path[::-1]
            patches.append(
                matplotlib.patches.PathPatch(
                    mpath.Path(
                        [ source.anchor() ] +
                        [ node.control_point() for node in source_to_target_path ] +
                        [ target.anchor() ] +
                        [ node.control_point() for node in target_to_source_path ] +
                        [ source.anchor() ],
                        [ mpath.Path.MOVETO ] + 
                        [ mpath.Path.LINETO for node in source_to_target_path ] +
                        [ mpath.Path.LINETO ] +
                        [ mpath.Path.LINETO for node in target_to_source_path ] +
                        [ mpath.Path.CLOSEPOLY ]
                    )
                )
            )
            colors.append(self.color)

#
# Parse data
#

data = {}
nodes = {}
max_depth = 0

for line in sys.stdin:
    line = line.strip()
    
    if len(line) == 0:
        continue
    
    type, hierarchy_name, count = line.split(";")
    
    if type == "hierarchy":
        count = int(count)
        data[hierarchy_name] = Node(hierarchy_name, None)
        while count > 0:
            line = sys.stdin.readline().strip()
            type1, type2, identifier, weight, color, *other = line.split(";") # ignore type2 for now
            
            if type1 != "node":
                print("Expected type 'node', got %s" % (type1))
                sys.exit(1)

            weight = int(weight)
            path = identifier.split("/")
            max_depth = max(max_depth, len(path))
            nodes[identifier] = data[hierarchy_name].insert(path, weight, color)
            count -= 1
    
    elif type == "edges":
        count = int(count)
        while count > 0:
            line = sys.stdin.readline().strip()
            type1, type2, source, target, *other = line.split(";") # ignore type2 for now
            
            if type1 != "edge":
                print("Expected type 'edge', got %s" % (type1))
                sys.exit(1)
            
            nodes[source].relations.append(nodes[target])
            count -= 1
    
    else:
        print("Unsupported type %s" % (type))
        sys.exit(1)

#
# Compute Hierarchical Nesting
#

num_hierarchies = len(data)

radius_of_rings = 1.15
ring_radius = 1.0

for i, hierarchy in enumerate(data.items()):
    radius = radius_of_rings * (num_hierarchies - 1)
    center_angle = i * 2 * math.pi / num_hierarchies
    opening_angle = center_angle - math.pi
    opening_angle_opening = math.pi / 8.0
    
    root = hierarchy[1]
    
    # Layouting
    root.set_center(math.cos(center_angle) * radius, math.sin(center_angle) * radius)
    root.set_angle_range(opening_angle + opening_angle_opening, opening_angle + 2 * math.pi - opening_angle_opening)
    root.set_radius_range(ring_radius, ring_radius / (2.0 * (max_depth+1.0)), 0.0)

#
# Rendering
#

fig, ax = plt.subplots()

# Render nodes

parent_patches = []
parent_colors = []
leaf_patches = []
leaf_colors = []
for i, hierarchy in enumerate(data.items()):
    root = hierarchy[1]
    
    root.render(parent_patches, parent_colors, leaf_patches, leaf_colors)

norm = cm.colors.Normalize(vmax=max(parent_colors)+1, vmin=-1) # don't use plain black and white
parent_collection = matplotlib.collections.PatchCollection(parent_patches, alpha = 1.0, cmap=matplotlib.cm.gray, norm=norm)
parent_collection.set_array(np.array(parent_colors, dtype=float))
ax.add_collection(parent_collection)

leaf_collection = matplotlib.collections.PatchCollection(leaf_patches, alpha = 1.0, cmap=matplotlib.cm.OrRd)
leaf_collection.set_array(np.array(leaf_colors, dtype=float))
ax.add_collection(leaf_collection)

# Render edges

patches = []
colors = []
for node in nodes:
    source = nodes[node]
    
    source.render_relations(patches, colors)

# Create PDF

collection = matplotlib.collections.PatchCollection(patches, cmap=matplotlib.cm.jet, edgecolor='black', alpha=0.3,
                    linewidth=0.01)
collection.set_array(np.array(colors, dtype=float))
ax.add_collection(collection)

drawing_size = radius_of_rings if num_hierarchies == 1 else 2 * radius_of_rings + 2 * ring_radius
ax.set_xlim(-drawing_size/2, drawing_size/2)
ax.set_ylim(-drawing_size/2, drawing_size/2)

fig.set_size_inches(6 * num_hierarchies, 6 * num_hierarchies)
fig.tight_layout()

plt.axis('off')
plt.savefig(sys.stdout.buffer, format="pdf")
