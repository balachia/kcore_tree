# -*- coding: utf-8 -*-

"""Main module."""

import igraph
from collections import defaultdict, OrderedDict, namedtuple

# VERBOSITY
QUIET   = 0
INFO    = 1
DEBUG   = 2

# set up block 'class'
Block = namedtuple('Block', ['idx', 'parent', 'vertices', 'klevel', 'kconn'])

def kcore_tree(g, *args, **kwargs):
    """
    .. function:: kcore_tree(g, *args, **kwargs)

    Derives the k-core hierarchy tree for a given graph.

    :param igraph.Graph g: graph
    :return: (blocks, hierarchy) tuple
    """

    # preserve indices
    g1 = g.copy()
    for v in g1.vs:
        v['_index'] = v.index

    # build vertex sets
    components_dict = build_vertex_sets(g1, *args, **kwargs)

    # build blocks
    blocks = component_lists_to_blocks(components_dict, *args, **kwargs)

    # build hierarchy
    hierarchy = blocks_to_hierarchy(blocks, *args, **kwargs)

    return (blocks, hierarchy)

def build_vertex_sets(g, verbose=0, *args, **kwargs):
    """
    .. function:: build_vertex_sets(g)

    Builds an ordered dictionary mapping k-core levels to lists of connected vertex ids at that level.
    Graph vertices must have '_index' attribute.

    :param igraph.Graph g: graph
    :rtype: OrderedDict, keys=k, values=list of lists of vertex ids
    """
    coreness = g.coreness()
    components = OrderedDict()
    # components = dict()
    for k in sorted(set(coreness)):
        if verbose >= INFO:
            print('Finding k=%d' % k)
        vset = __filter_vertices(k, coreness)
        if k > 0:
            components[k] = induced_components(g, vset)
        else:
            components[k] = [vset]
    return components
        
def __filter_vertices(k, coreness, *args, **kwargs):
    """
    .. function filter_vertices(k, coreness)

    Filters coreness mapping for vertex ids in k-core >= k.

    :param k: minimum k-core
    :param list coreness: vertex -> k-core mapping
    :return: vertices in k-core
    """
    return list(filter(lambda i: coreness[i] >= k, range(len(coreness))))

def induced_components(g, vs, *args, **kwargs):
    """
    .. function:: induced_components(g, vs)

    Finds disjoint components formed by selected vertices.
    Graph vertices must have '_index' attribute.

    :param g: graph
    :param vs: vertex id list
    :return: list of components (vertex ids)
    """
    components = list()
    gs = g.induced_subgraph(vs)
    for component in gs.components(igraph.WEAK):
        component_vs = gs.induced_subgraph(component).vs
        components.append([v['_index'] for v in component_vs])
    return components

def component_lists_to_blocks(components_dict, *args, **kwargs):
    """
    .. function component_lists_to_blocks(components_dict)

    Converts components list to blocks.

    :param components_dict: OrderedDict (list) of lists of components
    """

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

            blk = Block(idx=index, parent=parent, vertices=vs, klevel=k, kconn=k)
            blocks.append(blk)
            index += 1
    
    return (blocks)

def blocks_to_hierarchy(blocks, *args, **kwargs):
    """
    .. function:: blocks_to_hierarchy(blocks)

    Builds hierarchy graph from block list.

    :param blocks: list of blocks
    :return: hierarchy tree
    :rtype: igraph.Graph
    """
    hier = igraph.Graph()
    idxs = [blk.index for blk in blocks]
    hier.add_vertices(idxs)

    for blk in blocks:
        if blk.parent is not None:
            hier.add_edge(blk.parent, blk.idx)

    return hier

