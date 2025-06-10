import networkx as nx
import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive
import matplotlib.pyplot as plt

def draw_family_tree(family_data, output_file="family_tree.png"):
    print(family_data)
    tree = {}
    root = None
    spouses = []
    anchors = []
    edge_styles = []
    labels = {}

    # Helper to parse the value string
    def parse_relation_info(value):
        parts = value.split(":")
        relation = parts[0] if len(parts) > 0 else None
        certainty = parts[1] if len(parts) > 1 else None
        dates = parts[2] if len(parts) > 2 else None
        city = parts[3] if len(parts) > 3 else None
        return relation, certainty, dates, city

    pos = {}
    x_counter = [0]

    def assign_pos(node, depth):
        children = tree.get(node, [])
        if not children:
            x = x_counter[0]
            pos[node] = (x, -depth)
            x_counter[0] += 1
            return x
        else:
            child_xs = [assign_pos(child, depth + 1) for child, *_ in children]
            mid_x = (child_xs[0] + child_xs[-1]) / 2
            pos[node] = (mid_x, -depth)
            return mid_x

    # First pass: parse the family structure
    for person, value in family_data.items():
        rel, cert, dates, city = parse_relation_info(value)

        # Label for each person node
        label = f"{person}"
        if dates:
            label += f"\n{dates}"
        if city:
            label += f"\n{city}"
        labels[person] = label

        if rel == "root":
            root = person
        elif rel.endswith("_child"):
            parent = rel.replace("_child", "")
            tree.setdefault(parent, []).append((person, cert))
        elif rel.endswith("_Spouse"):
            spouse_of = rel.replace("_Spouse", "")
            spouses.append((person, spouse_of, cert))
        elif rel.endswith("_anchor"):
            anchors.append((person, rel.replace("_anchor", ""), cert))

    if root:
        assign_pos(root, 0)

    G = nx.DiGraph()
    for person in family_data:
        G.add_node(person)

    # Add child edges with style
    for parent, children in tree.items():
        for child, certainty in children:
            if certainty == "Confirmed":
                G.add_edge(parent, child, style="solid")
            elif certainty == "Probable":
                G.add_edge(parent, child, style="dotted")
            for s1, s2, s_cert in spouses:
                if s2 == parent:
                    if certainty == "Confirmed":
                        G.add_edge(s1, child, style="solid")
                    elif certainty == "Probable":
                        G.add_edge(s1, child, style="dotted")
                elif s1 == parent:
                    if certainty == "Confirmed":
                        G.add_edge(s2, child, style="solid")
                    elif certainty == "Probable":
                        G.add_edge(s2, child, style="dotted")

    # Add spouse edges with style
    for s1, s2, certainty in spouses:
        if certainty == "Confirmed":
            G.add_edge(s1, s2, style="solid")
            G.add_edge(s2, s1, style="solid")
        elif certainty == "Probable":
            G.add_edge(s1, s2, style="dotted")
            G.add_edge(s2, s1, style="dotted")

    # Add anchors
    for anchor, base, certainty in anchors:
        if base in pos:
            G.add_node(anchor)
            if certainty == "Confirmed":
                G.add_edge(base, anchor, style="solid")
            elif certainty == "Probable":
                G.add_edge(base, anchor, style="dotted")

    # Position spouses
    for s1, s2, _ in spouses:
        if s2 in pos:
            x, y = pos[s2]
            pos[s1] = (x - 1, y)
        elif s1 in pos:
            x, y = pos[s1]
            pos[s2] = (x + 1, y)
        else:
            pos[s1] = (x_counter[0], 0)
            x_counter[0] += 1

    # Position anchors
    for anchor, base, _ in anchors:
        if base in pos:
            x, y = pos[base]
            pos[anchor] = (x + 0.5, y - 0.3)
        else:
            pos[anchor] = (x_counter[0], 0)
            x_counter[0] += 1

    # Ensure all nodes have positions
    for node in G.nodes:
        if node not in pos:
            pos[node] = (x_counter[0], 0)
            x_counter[0] += 1

    # Drawing
    plt.figure(figsize=(12, 7))
    solid_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("style") == "solid"]
    dotted_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("style") == "dotted"]

    nx.draw_networkx_nodes(
        G,
        pos,
        node_shape='s',
        node_color="lightblue",
        node_size=5500,
        edgecolors="black"
    )
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_weight="bold")
    nx.draw_networkx_edges(G, pos, edgelist=solid_edges, arrows=False, style="solid", width=2)
    nx.draw_networkx_edges(G, pos, edgelist=dotted_edges, arrows=False, style="dotted", width=2)

    plt.title("Family Tree", fontsize=16)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()

family_data = {
    "Sofia Verdi": "Giovanni Rossi_anchor:Probable:990:Milan",
    "Giovanni Rossi": "root:Confirmed:950, 980:Milan",
    "Maria Rossi": "Giovanni Rossi_child:Confirmed:970, 1000:Milan",
    "Pietro Bianchi": "Maria Rossi_Spouse:Confirmed:965, 995:Milan",
    "Anna Bianchi": "Maria Rossi_child:Confirmed:995:Milan",
    "Luca Rossi": "Giovanni Rossi_child:Probable:975:Milan"
}



draw_family_tree(family_data, output_file="tree_with_certainty.png")
