# -*- coding: utf-8 -*-

"""Main module."""

import igraph
from collections import defaultdict, OrderedDict, namedtuple

def kcore_tree(g, *args, **kwargs):
    # get coreness; make sorted set
    # for core in coreness set,
    #   get subgraph for relevant nodes
    #   get components from subgraph (components(igraph.WEAK))

    # preserve indices
    g1 = g.copy()
    for v in g1.vs:
        v['_index'] = v.index

    # build vertex sets
    components_dict = build_vertex_sets(g1)

    # build blocks
    blocks = component_lists_to_blocks(components_dict)

    # build hierarchy
    hierarchy = blocks_to_hierarchy(blocks)

    return (blocks, hierarchy)

def build_vertex_sets(g):
    coreness = g.coreness()
    components = OrderedDict()
    # components = dict()
    for k in sorted(coreness):
        vset = filter_vertices(k, coreness)
        components[k] = induced_components(g, vset)
    return components
        
def filter_vertices(k, coreness):
    return list(filter(lambda i: coreness[i] >= k, range(len(coreness))))

def induced_components(g, vs):
    components = list()
    gs = g.induced_subgraph(vs)
    for component in gs.components(igraph.WEAK):
        component_vs = gs.induced_subgraph(component).vs
        components.append([v['_index'] for v in component_vs])
    return components

def component_lists_to_blocks(components_dict, vs=None):
    # set up block 'class'
    Block = namedtuple('Block', ['index', 'parent', 'vs', 'k'])

    # track block index
    index = 0
    ancestries = defaultdict(list)
    blocks = list()
    for k, cs in components_dict.items():
        for vs in cs:
            # check for parent, and add current block to node ancestry list
            # should be impossible for a block to have multiple parents,
            #   i.e. all nodes in block should have same parent ancestor
            parent=None
            for v in vs:
                if parent is None and ancestries[v]:
                    parent = ancestries[v][-1]
                ancestries[v].append(index)

            blk = Block(index=index, parent=parent, vs=vs, k=k)
            blocks.append(blk)
            index += 1
    
    return (blocks)

def blocks_to_hierarchy(blocks):
    hier = igraph.Graph()
    idxs = [blk.index for blk in blocks]
    hier.add_vertices(idxs)

    for blk in blocks:
        if blk.parent is not None:
            hier.add_edge(blk.parent, blk.index)

    return hier

