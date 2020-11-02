from leuvenmapmatching.matcher.distance import DistanceMatcher
from leuvenmapmatching.map.inmem import InMemMap
from leuvenmapmatching import visualization as mmviz
from leuvenmapmatching.util.gpx import gpx_to_path
from pathlib import Path
import requests
import osmread
import osmnx as ox

def example1():
    map_con = InMemMap("mymap", graph={
        "A": ((1, 1), ["B", "C", "X"]),
        "B": ((1, 3), ["A", "C", "D", "K"]),
        "C": ((2, 2), ["A", "B", "D", "E", "X", "Y"]),
        "D": ((2, 4), ["B", "C", "F", "E", "K", "L"]),
        "E": ((3, 3), ["C", "D", "F", "Y"]),
        "F": ((3, 5), ["D", "E", "L"]),
        "X": ((2, 0), ["A", "C", "Y"]),
        "Y": ((3, 1), ["X", "C", "E"]),
        "K": ((1, 5), ["B", "D", "L"]),
        "L": ((2, 6), ["K", "D", "F"])
    }, use_latlon=False)

    path = [(0.8, 0.7), (0.9, 0.7), (1.1, 1.0), (1.2, 1.5), (1.2, 1.6), (1.1, 2.0),
            (1.1, 2.3), (1.3, 2.9), (1.2, 3.1), (1.5, 3.2), (1.8, 3.5), (2.0, 3.7),
            (2.3, 3.5), (2.4, 3.2), (2.6, 3.1), (2.9, 3.1), (3.0, 3.2),
            (3.1, 3.8), (3.0, 4.0), (3.1, 4.3), (3.1, 4.6), (3.0, 4.9)]

    matcher = DistanceMatcher(map_con, max_dist=2, obs_noise=1, min_prob_norm=0.5)
    states, _ = matcher.match(path)
    nodes = matcher.path_pred_onlynodes

    print("States\n------")
    print(states)
    print("Nodes\n------")
    print(nodes)
    print("")
    matcher.print_lattice_stats()

def example2():
    path = [(1, 0), (7.5, 0.65), (10.1, 1.9)]
    mapdb = InMemMap("mymap", graph={
        "A": ((1, 0.00), ["B"]),
        "B": ((3, 0.00), ["A", "C"]),
        "C": ((4, 0.70), ["B", "D"]),
        "D": ((5, 1.00), ["C", "E"]),
        "E": ((6, 1.00), ["D", "F"]),
        "F": ((7, 0.70), ["E", "G"]),
        "G": ((8, 0.00), ["F", "H"]),
        "H": ((10, 0.0), ["G", "I"]),
        "I": ((10, 2.0), ["H"])
    }, use_latlon=False)
    matcher = DistanceMatcher(mapdb, max_dist_init=0.2, obs_noise=1, obs_noise_ne=10,
                            non_emitting_states=True, only_edges=True)
    states, _ = matcher.match(path)
    nodes = matcher.path_pred_onlynodes

    print("States\n------")
    print(states)
    print("Nodes\n------")
    print(nodes)
    print("")
    matcher.print_lattice_stats()

    mmviz.plot_map(mapdb, matcher=matcher,
                show_labels=True, show_matching=True,
                filename="output.png")


def download_map() -> None:
    xml_file = Path("./tests")/"osm.xml"
    url = 'http://overpass-api.de/api/map?bbox=4.694933,50.870047,4.709256000000001,50.879628'
    r = requests.get(url, stream=True)
    with xml_file.open("wb") as ofile:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                print('.', end='')
                ofile.write(chunk)

    return

def create_map_osmread() -> None:
    xml_file = Path("./tests")/"osm.xml"
    map_con = InMemMap("myosm", use_latlon=True, use_rtree=True, index_edges=True)
    for entity in osmread.parse_file(str(xml_file)):
        if isinstance(entity, osmread.Way) and 'highway' in entity.tags:
            for node_a, node_b in zip(entity.nodes, entity.nodes[1:]):
                map_con.add_edge(node_a, node_b)
                # Some roads are one-way. We'll add both directions.
                map_con.add_edge(node_b, node_a)
        if isinstance(entity, osmread.Node):
            map_con.add_node(entity.id, (entity.lat, entity.lon))
    map_con.purge()


def map_matching_osm():
    track = gpx_to_path("mytrack.gpx")
    matcher = DistanceMatcher(map_con,
                            max_dist=100, max_dist_init=25,  # meter
                            min_prob_norm=0.001,
                            non_emitting_length_factor=0.75,
                            obs_noise=50, obs_noise_ne=75,  # meter
                            dist_noise=50,  # meter
                            non_emitting_states=True)
    states, lastidx = matcher.match(track)
    return


def use_osmnx() -> None:
    graph = ox.graph_from_place('Leuven, Belgium', network_type='drive')
    graph_proj = ox.project_graph(graph)

    # Create GeoDataFrames
    # Approach 1
    nodes_proj, edges_proj = ox.graph_to_gdfs(graph_proj, nodes=True, edges=True)
    for nid, row in nodes_proj[['x', 'y']].iterrows():
        map_con.add_node(nid, (row['x'], row['y']))
    for nid, row in edges_proj[['u', 'v']].iterrows():
        map_con.add_edge(row['u'], row['v'])

    # Approach 2
    nodes, edges = ox.graph_to_gdfs(graph_proj, nodes=True, edges=True)

    nodes_proj = nodes.to_crs("EPSG:3395")
    edges_proj = edges.to_crs("EPSG:3395")

    for nid, row in nodes_proj.iterrows():
        map_con.add_node(nid, (row['lat'], row['lon']))

    # adding edges using networkx graph
    for nid1, nid2, _ in graph.edges:
        map_con.add_edge(nid1, nid2)




if __name__ == "__main__":
    # example1()
    # example2()
    
    # download_map()
    # create_map_osmread()
    map_matching_osm()