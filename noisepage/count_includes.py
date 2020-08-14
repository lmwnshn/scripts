'''
Build the header-include graph of a C++ project.
Useful for trying to figure out where compile time is going.

Typical use:
  python3 count_includes.py | sort -t, -n -k4
'''

import os
import networkx as nx


BASE_DIR = r'/home/cmudb/CLionProjects/terrier/'
SRC_INC_DIR = os.path.join(BASE_DIR, 'src/include/')
THIRD_PARTY_DIR = os.path.join(BASE_DIR, 'third_party/')


def add_neighbors(G, rel_file, f):
    with open(f) as current_file:
        for line in current_file:
            if line.startswith('#include ') and line.endswith('"\n'):
                include_name = line[line.index('"') + 1:-2]
                # We messed up some of the includes.
                if include_name.startswith('expression/'):
                    include_name = 'parser/' + include_name
                G.add_edge(rel_file, include_name)


def main():
    G = nx.DiGraph()
    for root, dirs, files in os.walk(SRC_INC_DIR):
        for f in files:
            if f.endswith('.h'):  # or f.endswith('.cpp'):
                rel_dir = os.path.relpath(root, SRC_INC_DIR)
                rel_file = os.path.join(rel_dir, f)
                abs_file = os.path.join(root, f)
                G.add_node(rel_file)
                add_neighbors(G, rel_file, abs_file)

    ancestors = {n: len(nx.ancestors(G, n)) for n in G.nodes()}

    print('header,num_includes,filesize,product')
    for (header, num_includes) in sorted(ancestors.items()):
        try:
            filesize = os.path.getsize(os.path.join(SRC_INC_DIR, header))
        except FileNotFoundError:
            filesize = os.path.getsize(os.path.join(THIRD_PARTY_DIR, header))
        product = filesize * num_includes
        print("{},{},{},{}".format(header, num_includes, filesize, product))


if __name__ == '__main__':
    main()


'''
Plotting support.
In practice, you have too many nodes to see anything useful.

import matplotlib.pyplot as plt
ancestor_threshold = 250
labels = {n: n for n in G.nodes() if ancestors[n] >= ancestor_threshold}
pos = nx.kamada_kawai_layout(G, scale=2)

plt.figure(1, figsize=(30, 30))
nx.draw_networkx_nodes(G, pos=pos, node_size=[ancestors[n] for n in G.nodes()])
nx.draw_networkx_edges(G, pos=pos)
nx.draw_networkx_labels(G, pos=pos, labels=labels)

plt.draw()
plt.show()
'''
